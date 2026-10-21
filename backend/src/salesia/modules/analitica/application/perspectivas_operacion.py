import json
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentReversalModel, TransferProofModel
from salesia.modules.organizacion.application.calendario_operativo import effective_calendar
from salesia.modules.ventas.application.motor_comisiones import collected, delivered_quantities
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesRepresentative
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import RefundModel

ZERO = Decimal("0")


class PerspectiveRequest(BaseModel):
    start: date
    end: date
    basis: Literal["sale", "collection", "delivery"] = "sale"
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    branch_id: UUID | None = None
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def bounded(self):
        if self.start.year < 1900 or self.end.year > 9900 or self.end < self.start or (self.end - self.start).days > 365:
            raise ValueError("Seleccione fechas ordenadas, entre 1900 y 9900, para un intervalo de hasta 366 días.")
        return self


def money(value):
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))


def bounds(calendar, payload):
    zone = ZoneInfo(calendar["timezone"])
    now = datetime.now(timezone.utc)
    if payload.end > now.astimezone(zone).date():
        raise HTTPException(422, "Seleccione un período observado; una fecha futura corresponde a una previsión.")
    start = datetime.combine(payload.start, time.min, tzinfo=zone).astimezone(timezone.utc)
    end = min(datetime.combine(payload.end + timedelta(days=1), time.min, tzinfo=zone).astimezone(timezone.utc), now)
    return start, end, now


def changed_cash_sales(db, company_id, start, end):
    changes = select(PaymentAllocationModel.payment_id).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.created_at >= start, PaymentAllocationModel.created_at < end).union(select(RefundModel.payment_id).where(RefundModel.company_id == company_id, RefundModel.created_at >= start, RefundModel.created_at < end, RefundModel.unapplied_only.is_(False), RefundModel.status.in_(["confirmed", "approved", "processed", "completed"])), select(PaymentReversalModel.payment_id).where(PaymentReversalModel.company_id == company_id, PaymentReversalModel.created_at >= start, PaymentReversalModel.created_at < end), select(TransferProofModel.payment_id).where(TransferProofModel.company_id == company_id, TransferProofModel.verified.is_(True), TransferProofModel.verified_at >= start, TransferProofModel.verified_at < end)).subquery()
    return select(PaymentAllocationModel.sale_id).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.payment_id.in_(select(changes.c.payment_id)), PaymentAllocationModel.created_at < end)


def query_sales(db, user, payload, start, end, currency):
    query = select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.currency == currency, SaleModel.status != "draft", func.coalesce(SaleModel.confirmed_at, SaleModel.created_at) < end)
    if payload.branch_id:
        query = query.where(SaleModel.branch_id == payload.branch_id)
    if user.role == "salesperson":
        representatives = db.scalars(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == user.user_id)).all()
        condition = SaleModel.sales_rep_id.in_(representatives)
        for identifier in representatives:
            condition = condition | SaleModel.commission_snapshot_json.contains(str(identifier))
        query = query.where(condition)
    if payload.basis == "sale":
        query = query.where(SaleModel.status.in_(["confirmed", "paid", "refunded"]), SaleModel.confirmed_at >= start, SaleModel.confirmed_at < end)
    elif payload.basis == "collection":
        query = query.where(SaleModel.id.in_(changed_cash_sales(db, user.company_id, start, end)))
    else:
        query = query.where(SaleModel.status.in_(["confirmed", "paid", "refunded"]))
    return query


def definition(basis):
    common = {"version": 1, "currency_policy": "Importes de una única moneda de venta, sin conversiones implícitas ni suma de monedas distintas.", "rounding": "Suma en decimal; presentación a seis decimales con redondeo HALF_EVEN.", "average": "Importe total dividido entre operaciones cuantificadas de esta misma base. En cobros solo se cuentan documentos con variación neta distinta de cero; los pendientes de moneda sin importe cuantificable quedan fuera del promedio. No se comparan promedios de bases diferentes."}
    specific = {
        "sale": {"name": "Facturación por confirmación de venta", "formula": "Suma del total de documentos confirmados dentro del intervalo; el total incluye impuestos y los descuentos ya aplicados.", "date_reference": "confirmed_at", "states": ["confirmed", "paid", "refunded"], "cancellations": "Se excluyen documentos cuyo estado actual es anulado o borrador.", "returns": "Esta cifra muestra facturación original. Las devoluciones, notas de crédito y saldos a favor se consultan como ajustes separados; no se sustituye la facturación por un desembolso de reembolso."},
        "collection": {"name": "Cobro neto aplicado a documentos", "formula": "Diferencia entre aplicaciones monetarias netas verificadas al final y al inicio del intervalo. Los reembolsos aplicados y las reversiones disminuyen el importe; se conservan valores negativos.", "date_reference": "Aplicación del cobro, verificación de transferencia, reembolso o reversión", "states": ["confirmed", "refunded"], "cancellations": "El estado de la venta no borra entradas o salidas monetarias registradas. El movimiento se evalúa a sus fechas.", "returns": "Solo un reembolso o reversión registrado disminuye esta cifra. El saldo de tienda, los créditos de cambios y otros medios virtuales no vuelven a contarse como dinero. Los anticipos sin aplicar no se consideran cobro de una venta."},
        "delivery": {"name": "Valor comercial de unidades entregadas", "formula": "Incremento de unidades aceptadas entre ambos cortes, valorado con el total histórico por unidad de cada línea, incluyendo sus descuentos e impuestos.", "date_reference": "Resultado físico de entrega o constancia de entrega directa", "states": ["Entrega aceptada", "Documento de venta vigente"], "cancellations": "Se excluyen ventas anuladas según su estado actual. Un despacho en tránsito no equivale a una entrega aceptada.", "returns": "Representa entrega bruta, sin restar devoluciones físicas posteriores ni tratar un reembolso como movimiento de entrega. Una asignación ambigua entre líneas repetidas se señala como dato por conciliar."},
    }
    return {**common, **specific[basis]}


def calculate(db, user, payload):
    if payload.basis == "collection" and "payments:read" not in user.permissions:
        raise HTTPException(403, "La perspectiva de cobros requiere permiso para consultar pagos.")
    if payload.basis == "delivery" and "inventory:read" not in user.permissions:
        raise HTTPException(403, "La perspectiva de entregas requiere permiso de lectura de inventario.")
    calendar = effective_calendar(db, user.company_id, payload.branch_id)
    start, end, now = bounds(calendar, payload)
    company = db.get(CompanyModel, user.company_id)
    currency = payload.currency or (company.base_currency if company else "USD")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise HTTPException(422, "La moneda de consulta debe tener tres letras mayúsculas.")
    query = query_sales(db, user, payload, start, end, currency)
    count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    if count > 20000:
        raise HTTPException(413, "La selección supera 20 000 operaciones para esta consulta interactiva. Reduzca las fechas o consulte una sede para mantener un cálculo completo.")
    sales = db.scalars(query.order_by(SaleModel.confirmed_at, SaleModel.id)).all()
    records, warnings = [], []
    total, positive, negative = ZERO, ZERO, ZERO
    clients = set()
    measured_count = 0
    for sale in sales:
        quality = []
        if payload.basis == "sale":
            value = sale.total_amount
        elif payload.basis == "collection":
            incompatible = db.scalar(select(PaymentModel.id).join(PaymentAllocationModel, PaymentAllocationModel.payment_id == PaymentModel.id).where(PaymentModel.company_id == user.company_id, PaymentAllocationModel.company_id == user.company_id, PaymentAllocationModel.sale_id == sale.id, PaymentModel.currency != sale.currency, PaymentModel.status.in_(["confirmed", "refunded"])).limit(1))
            if incompatible:
                quality.append("Hay cobros en otra moneda cuya equivalencia requiere conciliación; no se suman sus importes como si fueran de la moneda de esta venta.")
            before = sum((Decimal(item["amount"]) for item in collected(db, user.company_id, sale, start)), ZERO)
            after = sum((Decimal(item["amount"]) for item in collected(db, user.company_id, sale, end)), ZERO)
            value = after - before
            if value == 0 and not quality:
                continue
        else:
            before = delivered_quantities(db, user.company_id, sale, start)
            after = delivered_quantities(db, user.company_id, sale, end)
            differences = {line.id: after.get(line.id, ZERO) - before.get(line.id, ZERO) for line in sale.lines}
            if not any(differences.values()):
                continue
            value = sum((line.total_amount * differences[line.id] / line.quantity for line in sale.lines if line.quantity > 0), ZERO)
            if len({line.product_id for line in sale.lines}) < len(sale.lines):
                quality.append("El documento repite un producto en varias líneas. La distribución física disponible sigue el orden de línea; confirme su origen antes de interpretar el valor como definitivo.")
        total += value
        positive += max(ZERO, value)
        negative += min(ZERO, value)
        if payload.basis != "collection" or value != 0:
            measured_count += 1
            clients.add(sale.customer_id)
        warnings.extend({"sale_id": str(sale.id), "reference": f"{sale.series}-{sale.number:08d}", "message": message} for message in quality)
        records.append({"sale_id": str(sale.id), "reference": f"{sale.series}-{sale.number:08d}", "currency": sale.currency, "amount": money(value), "status": sale.status, "confirmed_at": sale.confirmed_at.isoformat() if sale.confirmed_at else None, "requires_reconciliation": bool(quality)})
    details_allowed = "sales:read" in user.permissions
    return {"basis": payload.basis, "definition": definition(payload.basis), "currency": currency, "branch_id": str(payload.branch_id) if payload.branch_id else None, "timezone": calendar["timezone"], "start": payload.start.isoformat(), "end": payload.end.isoformat(), "start_at": start.isoformat(), "cutoff_at": end.isoformat(), "generated_at": now.isoformat(), "is_partial_day": payload.end == now.astimezone(ZoneInfo(calendar["timezone"])).date(), "amount": money(total), "positive_amount": money(positive), "negative_amount": money(negative), "operations_count": measured_count, "customers_count": len(clients), "average_operation": money(total / measured_count) if measured_count else None, "complete": not warnings, "warnings": warnings if details_allowed else [{"message": item["message"]} for item in warnings], "details_allowed": details_allowed, "items": records[payload.offset:payload.offset + payload.limit] if details_allowed else [], "total_count": len(records) if details_allowed else 0, "limits": {"interactive_candidates": 20000, "calculated_candidates": count}, "calendar_versions": {"local": calendar["version"], "company": calendar["company_version"]}}


def options(db, user):
    company = db.get(CompanyModel, user.company_id)
    calendar = effective_calendar(db, user.company_id)
    today = datetime.now(timezone.utc).astimezone(ZoneInfo(calendar["timezone"])).date()
    branches = db.scalars(select(BranchModel).where(BranchModel.company_id == user.company_id).order_by(BranchModel.code)).all()
    currencies = db.scalars(select(SaleModel.currency).where(SaleModel.company_id == user.company_id).distinct()).all()
    currency = company.base_currency if company else "USD"
    return {"currency": currency, "currencies": sorted({currency, *[value for value in currencies if re.fullmatch(r"[A-Z]{3}", value)]}), "business_date": today.isoformat(), "default_start": (today - timedelta(days=29)).isoformat(), "timezone": calendar["timezone"], "branches": [{"id": str(row.id), "name": row.name, "code": row.code, "is_active": row.is_active, "timezone": row.timezone} for row in branches], "available_bases": ["sale"] + (["collection"] if "payments:read" in user.permissions else []) + (["delivery"] if "inventory:read" in user.permissions else []), "cost_visible": "products:cost:read" in user.permissions}
