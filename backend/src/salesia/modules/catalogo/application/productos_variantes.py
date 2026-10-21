import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_variantes import VariantCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel, ProductVariantModel
from fastapi import HTTPException
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def list_product_variants(product_id: UUID, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    variants = (
        db.execute(
            select(ProductVariantModel).where(
                ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.product_id == product_id
            )
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": str(v.id),
            "sku": v.sku,
            "attributes": json.loads(v.attributes_json),
            "price_delta": str(v.price_delta),
            "effective_price": str(product.unit_price + v.price_delta),
            "is_active": v.is_active,
        }
        for v in variants
    ]


def create_product_variant(product_id: UUID, req: VariantCreateModel, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    dup_sku = db.execute(
        select(ProductVariantModel).where(
            ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.sku == req.sku
        )
    ).scalar_one_or_none()

    if dup_sku:
        raise DomainConflictException(f"Ya existe una variante con el SKU '{req.sku}'.")

    req.attributes = {str(key).strip(): value for key, value in req.attributes.items() if value is not None and str(value).strip()}
    normalized_attrs = json.dumps(req.attributes, sort_keys=True)

    existing_variants = (
        db.execute(
            select(ProductVariantModel).where(
                ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.product_id == product_id
            )
        )
        .scalars()
        .all()
    )

    for ev in existing_variants:
        if json.dumps(json.loads(ev.attributes_json), sort_keys=True) == normalized_attrs:
            raise DomainConflictException("Ya existe una variante registrada con la misma combinación de atributos.")

    if db.scalar(select(ProductModel.id).where(ProductModel.company_id == current_user.company_id, ProductModel.sku == req.sku)):
        raise DomainConflictException("El SKU de la variante ya está utilizado por otro producto.")
    if product.unit_price + req.price_delta < 0:
        raise HTTPException(422, "El precio final de la variante no puede ser negativo.")
    if not req.attributes or any(not str(key).strip() or not str(value).strip() for key, value in req.attributes.items()):
        raise HTTPException(422, "Define al menos un atributo con nombre y valor.")
    operational = ProductModel(company_id=current_user.company_id, sku=req.sku, name=req.name or (product.name + " · " + ", ".join(str(value) for value in req.attributes.values()))[:255], category=product.category, unit_of_measure=product.unit_of_measure, unit_cost=product.unit_cost, unit_price=product.unit_price + req.price_delta, tax_rate=product.tax_rate, is_active=True)
    db.add(operational)
    db.flush()
    profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == product.id))
    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory if profile else True)
    if profile:
        db.add(ProductProfileModel(company_id=current_user.company_id, product_id=operational.id, description=profile.description, product_type=profile.product_type, status=profile.status, track_inventory=profile.track_inventory, category_id=profile.category_id, warranty_period_months=profile.warranty_period_months, warranty_policy=profile.warranty_policy, is_kit=False, price_includes_tax=profile.price_includes_tax, supplier_id=profile.supplier_id, brand=profile.brand, image_url=profile.image_url, length_cm=profile.length_cm, width_cm=profile.width_cm, height_cm=profile.height_cm, weight_kg=profile.weight_kg, tracking_mode=profile.tracking_mode))

    variant = ProductVariantModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=product.id,
        sku=req.sku,
        attributes_json=normalized_attrs,
        price_delta=req.price_delta,
        is_active=True,
        operational_product_id=operational.id,
    )

    db.add(variant)

    db.flush()

    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="CREATE_PRODUCT_VARIANT", entity_type="Product", entity_id=operational.id, diff={"parent_product_id": str(product.id), "variant_id": str(variant.id), "attributes": req.attributes})

    db.commit()

    db.refresh(variant)

    return {
        "id": str(variant.id),
        "sku": variant.sku,
        "attributes": req.attributes,
        "price_delta": str(variant.price_delta),
        "effective_price": str(product.unit_price + variant.price_delta),
        "is_active": variant.is_active,
        "operational_product_id": str(operational.id),
    }
