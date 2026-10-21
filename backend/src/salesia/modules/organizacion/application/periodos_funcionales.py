import hashlib
import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyTransferModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import ExpenseModel, PayableModel
from salesia.modules.finanzas.infrastructure.models.pagos import FinanceReconciliationModel, TransferProofModel
from salesia.modules.inventario.infrastructure_models import InventoryQuarantine, InventoryReconciliation, PhysicalCountSession, SupplyDocument
from salesia.modules.organizacion.application.periodos import business_date
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionSettlement
from salesia.shared.infrastructure.models import CashSessionModel, CompanyModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import CompanySettings, claim_request, complete_request

MODULES = {"sales": "Ventas", "inventory": "Inventario", "purchases": "Compras", "treasury": "Caja y tesorería", "receivables": "Cobros y cuentas por cobrar", "payables": "Cuentas por pagar", "expenses": "Gastos", "returns": "Devoluciones y reembolsos", "commissions": "Comisiones"}


class ClosePreview(BaseModel):
    modules: list[str] = Field(min_length=1, max_length=9)
    closed_until: date
    expected_version: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_modules(self):
        if len(set(self.modules)) != len(self.modules) or set(self.modules) - set(MODULES):
            raise ValueError("Seleccione módulos conocidos sin repetirlos.")
        return self


class CloseRequest(ClosePreview):
    preview_hash: str = Field(min_length=64, max_length=64)
    acknowledge_pending: bool = False
    reason: str = Field(min_length=5, max_length=2000)


class ReopenRequest(BaseModel):
    module: Literal["sales", "inventory", "purchases", "treasury", "receivables", "payables", "expenses", "returns", "commissions"]
    start: date
    end: date
    hours: int = Field(default=24, ge=1, le=168)
    expected_version: int = Field(ge=0)
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def bounded(self):
        if self.end < self.start or (self.end - self.start).days > 366:
            raise ValueError("La reapertura debe tener fechas ordenadas y abarcar como máximo 367 días.")
        return self


class RevokeRequest(BaseModel):
    module: str
    identifier: str = Field(min_length=1, max_length=64)
    expected_version: int = Field(ge=0)
    reason: str = Field(min_length=5, max_length=2000)


def values(db, company_id):
    row = db.get(CompanySettings, company_id)
    return row, json.loads(row.values_json or "{}") if row else {}


def state(db, company_id):
    row, saved = values(db, company_id)
    return {"version": row.version if row else 0, "modules": MODULES, "controls": saved.get("module_periods", {}), "closed_until": saved.get("closed_until"), "closed_periods": saved.get("closed_periods", []), "legacy_reopenings": saved.get("reopened_period_ranges", []), "business_date": business_date(db, company_id).isoformat()}


def pending(db, company_id, modules, cutoff):
    _, saved = values(db, company_id)
    end = datetime.combine(cutoff + timedelta(days=1), time.min, tzinfo=ZoneInfo(saved.get("timezone", "America/Lima"))).astimezone(timezone.utc)
    checks = []

    def check(module, code, label, model, conditions, hard=False, dated=True):
        if module not in modules:
            return
        query = select(model).where(model.company_id == company_id, *conditions)
        if dated:
            query = query.where(model.created_at < end)
        count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        examples = db.scalars(query.order_by(model.id).limit(20)).all() if count else []
        checks.append({"module": module, "code": code, "label": label, "count": count, "blocking": hard and count > 0, "samples": [{"id": str(item.id), "status": getattr(item, "status", None), "reference": getattr(item, "code", None) or getattr(item, "document_number", None) or str(item.id)[:8]} for item in examples]})

    check("sales", "drafts", "Borradores de venta que todavía no afectan saldos", SaleModel, [SaleModel.status == "draft"])
    check("inventory", "counts", "Conteos físicos sin concluir", PhysicalCountSession, [PhysicalCountSession.status.notin_(["approved", "cancelled", "completed"])], True)
    check("inventory", "discrepancies", "Discrepancias de stock sin resolver", InventoryReconciliation, [InventoryReconciliation.status == "DETECTED"], True)
    check("inventory", "quarantine", "Unidades retenidas en cuarentena", InventoryQuarantine, [InventoryQuarantine.status == "IN_QUARANTINE", InventoryQuarantine.quantity > 0])
    check("purchases", "open_orders", "Compromisos de compra pendientes de completar", SupplyDocument, [SupplyDocument.kind.in_(["PURCHASE_ORDER", "PURCHASE_REQUISITION", "PURCHASE_AGREEMENT"]), SupplyDocument.status.notin_(["closed", "cancelled", "received", "completed", "rejected"])])
    check("purchases", "receipts", "Recepciones pendientes de aceptación o inspección", SupplyDocument, [SupplyDocument.kind == "GOODS_RECEIPT", SupplyDocument.status.notin_(["accepted", "closed", "cancelled", "completed", "rejected"])], True)
    check("treasury", "cash", "Cajas sin cerrar", CashSessionModel, [CashSessionModel.status == "open"], True)
    check("treasury", "transfers", "Traspasos de efectivo sin recepción o retorno", CashCustodyTransferModel, [CashCustodyTransferModel.status.in_(["sent", "disputed", "return_pending"])], True)
    live_payments = select(PaymentModel.id).where(PaymentModel.company_id == company_id, PaymentModel.status.in_(["pending", "confirmed"]))
    check("receivables", "proofs", "Constancias de transferencia sin verificar", TransferProofModel, [TransferProofModel.verified.is_(False), TransferProofModel.payment_id.in_(live_payments)], True)
    check("receivables", "pending_payments", "Cobros pendientes de confirmación", PaymentModel, [PaymentModel.status == "pending"], True)
    check("receivables", "reconciliation", "Conciliaciones de cobros sin concluir", FinanceReconciliationModel, [FinanceReconciliationModel.status == "open", FinanceReconciliationModel.period_start < end], True, False)
    check("receivables", "debt", "Deudas de clientes que continúan al siguiente período", SaleModel, [SaleModel.status.in_(["confirmed", "paid"]), SaleModel.total_amount > SaleModel.paid_amount])
    check("payables", "payables", "Obligaciones con saldo que continúan al siguiente período", PayableModel, [PayableModel.status.notin_(["paid", "cancelled"])])
    check("expenses", "expenses", "Gastos pendientes de autorización o pago", ExpenseModel, [ExpenseModel.status.notin_(["paid", "cancelled", "rejected"])])
    check("returns", "returns", "Devoluciones pendientes de decisión", ReturnModel, [ReturnModel.status == "requested"])
    check("commissions", "calculations", "Liquidaciones calculadas sin aprobar", CommissionSettlement, [CommissionSettlement.period <= cutoff.strftime("%Y-%m"), CommissionSettlement.status == "calculated"], True, False)
    check("commissions", "payouts", "Comisiones aprobadas por desembolsar", CommissionSettlement, [CommissionSettlement.period <= cutoff.strftime("%Y-%m"), CommissionSettlement.status == "approved"], False, False)
    return checks


def preview(db, company_id, payload):
    current = state(db, company_id)
    if current["version"] != payload.expected_version:
        raise HTTPException(409, "La configuración de períodos cambió. Consulte los cierres vigentes.")
    if payload.closed_until > date.fromisoformat(current["business_date"]):
        raise HTTPException(422, "No se puede cerrar una fecha futura.")
    for module in payload.modules:
        closed = current["controls"].get(module, {}).get("closed_until")
        if closed and payload.closed_until < date.fromisoformat(closed):
            raise HTTPException(409, "No reduzca un cierre existente. Autorice una reapertura acotada.")
    checks = pending(db, company_id, payload.modules, payload.closed_until)
    result = {"version": current["version"], "modules": sorted(payload.modules), "closed_until": payload.closed_until.isoformat(), "checks": checks, "can_close": not any(item["blocking"] for item in checks), "requires_acknowledgement": any(item["count"] > 0 and not item["blocking"] for item in checks), "definition": "Los bloqueos deben resolverse antes del cierre. Los compromisos y deudas abiertos se conservan y pasan al período siguiente con reconocimiento explícito; el cierre no los cancela ni modifica sus importes."}
    result["preview_hash"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


def persist(db, user, row, saved, action, data):
    if row is None:
        row = CompanySettings(company_id=user.company_id, version=0, values_json="{}")
        db.add(row)
    row.version += 1
    row.values_json = json.dumps(saved)
    event = {"action": action, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), **data}
    db.add(AnalyticsArtifact(company_id=user.company_id, kind="period_control", artifact_key="company", version=row.version, status="recorded", data_json=json.dumps(event), created_by=user.user_id))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type="AccountingPeriod", entity_id=user.company_id, diff={"version": row.version, **event})
    db.flush()
    return row


def close(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "period.modules.close", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    impact = preview(db, user.company_id, payload)
    if impact["preview_hash"] != payload.preview_hash:
        raise HTTPException(409, "Los pendientes cambiaron. Vuelva a revisar el cierre.")
    if not impact["can_close"] or impact["requires_acknowledgement"] and not payload.acknowledge_pending:
        raise HTTPException(409, {"message": "Resuelva los bloqueos y reconozca los pendientes que continúan al siguiente período.", "preview": impact})
    row, saved = values(db, user.company_id)
    controls = saved.setdefault("module_periods", {})
    for module in payload.modules:
        previous = controls.get(module, {})
        controls[module] = {"closed_until": payload.closed_until.isoformat(), "reopenings": [item for item in previous.get("reopenings", []) if item["start"] > payload.closed_until.isoformat()], "actor": user.email, "reason": payload.reason, "at": datetime.now(timezone.utc).isoformat()}
    persist(db, user, row, saved, "MODULE_PERIODS_CLOSED", {"reason": payload.reason, "impact": impact, "acknowledged_pending": payload.acknowledge_pending})
    result = state(db, user.company_id)
    complete_request(record, result)
    db.commit()
    return result


def reopen(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "period.modules.reopen", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row, saved = values(db, user.company_id)
    if (row.version if row else 0) != payload.expected_version:
        raise HTTPException(409, "La configuración de períodos cambió. Consulte los cierres vigentes.")
    control = saved.setdefault("module_periods", {}).setdefault(payload.module, {"closed_until": None, "reopenings": []})
    day = payload.start
    while day <= payload.end:
        cutoffs = [value for value in (control.get("closed_until"), saved.get("closed_until")) if value]
        if not any(day <= date.fromisoformat(value) for value in cutoffs) and day.strftime("%Y-%m") not in saved.get("closed_periods", []):
            raise HTTPException(422, "Todas las fechas de la reapertura deben pertenecer a un período cerrado del módulo.")
        if day == payload.end:
            break
        day += timedelta(days=1)
    now = datetime.now(timezone.utc)
    authorization = {"id": uuid4().hex, "start": payload.start.isoformat(), "end": payload.end.isoformat(), "expires_at": (now + timedelta(hours=payload.hours)).isoformat(), "actor": user.email, "actor_id": str(user.user_id), "at": now.isoformat(), "reason": payload.reason}
    control.setdefault("reopenings", []).append(authorization)
    persist(db, user, row, saved, "MODULE_PERIOD_REOPENED", {"module": payload.module, "authorization": authorization, "reason": payload.reason})
    result = state(db, user.company_id)
    complete_request(record, result)
    db.commit()
    return result


def revoke(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "period.modules.revoke", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row, saved = values(db, user.company_id)
    if (row.version if row else 0) != payload.expected_version:
        raise HTTPException(409, "La configuración de períodos cambió.")
    control = saved.get("module_periods", {}).get(payload.module, {})
    selected = next((item for item in control.get("reopenings", []) if item["id"] == payload.identifier), None)
    if selected is None:
        raise HTTPException(404, "Autorización de reapertura no encontrada en el módulo.")
    control["reopenings"] = [item for item in control["reopenings"] if item["id"] != payload.identifier]
    persist(db, user, row, saved, "MODULE_REOPENING_REVOKED", {"module": payload.module, "authorization": selected, "reason": payload.reason})
    result = state(db, user.company_id)
    complete_request(record, result)
    db.commit()
    return result
