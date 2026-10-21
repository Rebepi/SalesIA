from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.portal_cotizaciones as service_portal_cotizaciones
from salesia.modules.pedidos.application.contracts.portal_cotizaciones import PublicQuotationAcceptance
from salesia.shared.infrastructure.database import get_db

quotation_portal_router = APIRouter(prefix="")


@quotation_portal_router.get("/quotation-portal/{quotation_id}")
def open_public_quotation(
    quotation_id: UUID, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
):

    return service_portal_cotizaciones.open_public_quotation(
        quotation_id=quotation_id, authorization=authorization, db=db
    )


@quotation_portal_router.post("/quotation-portal/{quotation_id}/accept")
def accept_public_quotation(
    quotation_id: UUID,
    payload: PublicQuotationAcceptance,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):

    return service_portal_cotizaciones.accept_public_quotation(
        quotation_id=quotation_id, payload=payload, authorization=authorization, db=db
    )


@quotation_portal_router.get("/quotation-portal/{quotation_id}/pdf")
def public_quotation_pdf(
    quotation_id: UUID, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
):

    return service_portal_cotizaciones.public_quotation_pdf(
        quotation_id=quotation_id, authorization=authorization, db=db
    )
