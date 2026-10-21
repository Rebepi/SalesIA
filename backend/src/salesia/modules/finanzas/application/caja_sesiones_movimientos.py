import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.contracts.caja_sesiones_movimientos import (
    CashSessionMovementRequest,
    CashSessionOpenRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import BranchModel, CashSessionModel, CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request
from salesia.modules.finanzas.application.control_arqueo import count_control
from salesia.modules.organizacion.application.periodos import business_date, require_open_period


def open_cash_session(
    payload: CashSessionOpenRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, "cash.open", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))

    if (
        db.scalar(
            select(BranchModel.id).where(
                BranchModel.id == payload.branch_id, BranchModel.company_id == current_user.company_id
            )
        )
        is None
    ):
        raise HTTPException(422, "La sucursal no existe en esta empresa.")

    existing = db.scalar(
        select(CashSessionModel.id).where(
            CashSessionModel.company_id == current_user.company_id,
            CashSessionModel.terminal_code == payload.terminal_code,
            CashSessionModel.status == "open",
        )
    )

    if existing:
        raise HTTPException(409, "La terminal ya tiene una sesión abierta.")

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    opened_at = datetime.now(timezone.utc)

    row = CashSessionModel(
        company_id=current_user.company_id,
        branch_id=payload.branch_id,
        user_id=current_user.user_id,
        terminal_code=payload.terminal_code,
        currency=payload.currency or company.base_currency,
        status="open",
        opened_at=opened_at,
        initial_cash=payload.opening_balance,
        expected_cash=payload.opening_balance,
        movements_json="[]",
    )

    db.add(row)

    db.flush()

    response = {
        "session_id": str(row.id),
        "branch_id": str(row.branch_id),
        "terminal_code": row.terminal_code,
        "currency": row.currency,
        "opening_balance": str(row.initial_cash),
        "status": row.status,
        "opened_by": current_user.email,
        "opened_at": row.opened_at.isoformat(),
    }

    complete_request(record, response)

    db.commit()

    return response


def list_cash_sessions(
    status: Optional[str], terminal_code: Optional[str], current_user: AuthenticatedUser, db: Session
):
    stmt = select(CashSessionModel).where(CashSessionModel.company_id == current_user.company_id)

    if status:
        stmt = stmt.where(CashSessionModel.status == status)

    if terminal_code:
        stmt = stmt.where(CashSessionModel.terminal_code == terminal_code)

    stmt = stmt.order_by(CashSessionModel.opened_at.desc())

    rows = db.scalars(stmt).all()

    return [
        {
            "id": str(r.id),
            "session_id": str(r.id),
            "branch_id": str(r.branch_id),
            "user_id": str(r.user_id),
            "terminal_code": r.terminal_code,
            "currency": r.currency,
            "status": r.status,
            "opened_at": r.opened_at.isoformat(),
            "closed_at": r.closed_at.isoformat() if r.closed_at else None,
            "initial_cash": str(r.initial_cash),
            "expected_cash": str(r.expected_cash),
            "actual_cash": str(r.actual_cash) if r.actual_cash is not None else None,
            "difference_cash": str(r.difference_cash) if r.difference_cash is not None else None,
            "notes": r.notes,
            "control": count_control(r),
            "can_count": r.status == "open" and r.user_id == current_user.user_id,
            "can_approve": r.status == "open" and r.user_id != current_user.user_id and bool({"organization:manage", "approvals:manage"} & set(current_user.permissions)),
            "movements": json.loads(r.movements_json) if r.movements_json else [],
        }
        for r in rows
    ]


def current_cash_session(branch_id: UUID, current_user: AuthenticatedUser, db: Session):
    session = db.scalar(
        select(CashSessionModel)
        .where(
            CashSessionModel.company_id == current_user.company_id,
            CashSessionModel.branch_id == branch_id,
            CashSessionModel.user_id == current_user.user_id,
            CashSessionModel.status == "open",
        )
        .order_by(CashSessionModel.opened_at.desc())
    )

    if not session:
        return {"session": None}

    return {
        "session": {
            "session_id": str(session.id),
            "branch_id": str(session.branch_id),
            "terminal_code": session.terminal_code,
            "currency": session.currency,
            "status": session.status,
        }
    }


def add_cash_session_movement(
    session_id: UUID,
    payload: CashSessionMovementRequest,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    record, cached = claim_request(
        db, current_user.company_id, f"cash.movement:{session_id}", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    row = db.scalar(
        select(CashSessionModel)
        .where(CashSessionModel.company_id == current_user.company_id, CashSessionModel.id == session_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Sesión de caja no encontrada.")

    if row.status != "open":
        raise HTTPException(409, "La sesión de caja está cerrada.")

    if row.user_id != current_user.user_id and not ({"organization:manage", "approvals:manage"} & set(current_user.permissions)):
        raise HTTPException(403, "Solo el responsable o un supervisor autorizado puede operar esta caja.")

    amount = payload.amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if amount != payload.amount:
        raise HTTPException(422, "El importe admite como máximo seis decimales.")

    if payload.movement_type == "WITHDRAWAL" and row.expected_cash < amount:
        raise HTTPException(409, "Saldo insuficiente en caja.")

    row.expected_cash = row.expected_cash + amount if payload.movement_type == "DEPOSIT" else row.expected_cash - amount

    movement = {
        "movement_id": str(uuid4()),
        "movement_type": payload.movement_type,
        "amount": str(amount),
        "reason": payload.reason,
        "balance_after": str(row.expected_cash),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": str(current_user.user_id),
    }

    movements = json.loads(row.movements_json)

    movements.append(movement)

    row.movements_json = json.dumps(movements)

    response = {
        "session_id": str(row.id),
        **movement,
        "current_balance": str(row.expected_cash),
        "recorded_at": movement["timestamp"],
    }

    complete_request(record, response)

    db.commit()

    return response
