from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_adjuntos import AttachmentCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductAttachmentModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def create_attachment(product_id: UUID, req: AttachmentCreateModel, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    att = ProductAttachmentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=product.id,
        file_name=req.file_name,
        file_url=req.file_url,
        content_type=req.content_type,
        file_size_bytes=req.file_size_bytes,
        is_primary=req.is_primary,
        is_private=req.is_private,
    )

    db.add(att)

    db.commit()

    return {"id": str(att.id), "file_name": att.file_name, "file_url": att.file_url, "is_primary": att.is_primary}
