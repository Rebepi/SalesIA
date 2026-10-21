from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_adjuntos as service_productos_adjuntos
from salesia.modules.catalogo.application.contracts.productos_adjuntos import AttachmentCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/{product_id}/attachments", status_code=status.HTTP_201_CREATED)
def create_attachment(
    product_id: UUID,
    req: AttachmentCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_adjuntos.create_attachment(
        product_id=product_id, req=req, current_user=current_user, db=db
    )
