import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel, CashCustodyTransferModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import BranchModel, CashSessionModel, CompanyModel, UserModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number

PENDING = ("sent", "disputed", "return_pending")


class AccountRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=255)
    kind: Literal["safe", "treasury", "branch_fund"]
    branch_id: UUID
    responsible_id: UUID
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    opening_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=20, decimal_places=6)
    is_active: bool = True
    reason: str = Field(min_length=5, max_length=4000)


class TransferRequest(BaseModel):
    source_kind: Literal["cash_session", "custody_account"]
    source_id: UUID
    destination_kind: Literal["cash_session", "custody_account"]
    destination_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    reference: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=5, max_length=4000)


class TransferAction(BaseModel):
    version: int = Field(ge=1)
    action: Literal["receive", "reject", "report_difference", "recall", "confirm_return"]
    counted_amount: Decimal | None = Field(default=None, ge=0, max_digits=20, decimal_places=6)
    reason: str = Field(min_length=5, max_length=4000)


def scoped(db, user, model, identifier, lock=False):
    query = select(model).where(model.company_id == user.company_id, model.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Registro de custodia no encontrado en la empresa activa.")
    return row


def audit(db, user, row, action, data):
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type=type(row).__name__, entity_id=row.id, diff=data, category="FINANCE")


def person(db, user, identifier, active=False):
    query = select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == identifier)
    if active:
        query = query.where(UserModel.is_active.is_(True))
    row = db.scalar(query)
    if active and row is None:
        raise HTTPException(422, "El responsable debe ser un usuario activo de la empresa.")
    return row.full_name or row.email if row else "Responsable histórico"


def account_data(db, user, row):
    branch = scoped(db, user, BranchModel, row.branch_id)
    return {"id": str(row.id), "code": row.code, "name": row.name, "kind": row.kind, "currency": row.currency, "branch_id": str(row.branch_id), "branch_name": branch.name, "responsible_id": str(row.responsible_id), "responsible_name": person(db, user, row.responsible_id), "balance": str(row.balance), "version": row.version, "is_active": row.is_active, "movements": json.loads(row.movements_json)}


def endpoint(db, user, kind, identifier, lock=False, require_available=False):
    model = CashSessionModel if kind == "cash_session" else CashCustodyAccountModel
    row = scoped(db, user, model, identifier, lock)
    if require_available and ((kind == "cash_session" and row.status != "open") or (kind == "custody_account" and not row.is_active)):
        raise HTTPException(409, "El origen y el destino deben estar disponibles para custodiar efectivo.")
    owner = row.user_id if kind == "cash_session" else row.responsible_id
    balance = row.expected_cash if kind == "cash_session" else row.balance
    return row, {"kind": kind, "id": str(row.id), "label": f"Caja {row.terminal_code}" if kind == "cash_session" else f"{row.code} · {row.name}", "branch_id": str(row.branch_id), "responsible_id": str(owner), "responsible_name": person(db, user, owner), "currency": row.currency, "balance": str(balance)}


def transfer_data(db, user, row):
    source_kind = "cash_session" if row.source_session_id else "custody_account"
    destination_kind = "cash_session" if row.destination_session_id else "custody_account"
    _, source = endpoint(db, user, source_kind, row.source_session_id or row.source_account_id)
    _, destination = endpoint(db, user, destination_kind, row.destination_session_id or row.destination_account_id)
    return {"id": str(row.id), "code": row.code, "currency": row.currency, "amount": str(row.amount), "source": source, "destination": destination, "sender_id": str(row.sender_id), "sender_name": person(db, user, row.sender_id), "receiver_id": str(row.receiver_id), "receiver_name": person(db, user, row.receiver_id), "status": row.status, "version": row.version, "reason": row.reason, "reference": row.reference, "created_at": row.created_at.isoformat(), "received_at": row.received_at.isoformat() if row.received_at else None, "returned_at": row.returned_at.isoformat() if row.returned_at else None, "history": json.loads(row.history_json)}


def history(row, user, action, reason, counted_amount=None):
    values = json.loads(row.history_json or "[]")
    values.append({"action": action, "reason": reason, "actor": user.email, "actor_id": str(user.user_id), "at": datetime.now(timezone.utc).isoformat(), "counted_amount": str(counted_amount) if counted_amount is not None else None, "version": row.version})
    row.history_json = json.dumps(values)


def move(db, user, kind, row, delta, transfer, action, reason):
    current = row.expected_cash if kind == "cash_session" else row.balance
    if current + delta < 0:
        raise HTTPException(409, "El efectivo disponible en el origen no cubre el traspaso.")
    movement = {"movement_id": str(uuid4()), "movement_type": "DEPOSIT" if delta > 0 else "WITHDRAWAL", "category": "CUSTODY", "amount": str(abs(delta)), "amount_delta": str(delta), "currency": row.currency, "reason": f"{transfer.code} · {reason}", "transfer_id": str(transfer.id), "transfer_action": action, "balance_after": str(current + delta), "timestamp": datetime.now(timezone.utc).isoformat(), "actor_id": str(user.user_id)}
    if kind == "cash_session":
        row.expected_cash = current + delta
    else:
        row.balance, row.version = current + delta, row.version + 1
    movements = json.loads(row.movements_json or "[]")
    movements.append(movement)
    row.movements_json = json.dumps(movements)
    audit(db, user, row, f"CASH_CUSTODY_{action}", movement)


def pending_for_account(db, user, identifier):
    from salesia.modules.finanzas.application.caja_chica import pending_for_account as pending_petty_cash
    if pending_petty_cash(db, user, identifier):
        return True
    return db.scalar(select(CashCustodyTransferModel.id).where(CashCustodyTransferModel.company_id == user.company_id, CashCustodyTransferModel.status.in_(PENDING), or_(CashCustodyTransferModel.source_account_id == identifier, CashCustodyTransferModel.destination_account_id == identifier)).limit(1)) is not None


def save_account(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"cash_custody.account:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    if not ({"organization:manage", "approvals:manage"} & set(user.permissions)):
        raise HTTPException(403, "Crear o modificar puntos de custodia requiere autorización de administración o aprobaciones.")
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    branch = scoped(db, user, BranchModel, payload.branch_id)
    if not branch.is_active:
        raise HTTPException(422, "La sede debe estar activa.")
    person(db, user, payload.responsible_id, True)
    row = scoped(db, user, CashCustodyAccountModel, identifier, True) if identifier else None
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "El punto de custodia cambió; recarga su ficha.")
    existing = db.scalar(select(CashCustodyAccountModel.id).where(CashCustodyAccountModel.company_id == user.company_id, CashCustodyAccountModel.code == payload.code.upper()))
    if existing and (row is None or existing != row.id):
        raise HTTPException(409, "El código del punto de custodia ya está registrado.")
    if row:
        if payload.opening_balance != 0:
            raise HTTPException(422, "El saldo inicial solo se declara al crear el punto; los fondos posteriores se traspasan con confirmación.")
        if (row.branch_id, row.currency, row.kind) != (payload.branch_id, payload.currency, payload.kind):
            raise HTTPException(409, "La sede, moneda y tipo conservan su historial. Crea otro punto para cambiar esos datos.")
        if (row.responsible_id != payload.responsible_id or not payload.is_active) and (row.balance > 0 or pending_for_account(db, user, row.id)):
            raise HTTPException(409, "El punto tiene efectivo, traspasos o anticipos de caja chica pendientes. Entrega y confirma los fondos antes de cambiar su responsable o desactivarlo.")
    else:
        if not payload.is_active and payload.opening_balance > 0:
            raise HTTPException(422, "Un punto con saldo contado inicial debe estar activo.")
        row = CashCustodyAccountModel(company_id=user.company_id, balance=payload.opening_balance, version=0, branch_id=payload.branch_id, currency=payload.currency, kind=payload.kind, movements_json="[]")
        db.add(row)
    created = row.version == 0
    row.code, row.name, row.responsible_id, row.is_active = payload.code.upper(), payload.name.strip(), payload.responsible_id, payload.is_active
    row.version += 1
    movements = json.loads(row.movements_json)
    movements.append({"movement_id": str(uuid4()), "movement_type": "OPENING_COUNT" if created else "CONFIGURE", "amount_delta": str(row.balance) if created else "0", "balance_after": str(row.balance), "currency": row.currency, "reason": payload.reason, "actor_id": str(user.user_id), "timestamp": datetime.now(timezone.utc).isoformat()})
    row.movements_json = json.dumps(movements)
    db.flush()
    result = account_data(db, user, row)
    audit(db, user, row, "SAVE_CASH_CUSTODY_ACCOUNT", {"reason": payload.reason, "code": row.code, "opening_count": str(row.balance) if created else None, "responsible_id": str(row.responsible_id), "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def create_transfer(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "cash_custody.transfer", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    if payload.source_kind == payload.destination_kind and payload.source_id == payload.destination_id:
        raise HTTPException(422, "El origen y el destino del traspaso deben ser distintos.")
    source_row, source = endpoint(db, user, payload.source_kind, payload.source_id, True, True)
    _, destination = endpoint(db, user, payload.destination_kind, payload.destination_id, True, True)
    if source["responsible_id"] != str(user.user_id):
        raise HTTPException(403, "Solo la persona que custodia los fondos de origen puede registrar su entrega.")
    person(db, user, UUID(destination["responsible_id"]), True)
    if not scoped(db, user, BranchModel, UUID(source["branch_id"])).is_active or not scoped(db, user, BranchModel, UUID(destination["branch_id"])).is_active:
        raise HTTPException(409, "Los nuevos traspasos requieren sedes activas.")
    if source["currency"] != destination["currency"]:
        raise HTTPException(422, "Traspasa efectivo entre puntos de la misma moneda; no se compensan monedas diferentes.")
    if not payload.reference.strip():
        raise HTTPException(422, "Indica la referencia del acta o entrega de efectivo.")
    row = CashCustodyTransferModel(company_id=user.company_id, code=f"TRC-{next_number(db, user.company_id, 'TRC'):08d}", currency=source["currency"], amount=payload.amount, source_session_id=payload.source_id if payload.source_kind == "cash_session" else None, source_account_id=payload.source_id if payload.source_kind == "custody_account" else None, destination_session_id=payload.destination_id if payload.destination_kind == "cash_session" else None, destination_account_id=payload.destination_id if payload.destination_kind == "custody_account" else None, sender_id=user.user_id, receiver_id=UUID(destination["responsible_id"]), status="sent", version=1, reason=payload.reason, reference=payload.reference.strip(), history_json="[]")
    db.add(row)
    db.flush()
    move(db, user, payload.source_kind, source_row, -payload.amount, row, "SEND", payload.reason)
    history(row, user, "SEND", payload.reason)
    db.flush()
    result = transfer_data(db, user, row)
    audit(db, user, row, "SEND_CASH_CUSTODY", {"currency": row.currency, "amount": str(row.amount), "sender_id": str(row.sender_id), "receiver_id": str(row.receiver_id), "reference": row.reference})
    complete_request(record, result)
    db.commit()
    return result


def transfer_action(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"cash_custody.action:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = scoped(db, user, CashCustodyTransferModel, identifier, True)
    if row.version != payload.version or row.status not in PENDING:
        raise HTTPException(409, "El traspaso cambió o ya tiene recepción o devolución confirmada.")
    if payload.action in ("receive", "reject", "report_difference"):
        if row.receiver_id != user.user_id:
            raise HTTPException(403, "Solo la persona destinataria puede confirmar o rechazar la entrega.")
        if row.status not in ("sent", "disputed"):
            raise HTTPException(409, "La devolución está en curso; el origen debe confirmar el retorno físico.")
        if payload.action == "receive":
            if payload.counted_amount != row.amount:
                raise HTTPException(409, "El conteo no coincide con el importe enviado. Registra la diferencia para mantenerla pendiente.")
            kind = "cash_session" if row.destination_session_id else "custody_account"
            destination, details = endpoint(db, user, kind, row.destination_session_id or row.destination_account_id, True, True)
            if details["responsible_id"] != str(row.receiver_id) or details["currency"] != row.currency:
                raise HTTPException(409, "El destino cambió de responsable o moneda; resuelve el retorno al origen.")
            move(db, user, kind, destination, row.amount, row, "RECEIVE", payload.reason)
            row.status, row.received_at = "received", datetime.now(timezone.utc)
        elif payload.action == "report_difference":
            if payload.counted_amount is None or payload.counted_amount == row.amount:
                raise HTTPException(422, "Registra un conteo distinto al importe enviado para abrir una diferencia.")
            row.status = "disputed"
        else:
            row.status = "return_pending"
    else:
        if row.sender_id != user.user_id:
            raise HTTPException(403, "Solo la persona que entregó el efectivo puede solicitar o confirmar su retorno.")
        if payload.action == "confirm_return":
            if row.status != "return_pending" or payload.counted_amount != row.amount:
                raise HTTPException(409, "Solicita el retorno y confirma físicamente el importe completo antes de restaurar el origen.")
            kind = "cash_session" if row.source_session_id else "custody_account"
            source, details = endpoint(db, user, kind, row.source_session_id or row.source_account_id, True, True)
            if details["responsible_id"] != str(row.sender_id) or details["currency"] != row.currency:
                raise HTTPException(409, "El origen cambió de responsable o moneda.")
            move(db, user, kind, source, row.amount, row, "RETURN", payload.reason)
            row.status, row.returned_at = "returned", datetime.now(timezone.utc)
        else:
            row.status = "return_pending"
    row.version += 1
    history(row, user, payload.action.upper(), payload.reason, payload.counted_amount)
    db.flush()
    result = transfer_data(db, user, row)
    audit(db, user, row, "CHANGE_CASH_CUSTODY", {"action": payload.action, "reason": payload.reason, "status": row.status, "counted_amount": str(payload.counted_amount) if payload.counted_amount is not None else None, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def require_no_pending_transfers(db, user, session_id):
    row = db.scalar(select(CashCustodyTransferModel).where(CashCustodyTransferModel.company_id == user.company_id, CashCustodyTransferModel.status.in_(PENDING), or_(CashCustodyTransferModel.source_session_id == session_id, CashCustodyTransferModel.destination_session_id == session_id)).limit(1))
    if row:
        raise HTTPException(409, f"La caja tiene el traspaso {row.code} pendiente de recepción, diferencia o retorno. Resuélvelo antes de cerrar.")


def list_transfers(db, user, status=None, currency=None, limit=25, offset=0):
    query = select(CashCustodyTransferModel).where(CashCustodyTransferModel.company_id == user.company_id)
    if status:
        query = query.where(CashCustodyTransferModel.status == status)
    if currency:
        query = query.where(CashCustodyTransferModel.currency == currency)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(CashCustodyTransferModel.created_at.desc(), CashCustodyTransferModel.id).offset(offset).limit(limit)).all()
    pending = db.execute(select(CashCustodyTransferModel.currency, func.sum(CashCustodyTransferModel.amount)).where(CashCustodyTransferModel.company_id == user.company_id, CashCustodyTransferModel.status.in_(PENDING)).group_by(CashCustodyTransferModel.currency)).all()
    return {"items": [transfer_data(db, user, row) for row in rows], "total_count": total, "in_transit_by_currency": {currency: str(amount) for currency, amount in pending}}


def options(db, user):
    accounts = db.scalars(select(CashCustodyAccountModel).where(CashCustodyAccountModel.company_id == user.company_id).order_by(CashCustodyAccountModel.code)).all()
    sessions = db.scalars(select(CashSessionModel).where(CashSessionModel.company_id == user.company_id, CashSessionModel.status == "open").order_by(CashSessionModel.terminal_code)).all()
    users = db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.is_active.is_(True)).order_by(UserModel.full_name, UserModel.email)).all()
    branches = db.scalars(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.is_active.is_(True)).order_by(BranchModel.name)).all()
    company = db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id))
    endpoints = [endpoint(db, user, "cash_session", row.id)[1] for row in sessions] + [endpoint(db, user, "custody_account", row.id)[1] for row in accounts if row.is_active]
    return {"accounts": [account_data(db, user, row) for row in accounts], "endpoints": endpoints, "people": [{"id": str(row.id), "name": row.full_name or row.email} for row in users], "branches": [{"id": str(row.id), "name": row.name} for row in branches], "current_user_id": str(user.user_id), "can_configure": bool({"organization:manage", "approvals:manage"} & set(user.permissions)), "base_currency": company.base_currency, "business_date": business_date(db, user.company_id)}
