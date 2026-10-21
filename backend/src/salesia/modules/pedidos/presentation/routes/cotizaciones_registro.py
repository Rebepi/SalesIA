from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.cotizaciones_registro as service_cotizaciones_registro
from salesia.modules.pedidos.application.contracts.cotizaciones_registro import QuotationCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/quotations", status_code=201)
def create_quotation(
    req: QuotationCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_cotizaciones_registro.create_quotation(
        req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/quotations")
def list_quotations(
    status_filter: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("quotations:read", "sales:read")),
    db: Session = Depends(get_db),
):

    return service_cotizaciones_registro.list_quotations(
        status_filter=status_filter,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/quotations/{quotation_id}")
def get_quotation(
    quotation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:read")),
    db: Session = Depends(get_db),
):

    return service_cotizaciones_registro.get_quotation(quotation_id=quotation_id, current_user=current_user, db=db)
