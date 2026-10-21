import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.catalogo.fechas import ensure_utc
from salesia.modules.catalogo.application.catalogo.unidades import validate_unit_fraction
from salesia.modules.catalogo.infrastructure_models import (
    CouponModel,
    PriceListItemModel,
    PriceListModel,
    ProductProfileModel,
    ProductVariantModel,
    ProductVolumeTierModel,
    PromotionModel,
)
from salesia.modules.clientes.infrastructure.models import CustomerProfileModel
from salesia.modules.organizacion.application.politicas import effective_policy
from salesia.shared.infrastructure.errors import DomainForbiddenException, DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def resolve_product_price(
    db: Session,
    company_id: UUID,
    product_id: UUID,
    quantity: Decimal,
    customer_id: Optional[UUID] = None,
    variant_id: Optional[UUID] = None,
    coupon_code: Optional[str] = None,
    effective_time: Optional[datetime] = None,
) -> dict:
    if effective_time is None:
        effective_time = datetime.now(timezone.utc)
    else:
        effective_time = ensure_utc(effective_time)

    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()
    if not product:
        other = db.scalar(select(ProductModel.id).where(ProductModel.id == product_id))
        if other:
            raise DomainForbiddenException("El producto pertenece a otra empresa.")
        raise DomainNotFoundException("Producto no encontrado.")

    profile = db.execute(
        select(ProductProfileModel).where(
            ProductProfileModel.company_id == company_id, ProductProfileModel.product_id == product_id
        )
    ).scalar_one_or_none()

    validate_unit_fraction(db, company_id, product.unit_of_measure, quantity)

    base_unit_price = product.unit_price
    variant_info = None
    if variant_id:
        variant = db.execute(
            select(ProductVariantModel).where(
                ProductVariantModel.company_id == company_id,
                ProductVariantModel.product_id == product_id,
                ProductVariantModel.id == variant_id,
                ProductVariantModel.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if not variant:
            raise DomainNotFoundException("Variante no encontrada para el producto especificado.")
        if variant.operational_product_id:
            result = resolve_product_price(db, company_id, variant.operational_product_id, quantity, customer_id, coupon_code=coupon_code, effective_time=effective_time)
            result["variant"] = {"variant_id": str(variant.id), "parent_product_id": str(product_id), "sku": variant.sku, "price_delta": str(variant.price_delta)}
            return result
        base_unit_price = base_unit_price + variant.price_delta
        variant_info = {"variant_id": str(variant.id), "sku": variant.sku, "price_delta": str(variant.price_delta)}

    rules_applied = []
    current_unit_price = base_unit_price

    assigned_price_list_id = None
    cust_profile = None
    if customer_id:
        cust_profile = db.execute(
            select(CustomerProfileModel).where(
                CustomerProfileModel.company_id == company_id, CustomerProfileModel.customer_id == customer_id
            )
        ).scalar_one_or_none()
        if cust_profile and cust_profile.price_list_id:
            try:
                assigned_price_list_id = UUID(cust_profile.price_list_id)
            except ValueError:
                pass

    price_lists_all = (
        db.execute(
            select(PriceListModel)
            .where(PriceListModel.company_id == company_id, PriceListModel.is_active.is_(True))
            .order_by(PriceListModel.priority.desc())
        )
        .scalars()
        .all()
    )

    candidate_lists = []
    for pl in price_lists_all:
        pl_start = ensure_utc(pl.valid_from)
        pl_end = ensure_utc(pl.valid_to)
        if (pl_start is None or pl_start <= effective_time) and (pl_end is None or pl_end >= effective_time):
            if assigned_price_list_id:
                if pl.id == assigned_price_list_id:
                    candidate_lists.append(pl)
                    break
            elif pl.target_type == "all" or (pl.target_type == "customer" and pl.target_id == str(customer_id)):
                candidate_lists.append(pl)
            elif pl.target_type == "tag" and cust_profile and pl.target_id in json.loads(cust_profile.tags_json or "[]"):
                candidate_lists.append(pl)

    applied_pl_item = None
    for pl in candidate_lists:
        item_query = select(PriceListItemModel).where(
            PriceListItemModel.company_id == company_id,
            PriceListItemModel.price_list_id == pl.id,
            PriceListItemModel.product_id == product_id,
        )
        if variant_id:
            item_query = item_query.where(or_(PriceListItemModel.variant_id == variant_id, PriceListItemModel.variant_id.is_(None))).order_by(PriceListItemModel.variant_id.is_(None))
        else:
            item_query = item_query.where(PriceListItemModel.variant_id.is_(None))
        pl_item = db.scalars(item_query.limit(1)).first()
        if pl_item:
            applied_pl_item = (pl, pl_item)
            break

    if applied_pl_item:
        pl, pl_item = applied_pl_item
        if pl_item.fixed_price is not None:
            current_unit_price = pl_item.fixed_price
            rules_applied.append(
                {
                    "rule_type": "PRICE_LIST",
                    "name": pl.name,
                    "code": pl.code,
                    "priority": pl.priority,
                    "fixed_price": str(pl_item.fixed_price),
                }
            )
        elif pl_item.discount_percentage is not None and pl_item.discount_percentage > 0:
            disc = (current_unit_price * pl_item.discount_percentage).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_EVEN
            )
            current_unit_price = current_unit_price - disc
            rules_applied.append(
                {
                    "rule_type": "PRICE_LIST",
                    "name": pl.name,
                    "code": pl.code,
                    "priority": pl.priority,
                    "discount_percentage": str(pl_item.discount_percentage * Decimal("100")),
                    "discount_amount": str(disc),
                }
            )

    volume_tier = (
        db.execute(
            select(ProductVolumeTierModel)
            .where(
                ProductVolumeTierModel.company_id == company_id,
                ProductVolumeTierModel.product_id == product_id,
                ProductVolumeTierModel.min_quantity <= quantity,
            )
            .order_by(ProductVolumeTierModel.min_quantity.desc())
        )
        .scalars()
        .first()
    )

    has_any_volume_tiers = db.scalar(
        select(func.count(ProductVolumeTierModel.id)).where(
            ProductVolumeTierModel.company_id == company_id, ProductVolumeTierModel.product_id == product_id
        )
    )

    if volume_tier:
        if volume_tier.unit_price is not None:
            current_unit_price = volume_tier.unit_price
            rules_applied.append(
                {
                    "rule_type": "VOLUME_TIER",
                    "min_quantity": str(volume_tier.min_quantity),
                    "tier_unit_price": str(volume_tier.unit_price),
                }
            )
        elif volume_tier.discount_percentage is not None and volume_tier.discount_percentage > 0:
            disc = (current_unit_price * volume_tier.discount_percentage).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_EVEN
            )
            current_unit_price = current_unit_price - disc
            rules_applied.append(
                {
                    "rule_type": "VOLUME_TIER",
                    "min_quantity": str(volume_tier.min_quantity),
                    "discount_percentage": str(volume_tier.discount_percentage * Decimal("100")),
                    "discount_amount": str(disc),
                }
            )
    elif not has_any_volume_tiers:
        policy = effective_policy(db, company_id, "pricing_policy")
        eligible = [tier for tier in policy.get("volume_tiers", []) if Decimal(str(tier["min_quantity"])) <= quantity]
        if policy.get("default_volume_discounts_enabled", True) and eligible:
            tier = max(eligible, key=lambda item: Decimal(str(item["min_quantity"])))
            percentage = Decimal(str(tier["discount_percentage"]))
            disc = (current_unit_price * percentage).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
            current_unit_price -= disc
            rules_applied.append({"rule_type": "VOLUME_TIER_DEFAULT", "min_quantity": str(tier["min_quantity"]), "discount_percentage": str(percentage * 100), "discount_amount": str(disc)})

    promotions_all = (
        db.execute(
            select(PromotionModel)
            .where(
                PromotionModel.company_id == company_id,
                PromotionModel.is_active.is_(True),
                PromotionModel.current_uses < PromotionModel.max_quota,
                PromotionModel.min_quantity <= quantity,
                or_(PromotionModel.product_id.is_(None), PromotionModel.product_id == product_id),
            )
            .order_by(PromotionModel.priority.desc())
        )
        .scalars()
        .all()
    )

    promotions = []
    for promo in promotions_all:
        p_start = ensure_utc(promo.start_date)
        p_end = ensure_utc(promo.end_date)
        if p_start <= effective_time <= p_end:
            promotions.append(promo)

    exclusive_promo = next((p for p in promotions if p.is_exclusive), None)
    if exclusive_promo:
        promos_to_apply = [exclusive_promo]
    else:
        promos_to_apply = promotions

    for promo in promos_to_apply:
        disc = (current_unit_price * promo.discount_percentage).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        current_unit_price = current_unit_price - disc
        rules_applied.append(
            {
                "rule_type": "PROMOTION",
                "name": promo.name,
                "code": promo.code,
                "priority": promo.priority,
                "is_exclusive": promo.is_exclusive,
                "discount_percentage": str(promo.discount_percentage * Decimal("100")),
                "discount_amount": str(disc),
            }
        )

    final_unit_price = max(Decimal("0.000000"), current_unit_price)
    subtotal = (final_unit_price * quantity).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    coupon_discount = Decimal("0.000000")
    if coupon_code:
        normalized_code = coupon_code.strip().upper()
        coupons = (
            db.execute(
                select(CouponModel).where(
                    CouponModel.company_id == company_id,
                    CouponModel.code == normalized_code,
                    CouponModel.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )

        for coupon in coupons:
            c_start = ensure_utc(coupon.start_date)
            c_end = ensure_utc(coupon.end_date)
            if (
                c_start <= effective_time <= c_end
                and coupon.current_uses < coupon.max_uses
                and coupon.min_purchase_amount <= subtotal
            ):
                if coupon.discount_type == "PERCENTAGE":
                    coupon_discount = (subtotal * coupon.discount_value).quantize(
                        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                    )
                else:
                    coupon_discount = min(subtotal, coupon.discount_value)
                rules_applied.append(
                    {
                        "rule_type": "COUPON",
                        "code": coupon.code,
                        "discount_type": coupon.discount_type,
                        "discount_amount": str(coupon_discount),
                    }
                )
                break

    net_subtotal = max(Decimal("0.000000"), subtotal - coupon_discount)
    tax_rate = product.tax_rate

    price_includes_tax = profile.price_includes_tax if profile else False
    if price_includes_tax:
        base_taxable = (net_subtotal / (Decimal("1") + tax_rate)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )
        tax_amount = (net_subtotal - base_taxable).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        total_estimated = net_subtotal
        subtotal_display = base_taxable
    else:
        base_taxable = net_subtotal
        tax_amount = (net_subtotal * tax_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        total_estimated = (net_subtotal + tax_amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        subtotal_display = net_subtotal

    total_discount = max(Decimal("0"), (base_unit_price * quantity) - net_subtotal)
    discount_percentage = Decimal("0.00")
    if base_unit_price > 0:
        discount_percentage = ((total_discount / (base_unit_price * quantity)) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )

    return {
        "product_id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "quantity": str(quantity),
        "unit_of_measure": product.unit_of_measure,
        "variant": variant_info,
        "unit_price_base": str(base_unit_price),
        "discount_percentage": str(discount_percentage),
        "discount_applied": str(total_discount),
        "final_unit_price": str(final_unit_price),
        "subtotal": str(subtotal_display),
        "tax_rate": str(tax_rate),
        "tax_amount": str(tax_amount),
        "total_estimated": str(total_estimated),
        "rules_applied": rules_applied,
    }
