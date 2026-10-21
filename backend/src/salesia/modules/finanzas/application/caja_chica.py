import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select

from salesia.modules.finanzas.application.custodia import audit, person, scoped
from salesia.modules.finanzas.application.obligaciones import verify_expense_budget
from salesia.modules.finanzas.infrastructure.models.caja_chica import PettyCashAdvanceModel, PettyCashFundModel
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import CostCenterModel, ExpenseAllocationModel, ExpenseModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number
from salesia.shared.infrastructure.models import BranchModel

CLOSED = ("closed", "cancelled")


class ReasonRequest(BaseModel):
    @field_validator("reason", "purpose", check_fields=False, mode="before")
    @classmethod
    def clean_reason(cls, value):
        return value.strip() if isinstance(value, str) else value


class FundSave(ReasonRequest):
    version: int = Field(default=0, ge=0)
    account_id: UUID
    categories: list[str] = Field(min_length=1, max_length=50)
    max_advance: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    max_receipt: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    max_settlement: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    document_required: bool = True
    is_active: bool = True
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def validate_policy(self):
        self.categories = [value.strip() for value in self.categories]
        if any(len(value) < 2 or len(value) > 128 for value in self.categories):
            raise ValueError("Las categorías deben tener entre 2 y 128 caracteres.")
        if len({value.casefold() for value in self.categories}) != len(self.categories):
            raise ValueError("No repita categorías.")
        if self.max_settlement < self.max_advance or self.max_receipt > self.max_settlement:
            raise ValueError("El límite de rendición debe cubrir el anticipo y cada comprobante.")
        return self


class AdvanceCreate(ReasonRequest):
    fund_id: UUID
    beneficiary_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    due_date: date
    purpose: str = Field(min_length=5, max_length=2000)


class ReceiptInput(BaseModel):
    @field_validator("category", "title", "issuer", "document_reference", "evidence", mode="before")
    @classmethod
    def clean_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    category: str = Field(min_length=2, max_length=128)
    title: str = Field(min_length=3, max_length=255)
    issuer: str = Field(min_length=2, max_length=40)
    document_reference: str = Field(default="", max_length=60)
    evidence: str = Field(min_length=5, max_length=2000)
    expense_date: date
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    cost_center_id: UUID


class AdvanceAction(ReasonRequest):
    version: int = Field(ge=1)
    action: Literal["issue", "accept", "submit", "approve", "reject", "cancel", "recall", "confirm_return", "pay_reimbursement", "accept_reimbursement"]
    reason: str = Field(min_length=5, max_length=2000)
    counted_amount: Decimal | None = Field(default=None, ge=0, max_digits=20, decimal_places=6)
    receipts: list[ReceiptInput] = Field(default_factory=list, max_length=100)


def pending_for_account(db, user, account_id):
    return db.scalar(select(PettyCashAdvanceModel.id).join(PettyCashFundModel, PettyCashFundModel.id == PettyCashAdvanceModel.fund_id).where(PettyCashAdvanceModel.company_id == user.company_id, PettyCashFundModel.company_id == user.company_id, PettyCashFundModel.account_id == account_id, PettyCashAdvanceModel.status.notin_(CLOSED)).limit(1)) is not None


def account_for(db, user, fund, lock=False):
    return scoped(db, user, CashCustodyAccountModel, fund.account_id, lock)


def fund_data(db, user, row):
    account = account_for(db, user, row)
    return {"id": str(row.id), "account_id": str(account.id), "name": account.name, "code": account.code, "currency": account.currency, "balance": str(account.balance), "responsible_id": str(account.responsible_id), "responsible_name": person(db, user, account.responsible_id), "version": row.version, "is_active": row.is_active, "policy": json.loads(row.policy_json), "history": json.loads(row.history_json)}


def advance_data(db, user, row):
    fund = scoped(db, user, PettyCashFundModel, row.fund_id)
    account = account_for(db, user, fund)
    settlement = json.loads(row.settlement_json or "{}")
    return {"id": str(row.id), "code": row.code, "fund_id": str(fund.id), "fund_name": account.name, "responsible_id": str(account.responsible_id), "beneficiary_id": str(row.beneficiary_id), "beneficiary_name": person(db, user, row.beneficiary_id), "currency": row.currency, "amount": str(row.amount), "due_date": row.due_date.isoformat(), "is_overdue": row.status not in CLOSED and row.due_date < business_date(db, user.company_id), "purpose": row.purpose, "status": row.status, "version": row.version, "policy": json.loads(row.policy_json), "settlement": settlement, "history": json.loads(row.history_json)}


def save_fund(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"petty_cash.fund:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    if not ({"organization:manage", "approvals:manage"} & set(user.permissions)):
        raise HTTPException(403, "Configurar un fondo requiere autorización administrativa.")
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    account = scoped(db, user, CashCustodyAccountModel, payload.account_id, True)
    if account.kind != "branch_fund" or not account.is_active:
        raise HTTPException(422, "El fondo debe usar un punto de custodia activo de tipo fondo de sede.")
    row = scoped(db, user, PettyCashFundModel, identifier, True) if identifier else None
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "El fondo cambió. Actualice antes de guardar.")
    if row and row.account_id != account.id:
        raise HTTPException(409, "El fondo conserva su punto de custodia original.")
    existing = db.scalar(select(PettyCashFundModel.id).where(PettyCashFundModel.company_id == user.company_id, PettyCashFundModel.account_id == account.id))
    if existing and (row is None or existing != row.id):
        raise HTTPException(409, "Este punto de custodia ya tiene un fondo configurado.")
    if row is None:
        row = PettyCashFundModel(company_id=user.company_id, account_id=account.id, version=0, history_json="[]")
        db.add(row)
    policy = payload.model_dump(mode="json", exclude={"version", "account_id", "is_active", "reason"})
    events = json.loads(row.history_json)
    events.append({"version": row.version + 1, "policy": policy, "is_active": payload.is_active, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": payload.reason})
    row.policy_json, row.history_json, row.is_active, row.version = json.dumps(policy), json.dumps(events), payload.is_active, row.version + 1
    db.flush()
    result = fund_data(db, user, row)
    audit(db, user, row, "SAVE_PETTY_CASH_FUND", {"version": row.version, "reason": payload.reason})
    complete_request(record, result)
    db.commit()
    return result


def create_advance(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "petty_cash.advance", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    today = business_date(db, user.company_id)
    require_open_period(db, user.company_id, today)
    fund = scoped(db, user, PettyCashFundModel, payload.fund_id, True)
    account = account_for(db, user, fund, True)
    policy = json.loads(fund.policy_json)
    if not scoped(db, user, BranchModel, account.branch_id).is_active:
        raise HTTPException(409, "La sede del fondo debe estar activa para solicitar anticipos.")
    if not fund.is_active or not account.is_active:
        raise HTTPException(409, "El fondo está inactivo para nuevos anticipos.")
    if user.user_id not in (payload.beneficiary_id, account.responsible_id):
        raise HTTPException(403, "La solicitud corresponde al beneficiario o al custodio del fondo.")
    person(db, user, payload.beneficiary_id, True)
    if payload.amount > Decimal(policy["max_advance"]) or payload.due_date < today or (payload.due_date - today).days > 365:
        raise HTTPException(422, "Revise el límite de anticipo y el vencimiento, entre hoy y los próximos 365 días.")
    pending = db.scalar(select(PettyCashAdvanceModel.id).where(PettyCashAdvanceModel.company_id == user.company_id, PettyCashAdvanceModel.fund_id == fund.id, PettyCashAdvanceModel.beneficiary_id == payload.beneficiary_id, PettyCashAdvanceModel.status.notin_(CLOSED)).limit(1))
    if pending:
        raise HTTPException(409, "El beneficiario debe concluir su anticipo anterior de este fondo.")
    row = PettyCashAdvanceModel(company_id=user.company_id, fund_id=fund.id, beneficiary_id=payload.beneficiary_id, code=f"CCH-{next_number(db, user.company_id, 'CCH'):08d}", currency=account.currency, amount=payload.amount, due_date=payload.due_date, purpose=payload.purpose.strip(), policy_json=fund.policy_json, status="requested", version=1, settlement_json="{}", history_json="[]")
    db.add(row)
    db.flush()
    add_history(row, user, "REQUEST", payload.purpose)
    result = advance_data(db, user, row)
    audit(db, user, row, "REQUEST_PETTY_CASH_ADVANCE", {"amount": str(row.amount), "currency": row.currency, "beneficiary_id": str(row.beneficiary_id)})
    complete_request(record, result)
    db.commit()
    return result


def add_history(row, user, action, reason, counted=None):
    events = json.loads(row.history_json or "[]")
    events.append({"version": row.version, "action": action, "reason": reason, "actor_id": str(user.user_id), "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "counted_amount": str(counted) if counted is not None else None})
    row.history_json = json.dumps(events)


def move_fund(db, user, account, row, delta, action, reason):
    if not account.is_active or account.currency != row.currency:
        raise HTTPException(409, "El punto de custodia debe estar activo y conservar la moneda del anticipo.")
    if account.balance + delta < 0:
        raise HTTPException(409, "El fondo no tiene efectivo suficiente. Repóngalo mediante un traspaso confirmado.")
    account.balance, account.version = account.balance + delta, account.version + 1
    events = json.loads(account.movements_json or "[]")
    events.append({"movement_id": str(uuid4()), "movement_type": "WITHDRAWAL" if delta < 0 else "DEPOSIT", "category": "PETTY_CASH", "amount_delta": str(delta), "balance_after": str(account.balance), "currency": row.currency, "advance_id": str(row.id), "reason": f"{row.code} · {reason}", "timestamp": datetime.now(timezone.utc).isoformat(), "actor_id": str(user.user_id)})
    account.movements_json = json.dumps(events)
    audit(db, user, account, action, events[-1])


def validate_receipts(db, user, row, receipts):
    policy = json.loads(row.policy_json)
    state = json.loads(row.settlement_json or "{}")
    issued_on = date.fromisoformat(state["issued_on"])
    today = business_date(db, user.company_id)
    total = sum((item.amount for item in receipts), Decimal("0"))
    if total > Decimal(policy["max_settlement"]):
        raise HTTPException(422, "La rendición supera el límite total de gastos del fondo.")
    seen = set()
    result = []
    for item in receipts:
        if item.category not in policy["categories"] or item.amount > Decimal(policy["max_receipt"]):
            raise HTTPException(422, "La categoría o el importe del comprobante no está permitido por la política del anticipo.")
        if item.expense_date < issued_on or item.expense_date > today:
            raise HTTPException(422, "Los gastos deben corresponder a fechas entre la entrega y hoy.")
        require_open_period(db, user.company_id, item.expense_date, ["expenses", "treasury"])
        scoped(db, user, CostCenterModel, item.cost_center_id)
        reference = item.document_reference.strip().upper()
        issuer = item.issuer.strip().upper()
        if not issuer or (policy["document_required"] and not reference):
            raise HTTPException(422, "La política exige identificar al emisor y al comprobante.")
        document_key = f"{issuer}:{reference}" if reference else None
        if document_key:
            if document_key in seen:
                raise HTTPException(422, "El comprobante está repetido en la rendición.")
            seen.add(document_key)
            duplicate = db.scalar(select(ExpenseModel.id).where(ExpenseModel.company_id == user.company_id, func.upper(func.trim(ExpenseModel.document_number)) == document_key, ExpenseModel.status.notin_(("cancelled", "rejected"))).limit(1))
            if duplicate:
                raise HTTPException(409, "El comprobante ya está registrado como gasto.")
        result.append({**item.model_dump(mode="json"), "issuer": issuer, "document_reference": reference, "document_key": document_key})
    return result, total


def act(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"petty_cash.action:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    today = business_date(db, user.company_id)
    require_open_period(db, user.company_id, today)
    row = scoped(db, user, PettyCashAdvanceModel, identifier, True)
    fund = scoped(db, user, PettyCashFundModel, row.fund_id, True)
    account = account_for(db, user, fund, True)
    if row.version != payload.version or row.status in CLOSED:
        raise HTTPException(409, "El anticipo cambió o ya está concluido.")
    state = json.loads(row.settlement_json or "{}")
    action = payload.action
    beneficiary_actions = {"accept", "submit", "accept_reimbursement"}
    custodian_actions = {"issue", "recall", "confirm_return", "pay_reimbursement"}
    if action in beneficiary_actions and row.beneficiary_id != user.user_id:
        raise HTTPException(403, "Esta acción corresponde al beneficiario del anticipo.")
    if action in custodian_actions and account.responsible_id != user.user_id:
        raise HTTPException(403, "Esta acción corresponde al custodio del fondo.")
    if action in {"approve", "reject"}:
        if not ({"organization:manage", "approvals:manage"} & set(user.permissions)) or row.beneficiary_id == user.user_id:
            raise HTTPException(403, "La rendición requiere revisión independiente por una persona autorizada.")
        from salesia.modules.seguridad.application.separacion_funciones import enforce
        enforce(db, user, "petty_cash", [row.beneficiary_id], "PettyCashAdvance", row.id)
    if action == "issue":
        require_status(row, "requested")
        if not scoped(db, user, BranchModel, account.branch_id).is_active:
            raise HTTPException(409, "La sede del fondo debe estar activa para entregar anticipos.")
        if not fund.is_active or row.due_date < today:
            raise HTTPException(409, "El fondo está inactivo o venció la solicitud. Cancele y registre una solicitud vigente.")
        person(db, user, row.beneficiary_id, True)
        require_count(payload, row.amount)
        move_fund(db, user, account, row, -row.amount, "ISSUE_PETTY_CASH", payload.reason)
        state["issued_on"] = today.isoformat()
        row.status = "issued"
    elif action == "accept":
        require_status(row, "issued")
        require_count(payload, row.amount)
        row.status = "active"
        state["accepted_at"] = datetime.now(timezone.utc).isoformat()
    elif action == "submit":
        require_status(row, "active")
        receipts, total = validate_receipts(db, user, row, payload.receipts)
        revisions = state.get("revisions", [])
        if "receipts" in state:
            revisions.append({"receipts": state["receipts"], "total": state["total"], "submitted_at": state["submitted_at"]})
        state.update({"receipts": receipts, "total": str(total), "submitted_at": datetime.now(timezone.utc).isoformat(), "revisions": revisions})
        row.status = "submitted"
    elif action == "reject":
        require_status(row, "submitted")
        row.status = "active"
    elif action == "approve":
        require_status(row, "submitted")
        receipts, total = validate_receipts(db, user, row, [ReceiptInput.model_validate(item) for item in state["receipts"]])
        expense_ids = []
        for item in receipts:
            expense = ExpenseModel(company_id=user.company_id, petty_cash_advance_id=row.id, title=item["title"], category=item["category"], document_number=item["document_key"], expense_date=date.fromisoformat(item["expense_date"]), currency=row.currency, amount=Decimal(item["amount"]), status="pending", version=1, created_by=row.beneficiary_id, approved_by=user.user_id, notes=f"Rendición {row.code}. {item['evidence']}")
            db.add(expense)
            db.flush()
            db.add(ExpenseAllocationModel(company_id=user.company_id, expense_id=expense.id, cost_center_id=UUID(item["cost_center_id"]), amount=expense.amount))
            db.flush()
            verify_expense_budget(db, user, expense)
            expense.status = "approved"
            db.flush()
            expense_ids.append(str(expense.id))
            audit(db, user, expense, "APPROVE_PETTY_CASH_EXPENSE", {"advance_id": str(row.id), "amount": str(expense.amount), "currency": row.currency})
        difference = row.amount - total
        state.update({"expense_ids": expense_ids, "total": str(total), "difference": str(difference), "approved_by": str(user.user_id), "approved_at": datetime.now(timezone.utc).isoformat()})
        row.status = "return_due" if difference > 0 else "reimbursement_due" if difference < 0 else "closed"
    elif action == "cancel":
        require_status(row, "requested")
        if user.user_id not in (row.beneficiary_id, account.responsible_id):
            raise HTTPException(403, "Solo el beneficiario o custodio puede cancelar la solicitud.")
        row.status = "cancelled"
    elif action == "recall":
        if row.status not in ("issued", "active"):
            raise HTTPException(409, "Solo se solicita el retorno íntegro de anticipos aún sin rendición en revisión.")
        state["difference"] = str(row.amount)
        state["recall"] = True
        row.status = "return_due"
    elif action == "confirm_return":
        require_status(row, "return_due")
        amount = Decimal(state["difference"])
        require_count(payload, amount)
        move_fund(db, user, account, row, amount, "RETURN_PETTY_CASH", payload.reason)
        row.status = "closed"
    elif action == "pay_reimbursement":
        require_status(row, "reimbursement_due")
        amount = -Decimal(state["difference"])
        require_count(payload, amount)
        move_fund(db, user, account, row, -amount, "REIMBURSE_PETTY_CASH", payload.reason)
        row.status = "reimbursement_sent"
    elif action == "accept_reimbursement":
        require_status(row, "reimbursement_sent")
        require_count(payload, -Decimal(state["difference"]))
        row.status = "closed"
    row.version += 1
    row.settlement_json = json.dumps(state)
    add_history(row, user, action.upper(), payload.reason, payload.counted_amount)
    db.flush()
    result = advance_data(db, user, row)
    audit(db, user, row, "CHANGE_PETTY_CASH_ADVANCE", {"action": action, "status": row.status, "version": row.version, "reason": payload.reason})
    complete_request(record, result)
    db.commit()
    return result


def require_status(row, expected):
    if row.status != expected:
        raise HTTPException(409, "El estado del anticipo no admite esta acción.")


def require_count(payload, expected):
    if payload.counted_amount != expected:
        raise HTTPException(409, "El conteo físico debe coincidir con el importe de esta entrega o devolución.")


def list_advances(db, user, status=None, fund_id=None, limit=25, offset=0):
    query = select(PettyCashAdvanceModel).where(PettyCashAdvanceModel.company_id == user.company_id)
    if status:
        query = query.where(PettyCashAdvanceModel.status == status)
    if fund_id:
        query = query.where(PettyCashAdvanceModel.fund_id == fund_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(PettyCashAdvanceModel.created_at.desc(), PettyCashAdvanceModel.id).limit(limit).offset(offset)).all()
    return {"items": [advance_data(db, user, row) for row in rows], "total_count": total}


def options(db, user):
    from salesia.modules.finanzas.application.custodia import options as custody_options
    available = custody_options(db, user)
    funds = db.scalars(select(PettyCashFundModel).where(PettyCashFundModel.company_id == user.company_id).order_by(PettyCashFundModel.created_at.desc())).all()
    centers = db.scalars(select(CostCenterModel).where(CostCenterModel.company_id == user.company_id).order_by(CostCenterModel.name)).all()
    return {"funds": [fund_data(db, user, row) for row in funds], "accounts": [row for row in available["accounts"] if row["kind"] == "branch_fund"], "people": available["people"], "current_user_id": str(user.user_id), "can_review": bool({"organization:manage", "approvals:manage"} & set(user.permissions)), "cost_centers": [{"id": str(row.id), "name": row.name} for row in centers], "business_date": business_date(db, user.company_id)}
