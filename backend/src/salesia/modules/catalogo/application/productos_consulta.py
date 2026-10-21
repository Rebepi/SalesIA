import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import (
    ProductAttachmentModel,
    ProductBarcodeModel,
    ProductProfileModel,
    ProductVariantModel,
)
from salesia.modules.catalogo.service import get_or_create_product_profile
from salesia.modules.inventario.infrastructure_models import InventoryLot, InventorySerial, SupplyDocument, SupplyLine
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException, DomainNotFoundException
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, WarehouseModel


def list_products(
    category: Optional[str],
    search: Optional[str],
    status_filter: Optional[str],
    product_type: Optional[str],
    min_price: Optional[Decimal],
    max_price: Optional[Decimal],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(ProductModel).where(ProductModel.company_id == current_user.company_id)

    if category:
        query = query.where(ProductModel.category == category)

    if min_price is not None:
        query = query.where(ProductModel.unit_price >= min_price)

    if max_price is not None:
        query = query.where(ProductModel.unit_price <= max_price)

    if search:
        pattern = f"%{search}%"

        barcode_matches = db.scalars(
            select(ProductBarcodeModel.product_id).where(
                ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.barcode.ilike(pattern)
            )
        ).all()

        query = query.where(
            or_(
                ProductModel.name.ilike(pattern),
                ProductModel.sku.ilike(pattern),
                ProductModel.id.in_(barcode_matches) if barcode_matches else False,
            )
        )

    total_count = db.scalar(select(func.count()).select_from(query.subquery()))

    products = db.execute(query.order_by(ProductModel.created_at.desc()).limit(limit).offset(offset)).scalars().all()

    items = []

    for p in products:
        prof = db.execute(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == p.id
            )
        ).scalar_one_or_none()

        if status_filter and prof and prof.status != status_filter:
            continue

        if product_type and prof and prof.product_type != product_type:
            continue

        item = {
            "id": str(p.id),
            "product_id": str(p.id),
            "company_id": str(p.company_id),
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "unit_of_measure": p.unit_of_measure,
            "unit_price": str(p.unit_price),
            "tax_rate": str(p.tax_rate),
            "is_active": p.is_active,
            "product_type": prof.product_type if prof else "product",
            "status": prof.status if prof else ("active" if p.is_active else "archived"),
            "track_inventory": prof.track_inventory if prof else True,
            "barcode": prof.barcode if prof else None,
            "warranty_period_months": prof.warranty_period_months if prof else 0,
            "is_kit": prof.is_kit if prof else False,
            "category_id": str(prof.category_id) if prof and prof.category_id else None,
            "supplier_id": str(prof.supplier_id) if prof and prof.supplier_id else None,
            "brand": prof.brand if prof else None,
            "image_url": prof.image_url if prof else None,
            "tracking_mode": prof.tracking_mode if prof else "NONE",
            "created_at": p.created_at.isoformat(),
        }

        if "products:cost:read" in current_user.permissions:
            item["unit_cost"] = str(p.unit_cost)

            item["margin_amount"] = str(p.unit_price - p.unit_cost)

        items.append(item)

    return {"items": items, "total_count": total_count, "limit": limit, "offset": offset}


def search_products_with_availability(
    warehouse_id: UUID, search: Optional[str], limit: int, offset: int, current_user: AuthenticatedUser, db: Session
):
    selected_warehouse = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not selected_warehouse:
        raise HTTPException(422, "Seleccione un almacén activo de su empresa.")

    query = select(ProductModel).where(
        ProductModel.company_id == current_user.company_id, ProductModel.is_active.is_(True)
    )

    if search:
        pattern = f"%{search.strip()}%"

        barcode_matches = db.scalars(
            select(ProductBarcodeModel.product_id).where(
                ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.barcode.ilike(pattern)
            )
        ).all()

        query = query.where(
            or_(
                ProductModel.name.ilike(pattern),
                ProductModel.sku.ilike(pattern),
                ProductModel.id.in_(barcode_matches) if barcode_matches else False,
            )
        )

    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    products = db.scalars(query.order_by(ProductModel.name, ProductModel.sku).offset(offset).limit(limit)).all()

    items = []

    for product_row in products:
        product_profile = db.scalar(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == current_user.company_id,
                ProductProfileModel.product_id == product_row.id,
            )
        )

        stock = db.scalar(
            select(InventoryStockModel).where(
                InventoryStockModel.company_id == current_user.company_id,
                InventoryStockModel.warehouse_id == warehouse_id,
                InventoryStockModel.product_id == product_row.id,
            )
        )

        available = (stock.physical_quantity - stock.reserved_quantity) if stock else Decimal("0")

        has_lots = bool(
            db.scalar(
                select(InventoryLot.id)
                .where(
                    InventoryLot.company_id == current_user.company_id,
                    InventoryLot.product_id == product_row.id,
                    InventoryLot.status == "ACTIVE",
                )
                .limit(1)
            )
        )

        has_serials = bool(
            db.scalar(
                select(InventorySerial.id)
                .where(
                    InventorySerial.company_id == current_user.company_id,
                    InventorySerial.product_id == product_row.id,
                    InventorySerial.warehouse_id == warehouse_id,
                    InventorySerial.status == "IN_STOCK",
                )
                .limit(1)
            )
        )

        next_restock_at = None

        purchase_rows = (
            db.execute(
                select(SupplyDocument.details_json)
                .join(SupplyLine, SupplyLine.document_id == SupplyDocument.id)
                .where(
                    SupplyDocument.company_id == current_user.company_id,
                    SupplyDocument.kind == "PURCHASE_ORDER",
                    SupplyDocument.warehouse_id == warehouse_id,
                    SupplyDocument.status.in_(("submitted", "approved", "partially_received")),
                    SupplyLine.product_id == product_row.id,
                    SupplyLine.processed_quantity < SupplyLine.quantity,
                )
                .order_by(SupplyDocument.created_at)
            )
            .scalars()
            .all()
        )

        for raw_details in purchase_rows:
            try:
                delivery_date = json.loads(raw_details or "{}").get("delivery_date")

                if delivery_date and (next_restock_at is None or delivery_date < next_restock_at):
                    next_restock_at = delivery_date

            except (TypeError, ValueError, json.JSONDecodeError):
                continue

        items.append(
            {
                "id": str(product_row.id),
                "product_id": str(product_row.id),
                "sku": product_row.sku,
                "name": product_row.name,
                "category": product_row.category,
                "unit_of_measure": product_row.unit_of_measure,
                "unit_price": str(product_row.unit_price),
                "tax_rate": str(product_row.tax_rate),
                "physical_quantity": str(stock.physical_quantity if stock else Decimal("0")),
                "reserved_quantity": str(stock.reserved_quantity if stock else Decimal("0")),
                "available_quantity": str(available),
                "has_lots": has_lots,
                "has_serials": has_serials,
                "next_restock_at": next_restock_at,
                "track_inventory": product_profile.track_inventory if product_profile else True,
            }
        )

    return {"items": items, "total_count": total_count, "limit": limit, "offset": offset}


def get_product(product_id: UUID, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        other = db.scalar(select(ProductModel.id).where(ProductModel.id == product_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise DomainNotFoundException("Producto no encontrado.")

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    variants = (
        db.execute(
            select(ProductVariantModel).where(
                ProductVariantModel.company_id == current_user.company_id,
                ProductVariantModel.product_id == product.id,
                ProductVariantModel.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )

    attachments = (
        db.execute(
            select(ProductAttachmentModel).where(
                ProductAttachmentModel.company_id == current_user.company_id,
                ProductAttachmentModel.product_id == product.id,
            )
        )
        .scalars()
        .all()
    )

    att_list = []

    for att in attachments:
        url = att.file_url if (att.file_url and att.file_url.startswith("http")) else "/static/placeholder-product.webp"

        att_list.append(
            {
                "id": str(att.id),
                "file_name": att.file_name,
                "file_url": url,
                "content_type": att.content_type,
                "is_primary": att.is_primary,
            }
        )

    data = {
        "id": str(product.id),
        "product_id": str(product.id),
        "company_id": str(product.company_id),
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "unit_of_measure": product.unit_of_measure,
        "unit_price": str(product.unit_price),
        "tax_rate": str(product.tax_rate),
        "is_active": product.is_active,
        "description": profile.description,
        "product_type": profile.product_type,
        "status": profile.status,
        "track_inventory": profile.track_inventory,
        "barcode": profile.barcode,
        "warranty_period_months": profile.warranty_period_months,
        "warranty_policy": profile.warranty_policy,
        "price_includes_tax": profile.price_includes_tax,
        "is_kit": profile.is_kit,
        "variants": [
            {
                "id": str(v.id),
                "sku": v.sku,
                "price_delta": str(v.price_delta),
                "attributes": json.loads(v.attributes_json),
            }
            for v in variants
        ],
        "attachments": att_list
        if att_list
        else [
            {
                "id": "fallback",
                "file_name": "placeholder",
                "file_url": "/static/placeholder-product.webp",
                "content_type": "image/webp",
                "is_primary": True,
            }
        ],
        "created_at": product.created_at.isoformat(),
    }

    if "products:cost:read" in current_user.permissions:
        data["unit_cost"] = str(product.unit_cost)

        data["margin_amount"] = str(product.unit_price - product.unit_cost)

    return data
