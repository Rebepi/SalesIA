from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.cotizaciones_documentos as service_cotizaciones_documentos
from salesia.modules.pedidos.application.contracts.cotizaciones_documentos import QuotationSendRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/quotations/{quotation_id}/preview")
def preview_quotation(
    quotation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:read")),
    db: Session = Depends(get_db),
):

    return service_cotizaciones_documentos.preview_quotation(
        quotation_id=quotation_id, current_user=current_user, db=db
    )


@router.get("/quotations/{quotation_id}/pdf")
def download_quotation_pdf(
    quotation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:read")),
    db: Session = Depends(get_db),
):

    return service_cotizaciones_documentos.download_quotation_pdf(
        quotation_id=quotation_id, current_user=current_user, db=db
    )


@router.post("/quotations/{quotation_id}/send")
def send_quotation(
    quotation_id: UUID,
    req: QuotationSendRequest,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
):

    return service_cotizaciones_documentos.send_quotation(
        quotation_id=quotation_id, req=req, current_user=current_user, db=db
    )
