import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.finanzas.application.cuotas_cobranza import schedule_data
from salesia.modules.finanzas.infrastructure.models.caja_chica import PettyCashAdvanceModel, PettyCashFundModel
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel, CashCustodyTransferModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import ExpenseModel, PayableInstallmentModel, PayableModel
from salesia.modules.inventario.infrastructure_models import PurchaseInvoiceMatch, SupplyDocument
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import CashSessionModel, CompanyModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

SCALE = Decimal("0.000001")
KIND = "cash_forecast"


class SourceOverride(BaseModel):
    source_key: str = Field(min_length=1, max_length=160)
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    included: bool
    due_date: date | None = None
    point_key: str | None = Field(default=None, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=6)


class ManualEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=3, max_length=255)
    direction: Literal["in", "out", "transfer"]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    due_date: date
    point_key: str | None = Field(default=None, max_length=80)
    destination_key: str | None = Field(default=None, max_length=80)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_transfer(self):
        if self.direction == "transfer":
            if not self.point_key or not self.destination_key or self.point_key == self.destination_key:
                raise ValueError("La simulación de traspaso requiere dos puntos de custodia distintos.")
        elif self.destination_key:
            raise ValueError("Solo un traspaso tiene un segundo punto de custodia.")
        return self


class ForecastConfig(BaseModel):
    horizon_days: int = Field(default=30, ge=1, le=365)
    overrides: list[SourceOverride] = Field(default_factory=list, max_length=2000)
    manual_events: list[ManualEvent] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def distinct_items(self):
        if len({row.source_key for row in self.overrides}) != len(self.overrides):
            raise ValueError("Cada documento admite una sola regla en el escenario.")
        if len({row.id for row in self.manual_events}) != len(self.manual_events):
            raise ValueError("Las operaciones manuales deben tener identificadores distintos.")
        return self


class ScenarioSave(ForecastConfig):
    name: str = Field(min_length=3, max_length=128)
    version: int = Field(default=0, ge=0)
    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("name", "reason", mode="before")
    @classmethod
    def clean_text(cls, value):
        return value.strip() if isinstance(value, str) else value


def bounded(db, statement):
    rows = db.scalars(statement.limit(5001)).all()
    if len(rows) > 5000:
        raise HTTPException(422, "La previsión supera 5000 registros por origen. Se requiere ampliar el procesamiento antes de calcularla completa.")
    return rows


def money(value):
    return str(Decimal(value).quantize(SCALE))


def local_day(db, user, value):
    return business_date(db, user.company_id, value)


def sources(db, user):
    db.scalar(select(CompanyModel.id).where(CompanyModel.id == user.company_id).with_for_update())
    today = business_date(db, user.company_id)
    points, entries, warnings = {}, [], []
    sessions = bounded(db, select(CashSessionModel).where(CashSessionModel.company_id == user.company_id, CashSessionModel.status == "open").order_by(CashSessionModel.id))
    accounts = bounded(db, select(CashCustodyAccountModel).where(CashCustodyAccountModel.company_id == user.company_id).order_by(CashCustodyAccountModel.id))
    for kind, rows in (("cash_session", sessions), ("custody_account", accounts)):
        for row in rows:
            balance = row.expected_cash if kind == "cash_session" else row.balance
            active = row.status == "open" if kind == "cash_session" else row.is_active
            if not active and balance == 0:
                continue
            key = f"{kind}:{row.id}"
            points[key] = {"key": key, "name": f"Caja {row.terminal_code}" if kind == "cash_session" else f"{row.code} · {row.name}", "currency": row.currency, "opening_balance": money(balance), "is_active": active}

    def add(key, title, direction, currency, amount, due, kind, included=True, point=None, note="", version=None, fixed=False):
        amount = Decimal(amount).quantize(SCALE)
        if amount <= 0:
            return
        item = {"key": key, "title": title, "direction": direction, "currency": currency, "amount": money(amount), "original_due_date": due.isoformat(), "kind": kind, "default_included": included, "point_key": point, "fixed_point": fixed, "note": note, "source_version": version}
        item["fingerprint"] = hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        entries.append(item)

    sales = bounded(db, select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.status.in_(("confirmed", "paid")), SaleModel.total_amount > SaleModel.paid_amount).order_by(SaleModel.id))
    for sale in sales:
        label = f"Cobro {sale.series}-{sale.number:06d}"
        scheduled = schedule_data(db, user, sale)
        if scheduled and Decimal(scheduled["balance_difference"]) == 0 and Decimal(scheduled["unassigned_applications"]) == 0:
            for item in scheduled["items"]:
                add(f"receivable:{sale.id}:{item['id']}", f"{label} · cuota {item['sequence']}", "in", sale.currency, item["balance"], date.fromisoformat(item["due_date"]), "receivable", version=f"{sale.version}:{scheduled['version']}")
        else:
            due = sale.due_at or (sale.confirmed_at or sale.created_at) + timedelta(days=sale.payment_terms_days)
            add(f"receivable:{sale.id}", label, "in", sale.currency, sale.total_amount - sale.paid_amount, local_day(db, user, due), "receivable", note="Cronograma desajustado: se utiliza el saldo total al vencimiento de la venta." if scheduled else "", version=sale.version)
            if scheduled:
                warnings.append(f"{label}: revise el cronograma; se proyecta el saldo real sin duplicar cuotas.")

    payables = bounded(db, select(PayableModel).where(PayableModel.company_id == user.company_id, PayableModel.status != "cancelled").order_by(PayableModel.id))
    installments = bounded(db, select(PayableInstallmentModel).where(PayableInstallmentModel.company_id == user.company_id).order_by(PayableInstallmentModel.id))
    by_payable = defaultdict(list)
    for item in installments:
        by_payable[item.payable_id].append(item)
    booked_by_order = defaultdict(lambda: Decimal("0"))
    linked_matches = set()
    for payable in payables:
        if payable.purchase_order_id:
            booked_by_order[payable.purchase_order_id] += payable.amount
        if payable.invoice_match_id:
            linked_matches.add(payable.invoice_match_id)
        balance = payable.amount - payable.paid_amount
        parts = by_payable[payable.id]
        if parts and sum((row.amount - row.paid_amount for row in parts), Decimal("0")) == balance:
            for item in parts:
                add(f"payable:{payable.id}:{item.id}", f"Pago {payable.document_number} · cuota {item.sequence}", "out", payable.currency, item.amount - item.paid_amount, item.due_date, "payable", version=payable.version)
        else:
            add(f"payable:{payable.id}", f"Pago {payable.document_number}", "out", payable.currency, balance, payable.due_date, "payable", version=payable.version)
            if parts and balance > 0:
                warnings.append(f"Obligación {payable.document_number}: revise sus cuotas; se proyecta el saldo real.")

    matches = bounded(db, select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.status.in_(("MATCHED", "APPROVED_OVERRIDE"))).order_by(PurchaseInvoiceMatch.id))
    unposted_by_order = defaultdict(list)
    for match in matches:
        if match.id not in linked_matches:
            unposted_by_order[match.purchase_order_id].append(match)
    orders = bounded(db, select(SupplyDocument).options(selectinload(SupplyDocument.lines)).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "PURCHASE_ORDER", SupplyDocument.supplier_claim_id.is_(None), SupplyDocument.status.notin_(("draft", "submitted", "cancelled"))).order_by(SupplyDocument.id))
    for order in orders:
        details = json.loads(order.details_json or "{}")
        if details.get("no_additional_debt"):
            continue
        currency = details.get("currency")
        if not currency:
            warnings.append(f"Compra {order.id}: falta moneda histórica y se excluye su estimación.")
            continue
        try:
            due = date.fromisoformat(details["delivery_date"]) if details.get("delivery_date") else local_day(db, user, order.created_at)
            due += timedelta(days=int(details.get("payment_terms_days", 30)))
        except (ValueError, TypeError, OverflowError):
            warnings.append(f"Compra {order.id}: faltan condiciones de fecha válidas; revise el documento.")
            continue
        matched_amount = Decimal("0")
        for match in unposted_by_order[order.id]:
            matched_amount += match.invoice_amount
            add(f"invoice_match:{match.id}", f"Factura conciliada {match.invoice_number} sin obligación", "out", currency, match.invoice_amount, due, "purchase_invoice", included=False, note="Estimación pendiente de registrar la obligación y verificar el vencimiento.", version=f"{order.version}:{match.version}")
        commercial = {item["product_id"]: item for item in details.get("commercial_lines", [])}
        total = sum((max(Decimal("0"), line.quantity - line.cancelled_quantity) * line.unit_cost * (1 + Decimal(str(commercial.get(str(line.product_id), {}).get("tax_rate", "0")))) for line in order.lines if line.company_id == user.company_id), Decimal("0"))
        remainder = max(Decimal("0"), total - booked_by_order[order.id] - matched_amount)
        add(f"purchase_order:{order.id}", f"Compra {str(order.id)[:8].upper()} sin obligación", "out", currency, remainder, due, "purchase_estimate", included=False, note="Estimación de cantidades vigentes y sus impuestos registrados, descontando facturas y obligaciones vinculadas. No incorpora fletes ni ajustes posteriores.", version=order.version)

    expenses = bounded(db, select(ExpenseModel).where(ExpenseModel.company_id == user.company_id, ExpenseModel.status == "approved", ExpenseModel.petty_cash_advance_id.is_(None)).order_by(ExpenseModel.id))
    for expense in expenses:
        add(f"expense:{expense.id}", f"Gasto {expense.title}", "out", expense.currency, expense.amount, expense.expense_date, "expense", included=False, note="El gasto aprobado no dispone todavía de seguimiento de pago. Inclúyalo solo si sigue pendiente de desembolso.", version=expense.version)

    funds = {row.id: row for row in bounded(db, select(PettyCashFundModel).where(PettyCashFundModel.company_id == user.company_id).order_by(PettyCashFundModel.id))}
    advances = bounded(db, select(PettyCashAdvanceModel).where(PettyCashAdvanceModel.company_id == user.company_id, PettyCashAdvanceModel.status.in_(("requested", "return_due", "reimbursement_due"))).order_by(PettyCashAdvanceModel.id))
    for advance in advances:
        fund = funds.get(advance.fund_id)
        if not fund:
            continue
        point = f"custody_account:{fund.account_id}"
        state = json.loads(advance.settlement_json or "{}")
        if advance.status == "requested":
            amount, direction, due, included, note = advance.amount, "out", today, False, "Solicitud aún no entregada; confirme si espera desembolsarla."
        else:
            difference = Decimal(state["difference"])
            amount, direction, due, included, note = abs(difference), "in" if difference > 0 else "out", advance.due_date, True, "Retorno o reembolso aprobado pendiente de confirmar físicamente."
        add(f"petty_cash:{advance.id}", f"Caja chica {advance.code}", direction, advance.currency, amount, due, "petty_cash", included=included, point=point, note=note, version=advance.version, fixed=True)

    transfers = bounded(db, select(CashCustodyTransferModel).where(CashCustodyTransferModel.company_id == user.company_id, CashCustodyTransferModel.status.in_(("sent", "disputed", "return_pending"))).order_by(CashCustodyTransferModel.id))
    transit = defaultdict(lambda: Decimal("0"))
    for transfer in transfers:
        transit[transfer.currency] += transfer.amount
        returning = transfer.status == "return_pending"
        session_id = transfer.source_session_id if returning else transfer.destination_session_id
        account_id = transfer.source_account_id if returning else transfer.destination_account_id
        point = f"cash_session:{session_id}" if session_id else f"custody_account:{account_id}"
        add(f"custody_transfer:{transfer.id}", f"{'Retorno' if returning else 'Recepción'} {transfer.code}", "in", transfer.currency, transfer.amount, today, "cash_in_transit", included=False, point=point, note="El efectivo ya salió del origen y no forma parte del saldo disponible. Active su ingreso solo como hipótesis de recepción o retorno.", version=transfer.version, fixed=True)
    if len(entries) > 15000:
        raise HTTPException(422, "La previsión supera 15000 partidas y requiere ampliar el procesamiento para mostrarla completa.")
    return today, points, entries, warnings, {currency: money(amount) for currency, amount in transit.items()}


def build_forecast(db, user, config, strict=False):
    today, points, entries, warnings, transit = sources(db, user)
    end = today + timedelta(days=config.horizon_days - 1)
    by_key = {item["key"]: item for item in entries}
    overrides = {item.source_key: item for item in config.overrides}
    stale = []
    for key, rule in overrides.items():
        source = by_key.get(key)
        if source is None or source["fingerprint"] != rule.fingerprint:
            stale.append(key)
    if stale and strict:
        raise HTTPException(409, "Hay documentos modificados o desaparecidos. Actualice sus reglas antes de guardar el escenario.")
    if stale:
        warnings.append("Las reglas de documentos modificados se excluyen hasta que vuelva a confirmar sus datos: " + ", ".join(stale))

    def validate_point(key, currency):
        if not key:
            return
        point = points.get(key)
        if point is None or not point["is_active"] or point["currency"] != currency:
            raise HTTPException(409, "La caja o el punto de custodia ya no está activo o no coincide con la moneda de la partida.")

    projected = []
    for source in entries:
        rule = overrides.get(source["key"])
        included = source["default_included"]
        amount, due, point = Decimal(source["amount"]), date.fromisoformat(source["original_due_date"]), source["point_key"]
        invalid_rule = source["key"] in stale
        if rule and not invalid_rule:
            included, due = rule.included, rule.due_date or due
            if rule.amount is not None:
                if rule.amount > amount:
                    raise HTTPException(422, "Una hipótesis vinculada no puede superar el saldo del documento. Use una partida manual para una entrada o salida adicional.")
                amount = rule.amount
            if source["fixed_point"] and rule.point_key and rule.point_key != point:
                raise HTTPException(422, "El fondo o destino de este compromiso está fijado por su documento.")
            point = rule.point_key or point
        if invalid_rule:
            included = False
        if included and point:
            try:
                validate_point(point, source["currency"])
            except HTTPException:
                if strict:
                    raise
                included, invalid_rule = False, True
                warnings.append(f"{source['title']}: su punto de custodia requiere una nueva asignación.")
        effective = max(today, due)
        in_horizon = effective <= end
        item = {**source, "source_amount": source["amount"], "amount": money(amount), "due_date": effective.isoformat(), "point_key": point, "included": included, "in_horizon": in_horizon, "is_overdue": due < today, "needs_review": invalid_rule}
        projected.append(item)

    for manual in config.manual_events:
        if manual.due_date < today:
            if strict:
                raise HTTPException(422, "Reprograme las hipótesis manuales cuya fecha ya pasó.")
            warnings.append(f"Hipótesis {manual.title}: su fecha ya pasó y se excluye hasta reprogramarla.")
            continue
        try:
            validate_point(manual.point_key, manual.currency)
            validate_point(manual.destination_key, manual.currency)
        except HTTPException:
            if strict:
                raise
            warnings.append(f"Hipótesis {manual.title}: su punto de custodia ya no está disponible y se excluye hasta corregirlo.")
            continue
        legs = [("out", manual.point_key), ("in", manual.destination_key)] if manual.direction == "transfer" else [(manual.direction, manual.point_key)]
        for index, (direction, point) in enumerate(legs):
            projected.append({"key": f"manual:{manual.id}:{index}", "title": manual.title, "kind": "manual_transfer" if manual.direction == "transfer" else "manual", "direction": direction, "currency": manual.currency, "amount": money(manual.amount), "due_date": manual.due_date.isoformat(), "original_due_date": manual.due_date.isoformat(), "point_key": point, "included": True, "default_included": True, "in_horizon": manual.due_date <= end, "is_overdue": False, "needs_review": False, "fixed_point": manual.direction == "transfer", "note": "Hipótesis manual del escenario; no registra cobros, pagos ni traspasos reales.", "fingerprint": None})

    opening = defaultdict(lambda: Decimal("0"))
    groups = {key: {"key": key, "name": value["name"], "currency": value["currency"], "opening_balance": value["opening_balance"]} for key, value in points.items()}
    for point in points.values():
        opening[point["currency"]] += Decimal(point["opening_balance"])
    daily = defaultdict(lambda: {"in": Decimal("0"), "out": Decimal("0"), "keys": []})
    for item in projected:
        if not item["included"] or not item["in_horizon"]:
            continue
        amount = Decimal(item["amount"])
        day = item["due_date"]
        if item["kind"] != "manual_transfer":
            daily[(f"currency:{item['currency']}", day)][item["direction"]] += amount
            daily[(f"currency:{item['currency']}", day)]["keys"].append(item["key"])
        group = item["point_key"] or f"unassigned:{item['currency']}"
        if group not in groups:
            groups[group] = {"key": group, "name": f"Sin asignar · {item['currency']}", "currency": item["currency"], "opening_balance": "0.000000"}
        daily[(group, day)][item["direction"]] += amount
        daily[(group, day)]["keys"].append(item["key"])
        opening[item["currency"]] += Decimal("0")
    for currency, balance in opening.items():
        key = f"currency:{currency}"
        groups[key] = {"key": key, "name": f"Total interno · {currency}", "currency": currency, "opening_balance": money(balance)}
    if len(groups) * config.horizon_days > 50000:
        raise HTTPException(422, "La proyección supera 50000 saldos diarios. Reduzca el horizonte para mostrar todos los puntos sin omisiones.")
    timelines = []
    for key, group in groups.items():
        running = Decimal(group["opening_balance"])
        days = []
        for index in range(config.horizon_days):
            day = (today + timedelta(days=index)).isoformat()
            values = daily[(key, day)]
            start = running
            running += values["in"] - values["out"]
            days.append({"date": day, "opening": money(start), "incoming": money(values["in"]), "outgoing": money(values["out"]), "closing": money(running), "negative": running < 0, "requires_prior_receipts": start < values["out"], "source_keys": values["keys"]})
        timelines.append({**group, "closing_balance": money(running), "first_negative_date": next((item["date"] for item in days if item["negative"]), None), "days": days})
    return {"business_date": today.isoformat(), "end_date": end.isoformat(), "points": list(points.values()), "items": sorted(projected, key=lambda item: (item["due_date"], item["currency"], item["key"])), "timelines": timelines, "warnings": warnings, "stale_source_keys": stale, "in_transit_by_currency": transit, "method": "Saldo inicial de cajas abiertas y puntos de custodia registrados; las cajas cerradas quedan fuera hasta resolver su relevo. Vencidos al día de hoy; importes por moneda sin conversión; cobros por cuotas o deuda real; compras sin duplicar obligaciones; estimaciones de compras, gastos sin seguimiento de pago y tránsito desactivadas hasta confirmarlas. Los cobros y pagos proyectados son hipótesis; asigne los documentos que prevé mover en efectivo a su caja correspondiente. El saldo diario no garantiza el orden de entradas y salidas: las salidas superiores al saldo inicial requieren ingresos previos.", "generated_at": datetime.now(timezone.utc).isoformat()}


def latest_scenario(db, user, identifier, lock=False):
    query = select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == KIND, AnalyticsArtifact.artifact_key == str(identifier)).order_by(AnalyticsArtifact.version.desc()).limit(1)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Escenario no encontrado en la empresa activa.")
    return row


def serialize_scenario(row):
    data = json.loads(row.data_json)
    return {"id": row.artifact_key, "version": row.version, "name": data["name"], "reason": data["reason"], "config": data["config"], "created_at": row.created_at.isoformat(), "created_by": str(row.created_by)}


def list_scenarios(db, user):
    rows = bounded(db, select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == KIND).order_by(AnalyticsArtifact.version.desc(), AnalyticsArtifact.created_at.desc()))
    latest = {}
    for row in rows:
        latest.setdefault(row.artifact_key, row)
    return [serialize_scenario(row) for row in sorted(latest.values(), key=lambda value: value.created_at, reverse=True)]


def save_scenario(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"cash_forecast.save:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    previous = latest_scenario(db, user, identifier, True) if identifier else None
    if (previous.version if previous else 0) != payload.version:
        raise HTTPException(409, "El escenario cambió. Actualice antes de guardar otra versión.")
    config = ForecastConfig.model_validate(payload.model_dump())
    build_forecast(db, user, config, strict=True)
    row = AnalyticsArtifact(company_id=user.company_id, kind=KIND, artifact_key=str(identifier or uuid4()), version=payload.version + 1, status="active", parent_id=previous.id if previous else None, data_json=json.dumps({"name": payload.name, "reason": payload.reason, "config": config.model_dump(mode="json")}), created_by=user.user_id)
    db.add(row)
    db.flush()
    result = serialize_scenario(row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_CASH_FORECAST_SCENARIO", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"scenario_key": row.artifact_key, "version": row.version, "reason": payload.reason})
    complete_request(record, result)
    db.commit()
    return result


def scenario_history(db, user, identifier):
    latest_scenario(db, user, identifier)
    rows = bounded(db, select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == KIND, AnalyticsArtifact.artifact_key == str(identifier)).order_by(AnalyticsArtifact.version.desc()))
    return [serialize_scenario(row) for row in rows]
