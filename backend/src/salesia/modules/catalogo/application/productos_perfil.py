import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_perfil import ProductCommercialProfileUpdate
from salesia.modules.catalogo.infrastructure_models import (
    ProductAttachmentModel,
    ProductBarcodeModel,
    ProductKitItemModel,
    ProductVariantModel,
    ProductVolumeTierModel,
    ProductWarrantyClaimModel,
)
from salesia.modules.catalogo.service import get_or_create_product_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def get_product_commercial_profile(product_id: UUID, current_user: AuthenticatedUser, db: Session):
    product = db.scalar(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.company_id == current_user.company_id)
    )

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    variants = db.scalars(
        select(ProductVariantModel)
        .where(ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.product_id == product.id)
        .order_by(ProductVariantModel.created_at.desc())
    ).all()

    barcodes = db.scalars(
        select(ProductBarcodeModel)
        .where(ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.product_id == product.id)
        .order_by(ProductBarcodeModel.created_at.desc())
    ).all()

    tiers = db.scalars(
        select(ProductVolumeTierModel)
        .where(
            ProductVolumeTierModel.company_id == current_user.company_id,
            ProductVolumeTierModel.product_id == product.id,
        )
        .order_by(ProductVolumeTierModel.min_quantity)
    ).all()

    kit_items = db.scalars(
        select(ProductKitItemModel)
        .where(
            ProductKitItemModel.company_id == current_user.company_id, ProductKitItemModel.kit_product_id == product.id
        )
        .order_by(ProductKitItemModel.created_at.desc())
    ).all()

    claims = db.scalars(
        select(ProductWarrantyClaimModel)
        .where(
            ProductWarrantyClaimModel.company_id == current_user.company_id,
            ProductWarrantyClaimModel.product_id == product.id,
        )
        .order_by(ProductWarrantyClaimModel.claim_date.desc())
    ).all()

    attachments = db.scalars(
        select(ProductAttachmentModel)
        .where(
            ProductAttachmentModel.company_id == current_user.company_id,
            ProductAttachmentModel.product_id == product.id,
        )
        .order_by(ProductAttachmentModel.is_primary.desc(), ProductAttachmentModel.created_at.desc())
    ).all()

    return {
        "product": {
            "id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "category": product.category,
            "unit_of_measure": product.unit_of_measure,
            "unit_price": str(product.unit_price),
            "unit_cost": str(product.unit_cost) if "products:cost:read" in current_user.permissions else None,
            "tax_rate": str(product.tax_rate),
            "is_active": product.is_active,
        },
        "profile": {
            "description": profile.description,
            "product_type": profile.product_type,
            "status": profile.status,
            "track_inventory": profile.track_inventory,
            "default_warranty_months": profile.warranty_period_months,
            "warranty_period_months": profile.warranty_period_months,
            "allow_fractional": False,
            "is_kit": profile.is_kit,
            "brand": profile.brand,
            "tracking_mode": profile.tracking_mode,
        },
        "variants": [
            {
                "id": str(item.id),
                "sku": item.sku,
                "attributes": json.loads(item.attributes_json),
                "price_delta": str(item.price_delta),
                "operational_product_id": str(item.operational_product_id) if item.operational_product_id else None,
                "name": db.get(ProductModel, item.operational_product_id).name if item.operational_product_id else item.sku,
                "is_active": item.is_active,
            }
            for item in variants
        ],
        "barcodes": [
            {
                "id": str(item.id),
                "barcode": item.barcode,
                "barcode_type": item.barcode_type,
                "is_primary": profile.barcode == item.barcode,
                "is_active": item.is_active,
            }
            for item in barcodes
        ],
        "volume_tiers": [
            {
                "id": str(item.id),
                "min_quantity": str(item.min_quantity),
                "unit_price": str(item.unit_price) if item.unit_price is not None else None,
                "discount_percentage": str(item.discount_percentage) if item.discount_percentage is not None else None,
            }
            for item in tiers
        ],
        "kit_items": [
            {"id": str(item.id), "component_product_id": str(item.component_product_id), "quantity": str(item.quantity)}
            for item in kit_items
        ],
        "warranty_claims": [
            {
                "id": str(item.id),
                "sale_id": str(item.sale_id),
                "serial_number": item.serial_number,
                "description": item.issue_description,
                "status": item.status,
                "created_at": item.claim_date.isoformat(),
            }
            for item in claims
        ],
        "attachments": [
            {
                "id": str(item.id),
                "file_name": item.file_name,
                "file_url": item.file_url,
                "content_type": item.content_type,
                "is_primary": item.is_primary,
            }
            for item in attachments
        ],
    }


def update_product_commercial_profile(
    product_id: UUID, req: ProductCommercialProfileUpdate, current_user: AuthenticatedUser, db: Session
):
    product = db.scalar(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.company_id == current_user.company_id)
    )

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    profile.product_type = req.product_type

    profile.track_inventory = req.track_inventory if req.product_type == "product" else False

    profile.warranty_period_months = req.default_warranty_months

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory, profile.is_kit, product.is_active)
    db.commit()

    return {
        "product_id": str(product.id),
        "product_type": profile.product_type,
        "track_inventory": profile.track_inventory,
        "default_warranty_months": profile.warranty_period_months,
        "allow_fractional": req.allow_fractional,
    }
