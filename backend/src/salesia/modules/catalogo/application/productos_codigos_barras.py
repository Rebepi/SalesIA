from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_codigos_barras import BarcodeCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductBarcodeModel, ProductVariantModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def create_product_barcode(product_id: UUID, req: BarcodeCreateModel, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    if req.variant_id:
        variant = db.scalar(select(ProductVariantModel).where(ProductVariantModel.company_id == current_user.company_id, ProductVariantModel.id == req.variant_id, ProductVariantModel.product_id == product_id, ProductVariantModel.is_active.is_(True)))
        if not variant or not variant.operational_product_id:
            raise DomainNotFoundException("Variante activa no encontrada para este producto.")
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == variant.operational_product_id))

    existing = db.execute(
        select(ProductBarcodeModel).where(
            ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.barcode == req.barcode
        )
    ).scalar_one_or_none()

    if existing:
        raise DomainConflictException(f"El código de barras '{req.barcode}' ya está registrado en esta empresa.")

    bc = ProductBarcodeModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=product.id,
        variant_id=req.variant_id,
        barcode=req.barcode,
        barcode_type=req.barcode_type,
        is_active=True,
    )

    db.add(bc)

    db.commit()

    return {
        "id": str(bc.id),
        "product_id": str(bc.product_id),
        "variant_id": str(bc.variant_id) if bc.variant_id else None,
        "barcode": bc.barcode,
        "barcode_type": bc.barcode_type,
    }
