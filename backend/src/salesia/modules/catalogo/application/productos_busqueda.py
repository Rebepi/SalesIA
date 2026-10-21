from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductBarcodeModel, ProductVariantModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def lookup_product_by_barcode(code: str, current_user: AuthenticatedUser, db: Session):
    bc = db.execute(
        select(ProductBarcodeModel).where(
            ProductBarcodeModel.company_id == current_user.company_id,
            ProductBarcodeModel.barcode == code,
            ProductBarcodeModel.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if not bc:
        raise DomainNotFoundException(f"Código de barras '{code}' no registrado en el sistema.")

    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == bc.product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto asociado al código de barras no encontrado.")

    variant = None

    if bc.variant_id:
        v = db.execute(
            select(ProductVariantModel).where(
                ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.id == bc.variant_id
            )
        ).scalar_one_or_none()

        if v:
            variant = {"id": str(v.id), "sku": v.sku, "price_delta": str(v.price_delta)}

    return {
        "product_id": str(product.id),
        "sku": product.sku,
        "name": product.name,
        "unit_price": str(product.unit_price),
        "barcode": bc.barcode,
        "variant": variant,
    }
