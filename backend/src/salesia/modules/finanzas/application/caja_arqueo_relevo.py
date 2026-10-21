import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.control_arqueo import count_control, ledger_fingerprint, require_current_count
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.finanzas.application.contracts.caja_arqueo_relevo import (
    ApproveDifferenceRequest,
    BlindCountRequest,
    CashSessionCloseRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CashSessionModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def get_blind_session_status(session_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(CashSessionModel).where(
            CashSessionModel.company_id == current_user.company_id, CashSessionModel.id == session_id
        )
    )

    if not row:
        raise HTTPException(404, "Sesión de caja no encontrada.")

    return {
        "session_id": str(row.id),
        "terminal_code": row.terminal_code,
        "status": row.status,
        "opened_at": row.opened_at.isoformat(),
    }


def submit_blind_count(session_id: UUID, payload: BlindCountRequest, current_user: AuthenticatedUser, db: Session):
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

    if row.user_id != current_user.user_id:
        raise HTTPException(403, "El arqueo debe registrarlo el responsable de la sesión.")

    if payload.counted_cash.quantize(Decimal("0.000001")) != payload.counted_cash:
        raise HTTPException(422, "El conteo admite como máximo seis decimales.")

    if payload.denominations:
        total = Decimal("0")

        for denomination, quantity in payload.denominations.items():
            try:
                value = Decimal(denomination)

            except Exception:
                raise HTTPException(422, "Una de las denominaciones no es válida.")

            if not value.is_finite() or value <= 0 or quantity < 0 or quantity > 1000000:
                raise HTTPException(
                    422, "Las denominaciones deben ser positivas y sus cantidades no pueden ser negativas."
                )

            total += value * quantity

        if total != payload.counted_cash:
            raise HTTPException(422, "El total de denominaciones no coincide con el efectivo contado.")

    if any(not amount.is_finite() or amount < 0 for amount in payload.non_cash_totals.values()):
        raise HTTPException(422, "Los medios no monetarios deben tener totales válidos y no negativos.")

    diff = (payload.counted_cash - row.expected_cash).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    requires_approval = diff != Decimal("0.000000")

    row.actual_cash = payload.counted_cash

    row.difference_cash = diff
    previous = count_control(row)
    history = previous.get("history", [])
    if previous:
        history.append({key: value for key, value in previous.items() if key not in {"history", "is_current"}})
    control = {
        "version": previous.get("version", 0) + 1,
        "currency": row.currency,
        "counted_cash": str(payload.counted_cash),
        "expected_cash": str(row.expected_cash),
        "difference": str(diff),
        "denominations": payload.denominations,
        "non_cash_totals": {key: str(value) for key, value in payload.non_cash_totals.items()},
        "counted_by": str(current_user.user_id),
        "counted_at": datetime.now(timezone.utc).isoformat(),
        "ledger_fingerprint": ledger_fingerprint(row),
        "approval_status": "pending" if requires_approval else "not_required",
        "approval_history": [],
        "history": history,
    }
    row.count_control_json = json.dumps(control)

    record_audit_event(
        db,
        current_user.company_id,
        current_user.user_id,
        current_user.email,
        "CASH_COUNT_RECORDED",
        "CashSession",
        row.id,
        diff=payload.model_dump(mode="json"),
        category="FINANCE",
    )

    db.commit()

    return {
        "session_id": str(row.id),
        "counted_cash": str(payload.counted_cash),
        "requires_approval": requires_approval,
    }


def approve_cash_difference(
    session_id: UUID, payload: ApproveDifferenceRequest, current_user: AuthenticatedUser, db: Session
):
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
    if not ({"organization:manage", "approvals:manage"} & set(current_user.permissions)):
        raise HTTPException(403, "La diferencia requiere permiso de autorización.")
    control = require_current_count(row)
    if control["version"] != payload.control_version:
        raise HTTPException(409, "El arqueo cambió. Actualice la sesión antes de autorizar.")
    if control["counted_by"] == str(current_user.user_id):
        raise HTTPException(403, "Otra persona debe revisar y autorizar la diferencia.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, current_user, "cash_difference", [control["counted_by"]], "CashSession", row.id)
    if Decimal(control["difference"]) == 0:
        raise HTTPException(409, "Este arqueo no presenta diferencias que autorizar.")
    if not payload.notes or len(payload.notes.strip()) < 5:
        raise HTTPException(422, "Describa el motivo de la aprobación o rechazo.")
    if control["approval_status"] != "pending":
        raise HTTPException(409, "Este arqueo ya fue revisado. Registre otro conteo para una nueva revisión.")
    decision = {
        "approved": payload.approved,
        "reviewed_by": str(current_user.user_id),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "notes": payload.notes.strip(),
    }
    control["approval_status"] = "approved" if payload.approved else "rejected"
    control["approval_history"].append(decision)
    control.pop("is_current", None)
    row.count_control_json = json.dumps(control)
    record_audit_event(db, current_user.company_id, current_user.user_id, current_user.email,
                       "CASH_DIFFERENCE_REVIEWED", "CashSession", row.id,
                       diff={"control_version": control["version"], **decision}, category="FINANCE")
    db.commit()
    return {"session_id": str(row.id), "approved": payload.approved, "control": control}



def close_cash_session(
    session_id: UUID,
    payload: CashSessionCloseRequest,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    record, cached = claim_request(
        db, current_user.company_id, f"cash.close:{session_id}", idempotency_key, payload.model_dump(mode="json")
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
        other = db.scalar(select(CashSessionModel.id).where(CashSessionModel.id == session_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Sesión de caja no encontrada.")

    if row.status != "open":
        raise HTTPException(409, "La sesión de caja ya está cerrada.")

    if row.user_id != current_user.user_id and not ({"organization:manage", "approvals:manage"} & set(current_user.permissions)):
        raise HTTPException(403, "Solo el responsable o un supervisor autorizado puede cerrar esta caja.")

    from salesia.modules.finanzas.application.custodia import require_no_pending_transfers
    require_no_pending_transfers(db, current_user, row.id)
    control = require_current_count(row)
    if Decimal(control["counted_cash"]) != payload.counted_balance:
        raise HTTPException(409, "El cierre debe coincidir con el último conteo registrado.")
    if control["approval_status"] not in {"approved", "not_required"}:
        raise HTTPException(409, "La diferencia de arqueo requiere aprobación antes del cierre.")
    difference = (payload.counted_balance - row.expected_cash).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    row.status = "closed"

    row.actual_cash = payload.counted_balance

    row.difference_cash = difference

    row.closed_at = datetime.now(timezone.utc)

    row.notes = payload.notes

    response = {
        "session_id": str(row.id),
        "currency": row.currency,
        "counted_balance": str(row.actual_cash),
        "expected_balance": str(row.expected_cash),
        "difference": str(difference),
        "status": row.status,
        "closed_by": current_user.email,
        "closed_at": row.closed_at.isoformat(),
        "notes": row.notes,
    }

    record_audit_event(db, current_user.company_id, current_user.user_id, current_user.email,
                       "CASH_SESSION_CLOSED", "CashSession", row.id,
                       diff={"control_version": control["version"], "currency": row.currency,
                             "counted_cash": str(row.actual_cash), "difference": str(difference)}, category="FINANCE")
    complete_request(record, response)

    db.commit()

    return response
