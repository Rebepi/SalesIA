import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.organizacion.application.periodos import business_date, require_open_month, require_open_period
from salesia.modules.ventas.application.comisiones import get_settlement, history, scoped_settlement
from salesia.modules.ventas.application.motor_comisiones import period_cut, rounded
from salesia.modules.ventas.application.motor_comisiones import aware
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnLineModel, ReturnModel
from salesia.modules.ventas.application.participacion_comercial import freeze_commission
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionEntryModel, CommissionSettlement, SalesRepresentative
from salesia.shared.infrastructure.models import SaleLineModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

KINDS = ("commission_adjustment", "commission_reconciliation")


class ManualAdjustmentRequest(BaseModel):
    expected_version: int = Field(ge=1)
    period: str = Field(pattern=r"^\d{4}-\d{2}$")
    amount: Decimal = Field(max_digits=20, decimal_places=6)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_reference: str = Field(min_length=5, max_length=255)

    @model_validator(mode="after")
    def nonzero(self):
        if self.amount == 0:
            raise ValueError("El ajuste debe tener un importe distinto de cero.")
        return self


class HistoricalCommissionEntry(BaseModel):
    sale_id: UUID
    currency_rate: Decimal = Field(default=Decimal("1"), gt=0, max_digits=20, decimal_places=10)
    conversion_reference: str | None = Field(default=None, min_length=5, max_length=255)
    recognized_base: Decimal = Field(max_digits=20, decimal_places=6)
    rate: Decimal = Field(ge=0, le=1, max_digits=10, decimal_places=6)
    amount: Decimal = Field(max_digits=20, decimal_places=6)

    @model_validator(mode="after")
    def consistent_amount(self):
        with localcontext() as context:
            context.prec = 50
            expected = rounded(self.recognized_base * self.rate * self.currency_rate)
        if expected != self.amount:
            raise ValueError("El importe reconocido debe coincidir con la base firmada y su tasa histórica.")
        return self


class HistoricalReconciliationRequest(BaseModel):
    expected_version: int = Field(ge=1)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    entries: list[HistoricalCommissionEntry] = Field(default_factory=list, max_length=1000)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_reference: str = Field(min_length=5, max_length=255)

    @model_validator(mode="after")
    def unique_sales(self):
        if len({row.sale_id for row in self.entries}) != len(self.entries):
            raise ValueError("Consolide una sola aplicación histórica por venta en esta liquidación.")
        return self


class CaseReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)
    approve: bool
    reason: str = Field(min_length=10, max_length=2000)


class AcceptanceDateRequest(BaseModel):
    expected_updated_at: datetime
    accepted_at: datetime
    reason: str = Field(min_length=10, max_length=2000)
    evidence_reference: str = Field(min_length=5, max_length=255)


class ReturnLineOrigin(BaseModel):
    return_line_id: UUID
    sale_line_id: UUID


class ReturnOriginRequest(BaseModel):
    expected_updated_at: datetime
    lines: list[ReturnLineOrigin] = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_reference: str = Field(min_length=5, max_length=255)


def identify_return_lines(db, user, identifier, return_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.return_origins:{return_id}", key, {"settlement_id": str(identifier), **payload.model_dump(mode="json")})
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    source = scoped_settlement(db, user, identifier, True)
    ret = db.scalar(select(ReturnModel).where(ReturnModel.company_id == user.company_id, ReturnModel.id == return_id).with_for_update())
    if ret is None or ret.status != "accepted" or aware(ret.updated_at) != aware(payload.expected_updated_at):
        raise HTTPException(409, "La devolución no está disponible en su versión vigente.")
    if not db.scalar(select(CommissionEntryModel.id).where(CommissionEntryModel.company_id == user.company_id, CommissionEntryModel.settlement_id == source.id, CommissionEntryModel.sale_id == ret.sale_id).limit(1)):
        raise HTTPException(422, "La devolución no pertenece a una venta del detalle de la liquidación.")
    pending = {row.id: row for row in ret.lines if row.sale_line_id is None}
    if len({item.return_line_id for item in payload.lines}) != len(payload.lines) or set(pending) != {item.return_line_id for item in payload.lines}:
        raise HTTPException(422, "Identifique una sola vez el origen de todas las líneas aún pendientes de esta devolución.")
    original = {row.id: row for row in db.scalars(select(SaleLineModel).where(SaleLineModel.company_id == user.company_id, SaleLineModel.sale_id == ret.sale_id)).all()}
    committed = db.execute(select(ReturnLineModel.sale_line_id, func.sum(ReturnLineModel.quantity)).join(ReturnModel, ReturnModel.id == ReturnLineModel.return_id).where(ReturnModel.company_id == user.company_id, ReturnModel.sale_id == ret.sale_id, ReturnModel.status.notin_(("rejected", "cancelled")), ReturnLineModel.sale_line_id.is_not(None)).group_by(ReturnLineModel.sale_line_id)).all()
    quantities = {line_id: quantity for line_id, quantity in committed}
    for item in payload.lines:
        line = pending[item.return_line_id]
        sold = original.get(item.sale_line_id)
        if sold is None or sold.product_id != line.product_id:
            raise HTTPException(422, "Cada línea devuelta debe identificar el mismo producto dentro de su venta original.")
        quantities[sold.id] = quantities.get(sold.id, Decimal("0")) + line.quantity
        delivered = sold.fulfilled_quantity if sold.fulfilled_quantity is not None else sold.quantity
        if quantities[sold.id] > delivered:
            raise HTTPException(409, "La cantidad comprometida en devoluciones supera las unidades entregadas de la línea elegida.")
        returned_serials = json.loads(line.serial_numbers_json or "[]")
        sold_serials = json.loads(sold.serial_numbers_json or "[]")
        if returned_serials and (len(returned_serials) != len(set(returned_serials)) or not set(returned_serials).issubset(set(sold_serials))):
            raise HTTPException(409, "Las series devueltas no coinciden con las series identificadas de la línea vendida.")
        if returned_serials:
            other_lines = db.scalars(select(ReturnLineModel).join(ReturnModel, ReturnModel.id == ReturnLineModel.return_id).where(ReturnModel.company_id == user.company_id, ReturnModel.sale_id == ret.sale_id, ReturnModel.status.notin_(("rejected", "cancelled")), ReturnLineModel.id != line.id, ReturnLineModel.product_id == line.product_id)).all()
            if any(set(returned_serials) & set(json.loads(other.serial_numbers_json or "[]")) for other in other_lines):
                raise HTTPException(409, "Una serie ya aparece comprometida en otra línea de devolución.")
        line.sale_line_id = sold.id
    detail = json.loads(ret.details_json or "{}")
    adoption = {"actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": payload.reason, "evidence_reference": payload.evidence_reference, "lines": [item.model_dump(mode="json") for item in payload.lines]}
    detail.setdefault("origin_adoptions", []).append(adoption)
    ret.details_json = json.dumps(detail)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="IDENTIFY_RETURN_LINE_ORIGINS", entity_type="Return", entity_id=ret.id, diff=adoption)
    result = get_settlement(db, user, source.id)
    complete_request(record, result)
    db.commit()
    return result


def identify_acceptance_date(db, user, identifier, return_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.return_date:{return_id}", key, {"settlement_id": str(identifier), **payload.model_dump(mode="json")})
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    source = scoped_settlement(db, user, identifier, True)
    ret = db.scalar(select(ReturnModel).where(ReturnModel.company_id == user.company_id, ReturnModel.id == return_id).with_for_update())
    if ret is None or ret.status != "accepted":
        raise HTTPException(404, "Devolución aceptada no encontrada en la empresa activa.")
    related = db.scalar(select(CommissionEntryModel.id).where(CommissionEntryModel.company_id == user.company_id, CommissionEntryModel.settlement_id == source.id, CommissionEntryModel.sale_id == ret.sale_id).limit(1))
    if not related:
        raise HTTPException(422, "La devolución debe corresponder a una venta del detalle de la liquidación.")
    detail = json.loads(ret.details_json or "{}")
    if detail.get("accepted_at") or aware(ret.updated_at) != aware(payload.expected_updated_at):
        raise HTTPException(409, "La devolución cambió o ya tiene su aceptación identificada. Actualice la liquidación.")
    if payload.accepted_at.tzinfo is None:
        raise HTTPException(422, "La fecha debe indicar su zona horaria.")
    accepted = aware(payload.accepted_at)
    if accepted < aware(ret.created_at) or accepted > datetime.now(timezone.utc):
        raise HTTPException(422, "La aceptación debe ocurrir después de la solicitud y no puede estar en el futuro.")
    detail["accepted_at"] = accepted.isoformat()
    detail["acceptance_date_adoption"] = {"actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": payload.reason, "evidence_reference": payload.evidence_reference}
    ret.details_json = json.dumps(detail)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="IDENTIFY_RETURN_ACCEPTANCE_DATE", entity_type="Return", entity_id=ret.id, diff={"accepted_at": accepted.isoformat(), "adoption": detail["acceptance_date_adoption"], "settlement_id": str(source.id)})
    result = get_settlement(db, user, source.id)
    complete_request(record, result)
    db.commit()
    return result


def cases(db, company_id, settlement_id):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind.in_(KINDS), AnalyticsArtifact.artifact_key == str(settlement_id)).order_by(AnalyticsArtifact.created_at.desc())).all()
    return [{**json.loads(row.data_json), "id": str(row.id), "kind": row.kind, "status": row.status, "created_by": str(row.created_by), "created_at": row.created_at.isoformat()} for row in rows]


def create_case(db, user, source, kind, payload):
    version = (db.scalar(select(func.max(AnalyticsArtifact.version)).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == kind, AnalyticsArtifact.artifact_key == str(source.id))) or 0) + 1
    data = {**payload.model_dump(mode="json"), "source_settlement_id": str(source.id), "source_version": source.version, "representative_id": str(source.representative_id), "currency": getattr(payload, "currency", source.currency), "source_hash": source.calculation_hash}
    row = AnalyticsArtifact(company_id=user.company_id, kind=kind, artifact_key=str(source.id), version=version, status="pending", data_json=json.dumps(data), created_by=user.user_id)
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REQUEST_COMMISSION_REVIEW", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"kind": kind, **data})
    return row


def target_is_available(db, user, source, period):
    if period <= source.period:
        raise HTTPException(422, "El ajuste de una liquidación aprobada requiere un período posterior.")
    start, _ = period_cut(db, user.company_id, period)
    require_open_month(db, user.company_id, period, ["commissions"])
    require_open_period(db, user.company_id, business_date(db, user.company_id, start))
    closed = db.scalar(select(CommissionSettlement.id).where(CommissionSettlement.company_id == user.company_id, CommissionSettlement.representative_id == source.representative_id, CommissionSettlement.currency == source.currency, CommissionSettlement.period == period, CommissionSettlement.status.in_(("approved", "paid"))).limit(1))
    if closed:
        raise HTTPException(409, "La liquidación destino ya está aprobada. Use un período posterior aún en preparación.")


def propose_adjustment(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.adjust:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    source = scoped_settlement(db, user, identifier, True)
    if source.status not in ("approved", "paid") or source.version != payload.expected_version or source.calculation_hash is None:
        raise HTTPException(409, "El origen debe estar aprobado, conservar su versión y tener sus fuentes conciliadas.")
    target_is_available(db, user, source, payload.period)
    create_case(db, user, source, "commission_adjustment", payload)
    result = get_settlement(db, user, source.id)
    complete_request(record, result)
    db.commit()
    return result


def validate_reconciliation(db, user, source, payload):
    if source.calculation_hash is not None:
        raise HTTPException(409, "La liquidación ya conserva un detalle reconocido; no reemplace su histórico.")
    if sum((row.amount for row in payload.entries), Decimal("0")) != source.commission_amount:
        raise HTTPException(422, "El desglose debe explicar exactamente la comisión histórica registrada, sin modificar su importe.")
    duplicate = db.scalar(select(CommissionSettlement.id).where(CommissionSettlement.company_id == user.company_id, CommissionSettlement.representative_id == source.representative_id, CommissionSettlement.period == source.period, CommissionSettlement.currency == payload.currency, CommissionSettlement.id != source.id).limit(1))
    if duplicate:
        raise HTTPException(409, "Ya existe otra liquidación del vendedor en ese período y moneda; concilie sus documentos antes de adoptar el origen.")
    details = []
    for item in payload.entries:
        sale = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == item.sale_id))
        if sale is None or sale.confirmed_at is None:
            raise HTTPException(422, "Las ventas históricas deben estar identificadas y expresadas en la moneda de su comisión, con confirmación registrada.")
        if sale.currency != payload.currency and not item.conversion_reference:
            raise HTTPException(422, "Cada venta de otra moneda requiere tasa histórica y respaldo de la conversión a la moneda pagada.")
        if sale.currency == payload.currency and item.currency_rate != 1:
            raise HTTPException(422, "Una venta en la moneda de la liquidación debe conservar tasa de conversión uno.")
        if abs(sale.total_amount * item.currency_rate) >= Decimal("100000000000000"):
            raise HTTPException(422, "El valor convertido de la venta supera la precisión admitida por el libro de comisiones.")
        sale_period = business_date(db, user.company_id, sale.confirmed_at).strftime("%Y-%m")
        if sale_period > source.period:
            raise HTTPException(422, "Una liquidación histórica no puede reconocer una venta posterior a su período.")
        snapshot = freeze_commission(db, sale, historical=True)
        participant = next((row for row in snapshot["participants"] if row["representative_id"] == str(source.representative_id)), None)
        if participant is None:
            raise HTTPException(422, "El vendedor de la liquidación debe constar entre los participantes de la venta histórica.")
        details.append({"sale_id": str(sale.id), "document_number": f"{sale.series}-{sale.number:08d}", "sale_period": sale_period, "currency": payload.currency, "native_currency": sale.currency, "currency_rate": str(item.currency_rate), "conversion_reference": item.conversion_reference, "policy_version": source.rules_version, "historical_snapshot": True, "earned_on": "sale", "base": "historical_reconciled", "include_tax": True, "participant": participant, "quota": str(source.target_quota), "attainment": "0", "rate": str(item.rate), "rate_source": "historical_reconciliation", "gross": "0", "returns_deduction": "0", "net_base": str(item.recognized_base), "earned_base": str(rounded(item.recognized_base * item.currency_rate)), "native_earned_base": str(item.recognized_base), "cumulative_amount": str(item.amount), "baseline_amount": "0", "previously_recognized": "0", "amount": str(item.amount), "lines": [], "receipts": [], "returns": []})
    return details


def propose_reconciliation(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.reconcile:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    source = scoped_settlement(db, user, identifier, True)
    if source.version != payload.expected_version or source.status not in ("approved", "paid"):
        raise HTTPException(409, "La adopción histórica requiere una liquidación aprobada con versión vigente. Los borradores se corrigen mediante recálculo.")
    validate_reconciliation(db, user, source, payload)
    create_case(db, user, source, "commission_reconciliation", payload)
    result = get_settlement(db, user, source.id)
    complete_request(record, result)
    db.commit()
    return result


def review_case(db, user, identifier, case_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.case:{case_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    source = scoped_settlement(db, user, identifier, True)
    case = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.id == case_id, AnalyticsArtifact.artifact_key == str(source.id), AnalyticsArtifact.kind.in_(KINDS)).with_for_update())
    if case is None:
        raise HTTPException(404, "Solicitud de conciliación o ajuste no encontrada.")
    rep = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.id == source.representative_id))
    if case.created_by == user.user_id or rep.user_id == user.user_id:
        raise HTTPException(403, "La solicitud debe revisarla otra persona autorizada distinta del vendedor.")
    if case.status != "pending" or source.version != payload.expected_version:
        raise HTTPException(409, "La solicitud o la liquidación cambiaron. Consulte su estado vigente.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, user, "commission_correction", [case.created_by, rep.user_id], "AnalyticsArtifact", case.id)
    data = json.loads(case.data_json)
    if payload.approve:
        if data["source_version"] != source.version or data["source_hash"] != source.calculation_hash:
            raise HTTPException(409, "El origen cambió desde la solicitud. Rechace la solicitud desactualizada y prepare otra con los datos vigentes.")
        if case.kind == "commission_adjustment":
            target_is_available(db, user, source, data["period"])
        else:
            request = HistoricalReconciliationRequest.model_validate(data)
            entries = validate_reconciliation(db, user, source, request)
            history(source, user, "reconcile_legacy", payload.reason, {"currency": source.currency, "calculation": json.loads(source.calculation_detail_json), "rules": json.loads(source.rules_snapshot_json)})
            source.currency = request.currency
            for item in entries:
                db.add(CommissionEntryModel(company_id=user.company_id, settlement_id=source.id, sale_id=UUID(item["sale_id"]), currency=source.currency, amount=Decimal(item["amount"]), earned_base=Decimal(item["earned_base"]), cumulative_amount=Decimal(item["cumulative_amount"]), details_json=json.dumps(item)))
            adopted = {"schema": 2, "legacy_reconciled": True, "entries": entries, "warnings": [], "reconciliation": {"case_id": str(case.id), "evidence_reference": request.evidence_reference, "reason": request.reason, "review_reason": payload.reason}, "rules": {"legacy": "Los totales agregados históricos se conservan. La conciliación acredita la moneda y el desglose de la comisión realmente reconocida, sin recalcular ni volver a pagar su importe."}}
            source.calculation_detail_json = json.dumps(adopted)
            source.calculation_hash = hashlib.sha256(json.dumps(adopted, sort_keys=True).encode()).hexdigest()
            source.version += 1
        case.status = "approved"
    else:
        case.status = "rejected"
    data["review"] = {"actor": user.email, "actor_id": str(user.user_id), "reason": payload.reason, "at": datetime.now(timezone.utc).isoformat()}
    case.data_json = json.dumps(data)
    case.updated_at = datetime.now(timezone.utc)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REVIEW_COMMISSION_CORRECTION", entity_type="AnalyticsArtifact", entity_id=case.id, diff={"kind": case.kind, "status": case.status, "source_settlement_id": str(source.id), "review": data["review"]})
    result = get_settlement(db, user, source.id)
    complete_request(record, result)
    db.commit()
    return result
