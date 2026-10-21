from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.ventas.application.ventas_operaciones as service_ventas_operaciones
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.ventas.application.contracts.ventas_operaciones import (
    AnnulSaleRequest,
    ConfirmSaleRequest,
    CorrectSaleRequest,
    CreateSaleDraftRequest,
    UpdateSaleDraftRequest,
)
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/sales")


@router.post("", status_code=201)
@router.post("/draft", status_code=201)
def create_draft(
    payload: CreateSaleDraftRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ventas_operaciones.create_draft(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.patch("/{sale_id}")
def update_draft(
    sale_id: UUID,
    payload: UpdateSaleDraftRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ventas_operaciones.update_draft(
        sale_id=sale_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/{sale_id}/confirm")
def confirm_sale(
    sale_id: UUID,
    payload: Optional[ConfirmSaleRequest] = None,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_ventas_operaciones.confirm_sale(
        sale_id=sale_id, payload=payload, idempotency_key=idempotency_key, current_user=current_user, db=db
    )


@router.post("/{sale_id}/cancel")
@router.post("/{sale_id}/annul")
def annul_sale(
    sale_id: UUID,
    payload: AnnulSaleRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:cancel")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ventas_operaciones.annul_sale(
        sale_id=sale_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/{sale_id}/clone")
def clone_sale_as_draft(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ventas_operaciones.clone_sale_as_draft(
        sale_id=sale_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/{sale_id}/prevalidate")
def prevalidate_sale(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_ventas_operaciones.prevalidate_sale(sale_id=sale_id, current_user=current_user, db=db)


@router.get("/{sale_id}/document")
def get_sale_document(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_ventas_operaciones.get_sale_document(sale_id=sale_id, current_user=current_user, db=db)


@router.post("/{sale_id}/correct")
def correct_sale(
    sale_id: UUID,
    payload: CorrectSaleRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ventas_operaciones.correct_sale(
        sale_id=sale_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
