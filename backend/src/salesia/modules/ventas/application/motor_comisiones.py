import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import or_, select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact

from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentReversalModel, TransferProofModel
from salesia.modules.inventario.infrastructure.models.entregas import DeliveryShipment
from salesia.modules.inventario.infrastructure_models import SupplyDocument, SupplyLine
from salesia.modules.organizacion.application.periodos import business_date
from salesia.modules.ventas.application.participacion_comercial import freeze_commission
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionEntryModel, CommissionSettlement, SalesTarget
from salesia.shared.infrastructure.models import AuditLogModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import CompanySettings, RefundModel

ZERO = Decimal("0")
SCALE = Decimal("0.000001")
VIRTUAL = ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT")


def aware(value):
    moment = datetime.fromisoformat(value) if isinstance(value, str) else value
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


def rounded(value):
    with localcontext() as context:
        context.prec = 60
        return value.quantize(SCALE, rounding=ROUND_HALF_UP)


def period_cut(db, company_id, period):
    try:
        year, month = map(int, period.split("-"))
        row = db.get(CompanySettings, company_id)
        zone = ZoneInfo(json.loads(row.values_json or "{}").get("timezone", "America/Lima") if row else "America/Lima")
        start = datetime(year, month, 1, tzinfo=zone)
        end = datetime(year + 1, 1, 1, tzinfo=zone) if month == 12 else datetime(year, month + 1, 1, tzinfo=zone)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
    except (ValueError, OverflowError, KeyError):
        raise HTTPException(422, "El período o la zona horaria no son válidos.")


def collected(db, company_id, sale, cutoff):
    identifiers = db.scalars(select(PaymentAllocationModel.payment_id).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.sale_id == sale.id, PaymentAllocationModel.created_at < cutoff)).all()
    receipts = []
    for identifier in set(identifiers):
        payment = db.scalar(select(PaymentModel).where(PaymentModel.company_id == company_id, PaymentModel.id == identifier, PaymentModel.currency == sale.currency, PaymentModel.status.in_(("confirmed", "refunded"))))
        if payment is None or payment.payment_method in VIRTUAL or aware(payment.created_at) >= cutoff:
            continue
        proof = db.scalar(select(TransferProofModel).where(TransferProofModel.company_id == company_id, TransferProofModel.payment_id == identifier))
        confirmed_at = aware(proof.verified_at) if proof and proof.verified and proof.verified_at else aware(payment.created_at)
        if proof and not proof.verified or confirmed_at >= cutoff:
            continue
        refunds = db.scalars(select(RefundModel).where(RefundModel.company_id == company_id, RefundModel.payment_id == identifier, RefundModel.unapplied_only.is_(False), RefundModel.status.in_(("confirmed", "approved", "processed", "completed")), RefundModel.created_at < cutoff)).all()
        reversals = db.scalars(select(PaymentReversalModel).where(PaymentReversalModel.company_id == company_id, PaymentReversalModel.payment_id == identifier, PaymentReversalModel.created_at < cutoff)).all()
        available = max(ZERO, payment.amount - sum((row.amount for row in [*refunds, *reversals]), ZERO))
        allocations = db.scalars(select(PaymentAllocationModel).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.payment_id == identifier, PaymentAllocationModel.created_at < cutoff).order_by(PaymentAllocationModel.created_at, PaymentAllocationModel.id)).all()
        for allocation in allocations:
            used = min(available, allocation.allocated_amount)
            available -= used
            at = max(aware(allocation.created_at), confirmed_at)
            if allocation.sale_id == sale.id and used > 0 and at < cutoff:
                receipts.append({"id": str(allocation.id), "payment_id": str(payment.id), "amount": str(used), "method": payment.payment_method, "at": at.isoformat()})
    return receipts


def delivered_quantities(db, company_id, sale, cutoff):
    quantities = defaultdict(lambda: ZERO)
    documents = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == company_id, SupplyDocument.sale_id == sale.id, SupplyDocument.kind == "DELIVERY")).all()
    for document in documents:
        details = json.loads(document.details_json or "{}")
        attempts = details.get("delivery_attempts", [])
        if attempts:
            for attempt in attempts:
                if aware(attempt["at"]) < cutoff:
                    for item in attempt["items"]:
                        quantities[UUID(item["product_id"])] += Decimal(item["accepted_quantity"])
        else:
            shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.company_id == company_id, DeliveryShipment.delivery_document_id == document.id))
            if shipment and shipment.status == "delivered" and shipment.delivered_at and aware(shipment.delivered_at) < cutoff:
                for line in db.scalars(select(SupplyLine).where(SupplyLine.document_id == document.id)).all():
                    quantities[line.product_id] += line.quantity
    result = {}
    for line in sorted(sale.lines, key=lambda row: row.line_number):
        if not documents and not sale.order_id:
            result[line.id] = line.quantity if line.delivered_at and aware(line.delivered_at) < cutoff and sale.fulfillment_status == "delivered" else ZERO
        else:
            result[line.id] = min(line.quantity, quantities[line.product_id])
            quantities[line.product_id] -= result[line.id]
    return result


def sale_measure(db, user, sale, snapshot, cutoff):
    policy = snapshot["policy"]
    returned = defaultdict(lambda: ZERO)
    return_references = []
    warnings = []
    rows = db.scalars(select(ReturnModel).where(ReturnModel.company_id == user.company_id, ReturnModel.sale_id == sale.id, ReturnModel.status == "accepted")).all()
    for ret in rows:
        detail = json.loads(ret.details_json or "{}")
        accepted_at = aware(detail["accepted_at"]) if detail.get("accepted_at") else aware(ret.updated_at)
        original_options = [{"id": str(line.id), "product_id": str(line.product_id), "line_number": line.line_number, "description": line.name_snapshot, "quantity": str(line.quantity), "unit_price": str(line.unit_price_snapshot), "discount": str(line.discount_amount)} for line in sale.lines]
        reference = {"id": str(ret.id), "accepted_at": accepted_at.isoformat(), "needs_acceptance_date": not bool(detail.get("accepted_at")), "updated_at": ret.updated_at.isoformat(), "created_at": ret.created_at.isoformat(), "reason": ret.reason, "unmapped_lines": [{"id": str(line.id), "product_id": str(line.product_id), "quantity": str(line.quantity), "original_options": [option for option in original_options if option["product_id"] == str(line.product_id)]} for line in ret.lines if line.sale_line_id is None]}
        if accepted_at >= cutoff:
            if not detail.get("accepted_at") and aware(ret.created_at) < cutoff:
                warnings.append(f"La devolución histórica {ret.id} requiere precisar su fecha de aceptación para este corte.")
                return_references.append(reference)
            continue
        for line in ret.lines:
            if line.sale_line_id is None:
                warnings.append(f"La devolución {ret.id} requiere identificar la línea original antes de liquidar comisiones.")
            else:
                returned[line.sale_line_id] += line.quantity
        return_references.append(reference)
    cancelled = False
    if sale.status == "cancelled":
        audit = db.scalar(select(AuditLogModel).where(AuditLogModel.company_id == user.company_id, AuditLogModel.entity_id == sale.id, AuditLogModel.action == "ANNUL_SALE").order_by(AuditLogModel.created_at).limit(1))
        cancelled = aware(audit.created_at if audit else sale.updated_at) < cutoff
        if audit is None and not cancelled:
            warnings.append(f"La anulación histórica de {sale.id} requiere identificar su fecha para este corte.")
    remaining_total = ZERO
    gross_base = ZERO
    returned_base = ZERO
    net_base = ZERO
    earned = ZERO
    deliveries = delivered_quantities(db, user.company_id, sale, cutoff) if policy["earned_on"] == "delivery" else {}
    receipts = collected(db, user.company_id, sale, cutoff) if policy["earned_on"] in ("collection", "full_payment") else []
    lines = []
    for line in sale.lines:
        remaining = max(ZERO, line.quantity - returned[line.id])
        remaining_total += line.total_amount * remaining / line.quantity
    paid = sum((Decimal(row["amount"]) for row in receipts), ZERO)
    payment_ratio = min(Decimal("1"), paid / remaining_total) if remaining_total > 0 else ZERO
    for line in sale.lines:
        if str(line.id) not in snapshot["eligible_line_ids"]:
            continue
        if returned[line.id] > line.quantity:
            warnings.append(f"Las devoluciones de la línea {line.id} superan su cantidad vendida.")
        remaining = max(ZERO, line.quantity - returned[line.id])
        base = max(ZERO, line.subtotal_amount - line.quantity * line.unit_cost_snapshot) if policy["base"] == "margin" else line.total_amount if policy["include_tax"] else line.subtotal_amount
        net = ZERO if cancelled else base * remaining / line.quantity
        earned_ratio = Decimal("1")
        if policy["earned_on"] == "collection":
            earned_ratio = payment_ratio
        elif policy["earned_on"] == "full_payment":
            earned_ratio = Decimal("1") if payment_ratio == 1 else ZERO
        elif policy["earned_on"] == "delivery":
            delivered = max(ZERO, deliveries.get(line.id, ZERO) - returned[line.id])
            earned_ratio = min(Decimal("1"), delivered / remaining) if remaining > 0 else ZERO
        earned_line = rounded(net * earned_ratio)
        gross_base += base
        returned_base += base - net
        net_base += net
        earned += earned_line
        lines.append({"line_id": str(line.id), "product_id": str(line.product_id), "description": line.name_snapshot, "quantity": str(line.quantity), "returned_quantity": str(returned[line.id]), "base_before_returns": str(rounded(base)), "net_base": str(rounded(net)), "earned_ratio": str(earned_ratio), "earned_base": str(earned_line)})
    return {"gross": rounded(gross_base), "returned": rounded(returned_base), "net": rounded(net_base), "earned": rounded(earned), "lines": lines, "receipts": receipts, "returns": return_references, "warnings": warnings, "cancelled": cancelled}


def calculate_details(db, user, representative, period, currency):
    start, cutoff = period_cut(db, user.company_id, period)
    if business_date(db, user.company_id, start) > business_date(db, user.company_id):
        raise HTTPException(422, "No calcule una liquidación de un mes que aún no comenzó.")
    prior = db.scalars(select(CommissionSettlement).where(CommissionSettlement.company_id == user.company_id, CommissionSettlement.representative_id == representative.id, CommissionSettlement.currency == currency, CommissionSettlement.period < period, CommissionSettlement.status.in_(("approved", "paid"))).order_by(CommissionSettlement.period)).all()
    prior_entries = []
    warnings = []
    for row in prior:
        entries = db.scalars(select(CommissionEntryModel).where(CommissionEntryModel.company_id == user.company_id, CommissionEntryModel.settlement_id == row.id)).all()
        if not row.calculation_hash:
            warnings.append(f"La liquidación histórica {row.id} requiere conciliar sus ventas y moneda antes de calcular ajustes posteriores.")
        prior_entries.extend(entries)
    recognized = defaultdict(lambda: ZERO)
    previous_rates = {}
    previous_baselines = {}
    previous_currency_rates = {}
    previous_sales = set()
    for entry in prior_entries:
        previous_sales.add(entry.sale_id)
        recognized[entry.sale_id] += entry.amount
        previous_baselines[entry.sale_id] = Decimal(json.loads(entry.details_json).get("baseline_amount", "0"))
        previous_currency_rates[entry.sale_id] = Decimal(json.loads(entry.details_json).get("currency_rate", "1"))
        if entry.earned_base > 0 or entry.cumulative_amount != 0:
            previous_rates[entry.sale_id] = json.loads(entry.details_json).get("rate")
    sales = db.scalars(select(SaleModel).where(SaleModel.company_id == user.company_id, or_(SaleModel.currency == currency, SaleModel.id.in_(list(previous_sales))), SaleModel.status != "draft", or_(SaleModel.confirmed_at < cutoff, SaleModel.confirmed_at.is_(None) & (SaleModel.created_at < cutoff)), or_(SaleModel.sales_rep_id == representative.id, SaleModel.commission_snapshot_json.contains(str(representative.id)))).order_by(SaleModel.confirmed_at, SaleModel.id)).all()
    measures = []
    monthly = defaultdict(lambda: ZERO)
    other_currency_sales = set(db.scalars(select(CommissionEntryModel.sale_id).join(CommissionSettlement, CommissionSettlement.id == CommissionEntryModel.settlement_id).where(CommissionEntryModel.company_id == user.company_id, CommissionSettlement.company_id == user.company_id, CommissionSettlement.representative_id == representative.id, CommissionSettlement.currency != currency, CommissionSettlement.status.in_(("approved", "paid")))).all())
    for sale in sales:
        if sale.id in other_currency_sales:
            continue
        snapshot = freeze_commission(db, sale, historical=True)
        participant = next((row for row in snapshot["participants"] if row["representative_id"] == str(representative.id)), None)
        if participant is None:
            continue
        measure = sale_measure(db, user, sale, snapshot, cutoff)
        share = Decimal(participant["percentage"]) / 100
        month = snapshot["sale_date"][:7]
        target_type = "margin" if snapshot["policy"]["base"] == "margin" else "amount"
        monthly[(month, target_type, sale.currency)] += measure["net"] * share
        measures.append((sale, snapshot, participant, measure, share, month, target_type))
    entries = []
    gross = ZERO
    returned = ZERO
    earned_total = ZERO
    policies = {}
    for sale, snapshot, participant, measure, share, month, target_type in measures:
        policy = snapshot["policy"]
        if month < period and sale.id not in previous_sales and policy["earned_on"] == "sale":
            continue
        warnings.extend(measure["warnings"])
        target = db.scalar(select(SalesTarget).where(SalesTarget.company_id == user.company_id, SalesTarget.representative_id == representative.id, SalesTarget.period == month, SalesTarget.target_type == target_type, SalesTarget.currency == sale.currency, SalesTarget.scope == "individual"))
        from salesia.shared.infrastructure.models import CompanyModel
        base_currency = db.scalar(select(CompanyModel.base_currency).where(CompanyModel.id == user.company_id))
        quota = target.target_value if target else representative.monthly_quota if sale.currency == base_currency and target_type == "amount" else ZERO
        attainment = monthly[(month, target_type, sale.currency)] / quota * 100 if quota > 0 else ZERO
        tiers = [tier for tier in policy["tiers"] if Decimal(tier["minimum_attainment"]) <= attainment]
        current_rate = Decimal(max(tiers, key=lambda tier: Decimal(tier["minimum_attainment"]))["rate"]) if tiers else ZERO
        rate = Decimal(previous_rates[sale.id]) if previous_rates.get(sale.id) is not None else current_rate
        currency_rate = previous_currency_rates.get(sale.id, Decimal("1"))
        baseline = previous_baselines.get(sale.id, ZERO)
        if month < period and sale.id not in previous_sales:
            before = sale_measure(db, user, sale, snapshot, start)
            warnings.extend(before["warnings"])
            baseline = rounded(before["earned"] * share * rate * currency_rate)
        cumulative = rounded(max(ZERO, measure["earned"] * share * rate * currency_rate - baseline))
        delta = rounded(cumulative - recognized[sale.id])
        detail = {"sale_id": str(sale.id), "document_number": f"{sale.series}-{sale.number:08d}", "sale_period": month, "currency": currency, "native_currency": sale.currency, "currency_rate": str(currency_rate), "policy_version": policy["version"], "historical_snapshot": snapshot["historical"], "base": policy["base"], "include_tax": policy["include_tax"], "earned_on": policy["earned_on"], "participant": participant, "quota": str(quota), "attainment": str(rounded(attainment)), "rate": str(rate), "rate_source": "previous_recognition" if sale.id in previous_rates else "original_sale_period", "gross": str(measure["gross"]), "returns_deduction": str(measure["returned"]), "net_base": str(measure["net"]), "earned_base": str(rounded(measure["earned"] * share * currency_rate)), "native_earned_base": str(rounded(measure["earned"] * share)), "cumulative_amount": str(cumulative), "baseline_amount": str(baseline), "previously_recognized": str(recognized[sale.id]), "amount": str(delta), "lines": measure["lines"], "receipts": measure["receipts"], "returns": measure["returns"], "cancelled": measure["cancelled"]}
        if delta != 0 or month == period or measure["warnings"]:
            entries.append(detail)
        if month == period:
            gross += measure["gross"] * share
            returned += measure["returned"] * share
            earned_total += measure["earned"] * share
        policies[str(policy["version"])] = policy
    adjustment_rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "commission_adjustment", AnalyticsArtifact.status == "approved").order_by(AnalyticsArtifact.created_at, AnalyticsArtifact.id)).all()
    manual_adjustments = []
    for adjustment in adjustment_rows:
        item = json.loads(adjustment.data_json)
        if item["representative_id"] == str(representative.id) and item["currency"] == currency and item["period"] == period:
            manual_adjustments.append({"id": str(adjustment.id), "source_settlement_id": item["source_settlement_id"], "amount": item["amount"], "reason": item["reason"], "evidence_reference": item["evidence_reference"], "review": item["review"]})
    commission = rounded(sum((Decimal(row["amount"]) for row in entries), ZERO) + sum((Decimal(item["amount"]) for item in manual_adjustments), ZERO))
    carry_in = prior[-1].carried_balance if prior else ZERO
    payable = rounded(max(ZERO, commission - carry_in))
    carry_out = rounded(max(ZERO, carry_in - commission))
    data = {"schema": 2, "period": period, "currency": currency, "gross": str(rounded(gross)), "returns": str(rounded(returned)), "earned_base": str(rounded(earned_total)), "commission_amount": str(commission), "carry_in": str(carry_in), "payable_amount": str(payable), "carried_balance": str(carry_out), "prior_settlements": [{"id": str(row.id), "version": row.version, "hash": row.calculation_hash} for row in prior], "policies": policies, "entries": entries, "manual_adjustments": manual_adjustments, "warnings": sorted(set(warnings)), "rules": {"timezone": "company", "rounding": "HALF_UP_6_DECIMALS", "rates": "La tasa se fija en el primer reconocimiento y se conserva para ajustes de la misma venta.", "margin": "Los márgenes negativos generan base cero por línea y no compensan márgenes positivos.", "collections": "Solo dinero confirmado y aplicado, neto de reembolsos y reversos al corte; los créditos internos no cuentan como dinero nuevo."}}
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return data, digest
