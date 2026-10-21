import calendar
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.acuerdos_cobranza import applications, aware
from salesia.modules.finanzas.infrastructure.models.cuotas_cobranza import ReceivableInstallmentAllocationModel, ReceivableScheduleModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.organizacion.application.calendario_operativo import effective_calendar, roll_day
from salesia.shared.infrastructure.models import SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

SCALE = Decimal("0.000001")


class ScheduleLine(BaseModel):
    due_date: date
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class ScheduleRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    sale_version: int = Field(ge=1)
    items: list[ScheduleLine] = Field(default_factory=list, max_length=120)
    installments_count: int | None = Field(default=None, ge=1, le=120)
    first_due_date: date | None = None
    interval_months: int = Field(default=1, ge=1, le=12)
    adjust_to_operating_calendar: bool = False
    reason: str = Field(min_length=5, max_length=4000)

    @model_validator(mode="after")
    def one_schedule_source(self):
        if self.items and (self.installments_count is not None or self.first_due_date is not None):
            raise ValueError("Usa cuotas manuales o generación automática, sin mezclar ambas modalidades.")
        if not self.items and (self.installments_count is None or self.first_due_date is None):
            raise ValueError("Indica cuotas manuales o la cantidad y primer vencimiento para generarlas.")
        return self


def scoped_sale(db, user, identifier, lock=False):
    query = select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Cuenta por cobrar no encontrada en la empresa activa.")
    return row


def schedule_for_sale(db, user, identifier, lock=False):
    query = select(ReceivableScheduleModel).where(ReceivableScheduleModel.company_id == user.company_id, ReceivableScheduleModel.sale_id == identifier)
    return db.scalar(query.with_for_update() if lock else query)


def schedule_data(db, user, sale, row=None, exclude_application=None):
    row = row or schedule_for_sale(db, user, sale.id)
    if row is None:
        return None
    items = json.loads(row.schedule_json)
    by_id = {item["id"]: item for item in items}
    paid, events = defaultdict(lambda: Decimal("0")), []
    targets = db.scalars(select(ReceivableInstallmentAllocationModel).where(ReceivableInstallmentAllocationModel.company_id == user.company_id, ReceivableInstallmentAllocationModel.schedule_id == row.id, ReceivableInstallmentAllocationModel.schedule_version == row.version).order_by(ReceivableInstallmentAllocationModel.created_at, ReceivableInstallmentAllocationModel.id)).all()
    grouped = defaultdict(list)
    for target in targets:
        grouped[str(target.allocation_id)].append(target)
    receipts = [item for item in applications(db, user.company_id, sale.id, sale.currency) if item["at"] >= aware(row.active_from) and item["id"] != str(exclude_application)]
    unapplied = Decimal("0")
    for receipt in receipts:
        remaining = receipt["amount"]
        explicit = grouped.get(receipt["id"], [])
        allocations = [(str(target.installment_id), target.amount) for target in sorted(explicit, key=lambda value: by_id.get(str(value.installment_id), {}).get("sequence", 0))] if explicit else [(item["id"], remaining) for item in items]
        for identifier, requested in allocations:
            if identifier not in by_id:
                raise HTTPException(409, "El cobro contiene una referencia de cuota que no pertenece al cronograma vigente.")
            amount = min(remaining, requested, max(Decimal("0"), Decimal(by_id[identifier]["amount"]) - paid[identifier]))
            if amount > 0:
                paid[identifier] += amount
                remaining -= amount
                events.append({"application_id": receipt["id"], "payment_id": receipt["payment_id"], "installment_id": identifier, "sequence": by_id[identifier]["sequence"], "amount": str(amount), "at": receipt["at"].isoformat(), "reference": receipt["reference"], "assignment": "explicit" if explicit else "oldest_due"})
        unapplied += remaining
    today = business_date(db, user.company_id)
    lines = []
    for item in items:
        balance = max(Decimal("0"), Decimal(item["amount"]) - paid[item["id"]])
        overdue = max(0, (today - date.fromisoformat(item["due_date"])).days) if balance > 0 else 0
        status = "paid" if balance == 0 else "overdue_partial" if overdue and paid[item["id"]] > 0 else "overdue" if overdue else "partial" if paid[item["id"]] > 0 else "pending"
        lines.append({**item, "paid_amount": str(paid[item["id"]]), "balance": str(balance), "overdue_days": overdue, "status": status})
    remaining = sum((Decimal(item["balance"]) for item in lines), Decimal("0"))
    actual = max(Decimal("0"), sale.total_amount - sale.paid_amount)
    return {"id": str(row.id), "sale_id": str(sale.id), "version": row.version, "sale_version": sale.version, "currency": sale.currency, "active_from": aware(row.active_from).isoformat(), "opening_balance": str(row.opening_balance), "actual_balance": str(actual), "schedule_balance": str(remaining), "balance_difference": str(remaining - actual), "unassigned_applications": str(unapplied), "items": lines, "applications": events, "history": json.loads(row.history_json), "rounding_policy": "Las cuotas automáticas se truncan a seis decimales; la última cuota absorbe exactamente el resto. La suma siempre coincide con la deuda programada. Los reembolsos y reversiones reducen la aplicación de cada abono comenzando por las cuotas de mayor secuencia.", "business_date": today.isoformat()}


def save_schedule(db, user, sale_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"receivable.schedule:{sale_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    sale = scoped_sale(db, user, sale_id, True)
    row = schedule_for_sale(db, user, sale_id, True)
    if sale.version != payload.sale_version or (row.version if row else 0) != payload.version:
        raise HTTPException(409, "La deuda o el cronograma cambiaron. Consulta los saldos actuales antes de guardar.")
    balance = max(Decimal("0"), sale.total_amount - sale.paid_amount)
    if sale.status not in ("confirmed", "paid") or balance <= 0:
        raise HTTPException(409, "La cuenta debe estar vigente y tener saldo pendiente para programar cuotas.")
    if row and not ({"approvals:manage", "organization:manage"} & set(user.permissions)):
        raise HTTPException(403, "Reprogramar cuotas requiere autorización de aprobaciones o administración.")
    items = payload.items
    if not items:
        base = (balance / payload.installments_count).quantize(SCALE, rounding=ROUND_DOWN)
        if base <= 0:
            raise HTTPException(422, "Reduce la cantidad de cuotas: cada cuota debe tener un importe positivo a seis decimales.")
        items = []
        first = payload.first_due_date
        for index in range(payload.installments_count):
            months = first.year * 12 + first.month - 1 + index * payload.interval_months
            year, month = months // 12, months % 12 + 1
            if year > 9999:
                raise HTTPException(422, "El cronograma supera el rango de fechas admitido.")
            due = date(year, month, min(first.day, calendar.monthrange(year, month)[1]))
            amount = base if index < payload.installments_count - 1 else balance - base * (payload.installments_count - 1)
            items.append(ScheduleLine(due_date=due, amount=amount))
    if sum((item.amount for item in items), Decimal("0")) != balance:
        raise HTTPException(422, "La suma de cuotas debe coincidir exactamente con el saldo pendiente actual.")
    if any(items[index].due_date > items[index + 1].due_date for index in range(len(items) - 1)):
        raise HTTPException(422, "Ordena los vencimientos de las cuotas cronológicamente.")
    issued = business_date(db, user.company_id, sale.confirmed_at or sale.created_at)
    if any(item.due_date < issued for item in items):
        raise HTTPException(422, "Ninguna cuota puede vencer antes de la confirmación de la venta.")
    operating_calendar = effective_calendar(db, user.company_id, sale.branch_id) if payload.adjust_to_operating_calendar else None
    scheduled = []
    for index, item in enumerate(items, 1):
        due = roll_day(operating_calendar, item.due_date, operating_calendar["rules"]["payment_roll"]) if operating_calendar else item.due_date
        if due < issued:
            raise HTTPException(422, "El traslado del calendario deja una cuota antes de la confirmación. Revise la fecha pactada o la regla de traslado.")
        scheduled.append({"id": str(uuid4()), "sequence": index, "due_date": due.isoformat(), "original_due_date": item.due_date.isoformat(), "amount": str(item.amount), "calendar_snapshot": operating_calendar})
    if any(scheduled[index]["due_date"] > scheduled[index + 1]["due_date"] for index in range(len(scheduled) - 1)):
        raise HTTPException(422, "El traslado de fechas altera el orden de las cuotas. Revise las fechas pactadas.")
    previous = schedule_data(db, user, sale, row) if row else None
    if row is None:
        row = ReceivableScheduleModel(company_id=user.company_id, sale_id=sale.id, version=0, created_by=user.user_id, history_json="[]")
        db.add(row)
    history = json.loads(row.history_json)
    history.append({"action": "REPROGRAM" if previous else "CREATE", "reason": payload.reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "previous": {key: value for key, value in previous.items() if key != "history"} if previous else None})
    row.version += 1
    row.active_from, row.opening_balance = datetime.now(timezone.utc), balance
    row.schedule_json = json.dumps(scheduled)
    row.history_json = json.dumps(history)
    db.flush()
    result = schedule_data(db, user, sale, row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_RECEIVABLE_SCHEDULE", entity_type="Sale", entity_id=sale.id, diff={"schedule_id": str(row.id), "version": row.version, "reason": payload.reason, "opening_balance": str(balance), "items": result["items"]})
    complete_request(record, result)
    db.commit()
    return result


def assign_installments(db, user, sale, allocation, targets=None, expected_version=None):
    db.flush()
    from salesia.modules.finanzas.application.reservas_credito_cliente import reconcile_sale_reservations
    reconcile_sale_reservations(db, user, sale)
    row = schedule_for_sale(db, user, sale.id, True)
    if row is None:
        if targets or expected_version is not None:
            raise HTTPException(409, "La deuda no tiene un cronograma vigente al que aplicar el cobro.")
        return
    if expected_version is not None and expected_version != row.version:
        raise HTTPException(409, "El cronograma cambió; consulta las cuotas antes de aplicar el cobro.")
    before = schedule_data(db, user, sale, row, allocation.id)
    expected_balance = max(Decimal("0"), sale.total_amount - sale.paid_amount) + allocation.allocated_amount
    if Decimal(before["schedule_balance"]) != expected_balance or Decimal(before["unassigned_applications"]) > 0:
        raise HTTPException(409, "El cronograma no coincide con la deuda actual. Reprograma sus cuotas con autorización antes de registrar un nuevo abono.")
    by_id = {UUID(item["id"]): item for item in before["items"]}
    selected = []
    if targets:
        if len({item.installment_id for item in targets}) != len(targets) or sum((item.amount for item in targets), Decimal("0")) != allocation.allocated_amount:
            raise HTTPException(422, "Distribuye el importe completo del abono entre cuotas distintas.")
        for item in targets:
            if item.installment_id not in by_id or item.amount > Decimal(by_id[item.installment_id]["balance"]):
                raise HTTPException(409, "La cuota no pertenece al cronograma o el abono supera su saldo.")
            selected.append((item.installment_id, item.amount))
    else:
        pending = allocation.allocated_amount
        for item in before["items"]:
            amount = min(pending, Decimal(item["balance"]))
            if amount > 0:
                selected.append((UUID(item["id"]), amount))
                pending -= amount
        if pending > 0:
            raise HTTPException(409, "El abono supera el saldo de las cuotas vigentes.")
    for identifier, amount in selected:
        db.add(ReceivableInstallmentAllocationModel(company_id=user.company_id, allocation_id=allocation.id, schedule_id=row.id, schedule_version=row.version, installment_id=identifier, amount=amount, created_by=user.user_id))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="APPLY_PAYMENT_TO_INSTALLMENTS", entity_type="Sale", entity_id=sale.id, diff={"allocation_id": str(allocation.id), "schedule_id": str(row.id), "schedule_version": row.version, "targets": [{"installment_id": str(identifier), "amount": str(amount)} for identifier, amount in selected], "assignment": "selected" if targets else "oldest_due"})
