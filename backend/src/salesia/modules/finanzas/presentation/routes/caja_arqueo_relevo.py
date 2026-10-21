from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.caja_arqueo_relevo as service_caja_arqueo_relevo
from salesia.modules.finanzas.application.contracts.caja_arqueo_relevo import (
    ApproveDifferenceRequest,
    BlindCountRequest,
    CashSessionCloseRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/cash-sessions/{session_id}/blind-status")
def get_blind_session_status(
    session_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_caja_arqueo_relevo.get_blind_session_status(session_id=session_id, current_user=current_user, db=db)


@router.post("/cash-sessions/{session_id}/blind-count")
def submit_blind_count(
    session_id: UUID,
    payload: BlindCountRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_caja_arqueo_relevo.submit_blind_count(
        session_id=session_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/cash-sessions/{session_id}/approve-difference")
def approve_cash_difference(
    session_id: UUID,
    payload: ApproveDifferenceRequest,
    current_user: AuthenticatedUser = Depends(require_permission("cash:register:manage")),
    db: Session = Depends(get_db),
):

    return service_caja_arqueo_relevo.approve_cash_difference(
        session_id=session_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/cash-sessions/{session_id}/close")
def close_cash_session(
    session_id: UUID,
    payload: CashSessionCloseRequest,
    current_user: AuthenticatedUser = Depends(require_permission("cash:register:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_caja_arqueo_relevo.close_cash_session(
        session_id=session_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
