from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.caja_sesiones_movimientos as service_caja_sesiones_movimientos
from salesia.modules.finanzas.application.contracts.caja_sesiones_movimientos import (
    CashSessionMovementRequest,
    CashSessionOpenRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/cash-sessions", status_code=status.HTTP_201_CREATED)
def open_cash_session(
    payload: CashSessionOpenRequest,
    current_user: AuthenticatedUser = Depends(require_permission("cash:register:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_caja_sesiones_movimientos.open_cash_session(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/cash-sessions")
def list_cash_sessions(
    status: Optional[str] = Query(None),
    terminal_code: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("cash:register:manage")),
    db: Session = Depends(get_db),
):

    return service_caja_sesiones_movimientos.list_cash_sessions(
        status=status, terminal_code=terminal_code, current_user=current_user, db=db
    )


@router.get("/cash-sessions/current")
def current_cash_session(
    branch_id: UUID = Query(...),
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_caja_sesiones_movimientos.current_cash_session(branch_id=branch_id, current_user=current_user, db=db)


@router.post("/cash-sessions/{session_id}/movements", status_code=status.HTTP_201_CREATED)
def add_cash_session_movement(
    session_id: UUID,
    payload: CashSessionMovementRequest,
    current_user: AuthenticatedUser = Depends(require_permission("cash:register:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_caja_sesiones_movimientos.add_cash_session_movement(
        session_id=session_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
