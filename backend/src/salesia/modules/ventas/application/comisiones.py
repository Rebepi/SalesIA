import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import String, delete, func, or_, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.organizacion.application.periodos import business_date, require_open_month, require_open_period
from salesia.modules.ventas.application.auxiliares.settlement_response import settlement_response
from salesia.modules.ventas.application.motor_comisiones import calculate_details, period_cut
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionEntryModel, CommissionObservationModel, CommissionSettlement, SalesRepresentative
from salesia.shared.infrastructure.models import CompanyModel, CustomerModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def scoped_settlement(db, user, identifier, lock=False):
    query = select(CommissionSettlement).where(CommissionSettlement.company_id == user.company_id, CommissionSettlement.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Liquidación no encontrada en la empresa activa.")
    if "organization:manage" not in user.permissions:
        rep = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.id == row.representative_id, SalesRepresentative.user_id == user.user_id))
        if rep is None:
            raise HTTPException(403, "Solo puede consultar y observar sus propias liquidaciones.")
    return row


def history(row, user, action, reason, previous=None):
    events = json.loads(row.history_json or "[]")
    events.append({"version": row.version, "action": action, "reason": reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "previous": previous})
    row.history_json = json.dumps(events)


def calculate_commissions(req, current_user, db):
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    representative = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == current_user.company_id, SalesRepresentative.id == req.rep_id))
    if representative is None:
        raise HTTPException(404, "Vendedor no encontrado en la empresa activa.")
    currency = req.currency or db.scalar(select(CompanyModel.base_currency).where(CompanyModel.id == current_user.company_id))
    period_cut(db, current_user.company_id, req.period)
    row = db.scalar(select(CommissionSettlement).where(CommissionSettlement.company_id == current_user.company_id, CommissionSettlement.representative_id == req.rep_id, CommissionSettlement.period == req.period, CommissionSettlement.currency == currency).with_for_update())
    if row and not req.recalculate:
        return get_settlement(db, current_user, row.id)
    require_open_month(db, current_user.company_id, req.period, ["commissions"])
    if row and (row.status not in ("calculated", "cancelled") or row.version != req.expected_version or not req.reason):
        raise HTTPException(409, "Solo puede recalcular una liquidación no aprobada, con versión vigente y motivo.")
    later = db.scalar(select(CommissionSettlement.id).where(CommissionSettlement.company_id == current_user.company_id, CommissionSettlement.representative_id == req.rep_id, CommissionSettlement.currency == currency, CommissionSettlement.period > req.period, CommissionSettlement.status.in_(("approved", "paid"))).limit(1))
    if later:
        raise HTTPException(409, "Hay liquidaciones posteriores aprobadas. Registre correcciones en un período posterior sin reabrir el histórico.")
    data, digest = calculate_details(db, current_user, representative, req.period, currency)
    if row:
        previous = {"calculation": json.loads(row.calculation_detail_json), "hash": row.calculation_hash}
        history(row, current_user, "recalculate", req.reason, previous)
        row.version += 1
        row.status = "calculated"
        db.execute(delete(CommissionEntryModel).where(CommissionEntryModel.company_id == current_user.company_id, CommissionEntryModel.settlement_id == row.id))
    else:
        row = CommissionSettlement(company_id=current_user.company_id, representative_id=req.rep_id, period=req.period, currency=currency, version=1, status="calculated", created_by=current_user.user_id)
        db.add(row)
    row.gross_sales = Decimal(data["gross"])
    row.returns_amount = Decimal(data["returns"])
    row.prior_adjustments = sum((Decimal(item["amount"]) for item in data["entries"] if item["sale_period"] < req.period), Decimal("0")) + sum((Decimal(item["amount"]) for item in data.get("manual_adjustments", [])), Decimal("0"))
    row.net_sales = Decimal(data["earned_base"])
    row.target_quota = representative.monthly_quota or Decimal("0")
    rates = {Decimal(item["rate"]) for item in data["entries"]}
    row.commission_rate = next(iter(rates)) if len(rates) == 1 else Decimal("0")
    row.commission_amount = Decimal(data["commission_amount"])
    row.payable_amount = Decimal(data["payable_amount"])
    row.carried_balance = Decimal(data["carried_balance"])
    row.rules_version = max((int(version) for version in data["policies"]), default=1)
    row.rules_snapshot_json = json.dumps(data["policies"])
    row.calculation_detail_json = json.dumps(data)
    row.calculation_hash = digest
    if any(abs(value) >= Decimal("100000000000000") for value in (row.gross_sales, row.returns_amount, row.prior_adjustments, row.net_sales, row.target_quota, row.commission_amount, row.payable_amount, row.carried_balance)):
        raise HTTPException(422, "Los importes acumulados superan la precisión del libro de comisiones.")
    db.flush()
    for item in data["entries"]:
        db.add(CommissionEntryModel(company_id=current_user.company_id, settlement_id=row.id, sale_id=UUID(item["sale_id"]), currency=currency, amount=Decimal(item["amount"]), earned_base=Decimal(item["earned_base"]), cumulative_amount=Decimal(item["cumulative_amount"]), details_json=json.dumps(item)))
    if not req.recalculate:
        history(row, current_user, "calculate", req.reason or "Cálculo desde operaciones registradas")
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="CALCULATE_COMMISSION", entity_type="CommissionSettlement", entity_id=row.id, diff={"period": req.period, "currency": currency, "version": row.version, "amount": str(row.commission_amount), "hash": digest, "reason": req.reason})
    db.commit()
    return get_settlement(db, current_user, row.id)


def get_settlement(db, user, identifier):
    row = scoped_settlement(db, user, identifier)
    result = settlement_response(row)
    from salesia.modules.ventas.application.conciliacion_comisiones import cases
    result["correction_requests"] = cases(db, user.company_id, row.id)
    observations = db.scalars(select(CommissionObservationModel).where(CommissionObservationModel.company_id == user.company_id, CommissionObservationModel.settlement_id == row.id).order_by(CommissionObservationModel.created_at)).all()
    result["observations"] = [{"id": str(item.id), "sale_id": str(item.sale_id) if item.sale_id else None, "reason": item.reason, "status": item.status, "version": item.version, "created_by": str(item.created_by), "resolved_by": str(item.resolved_by) if item.resolved_by else None, "resolution": item.resolution, "created_at": item.created_at.isoformat()} for item in observations]
    return result


def discard_settlement(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.discard:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = scoped_settlement(db, user, identifier, True)
    if row.status != "calculated" or row.version != payload.expected_version:
        raise HTTPException(409, "Solo puede descartar una liquidación aún no aprobada con versión vigente.")
    row.status = "cancelled"
    row.version += 1
    history(row, user, "discard", payload.reason)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="DISCARD_COMMISSION", entity_type="CommissionSettlement", entity_id=row.id, diff={"version": row.version, "reason": payload.reason})
    result = get_settlement(db, user, row.id)
    complete_request(record, result)
    db.commit()
    return result


def list_settlements(db, user, representative_id=None, period=None, currency=None, limit=25, offset=0):
    query = select(CommissionSettlement).where(CommissionSettlement.company_id == user.company_id)
    if "organization:manage" not in user.permissions:
        identifiers = select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == user.user_id)
        query = query.where(CommissionSettlement.representative_id.in_(identifiers))
    if representative_id:
        query = query.where(CommissionSettlement.representative_id == representative_id)
    if period:
        query = query.where(CommissionSettlement.period == period)
    if currency:
        query = query.where(CommissionSettlement.currency == currency)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(CommissionSettlement.period.desc(), CommissionSettlement.id).limit(limit).offset(offset)).all()
    return {"total_count": total, "items": [settlement_response(row) for row in rows]}


def sale_options(db, user, search=None, status=None, limit=20, offset=0):
    query = select(SaleModel).join(CustomerModel, CustomerModel.id == SaleModel.customer_id).where(SaleModel.company_id == user.company_id, CustomerModel.company_id == user.company_id)
    if user.role == "salesperson" and "organization:manage" not in user.permissions:
        rep = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == user.user_id))
        if rep is None:
            return {"items": [], "total_count": 0}
        query = query.where(or_(SaleModel.sales_rep_id == rep.id, SaleModel.commission_snapshot_json.contains(str(rep.id))))
    if status:
        query = query.where(SaleModel.status == status)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(SaleModel.series.ilike(term) | SaleModel.number.cast(String).ilike(term) | CustomerModel.legal_name.ilike(term) | SaleModel.id.cast(String).ilike(term))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(SaleModel.created_at.desc(), SaleModel.id).limit(limit).offset(offset)).all()
    return {"total_count": total, "items": [{"sale_id": str(row.id), "id": str(row.id), "document_number": f"{row.series}-{row.number:08d}", "currency": row.currency, "status": row.status, "version": row.version} for row in rows]}


def approve_commission_settlement(settlement_id, payload, current_user, db, idempotency_key):
    record, cached = claim_request(db, current_user.company_id, f"commission.approve:{settlement_id}", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    row = scoped_settlement(db, current_user, settlement_id, True)
    rep = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == current_user.company_id, SalesRepresentative.id == row.representative_id))
    if rep.user_id == current_user.user_id or row.created_by == current_user.user_id:
        raise HTTPException(403, "La revisión debe realizarla una persona distinta del vendedor y de quien calculó la liquidación.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, current_user, "commission", [rep.user_id, row.created_by], "CommissionSettlement", row.id)
    if row.status != "calculated" or row.version != payload.expected_version:
        raise HTTPException(409, "La liquidación cambió o ya fue aprobada.")
    require_open_month(db, current_user.company_id, row.period, ["commissions"])
    if db.scalar(select(CommissionSettlement.id).where(CommissionSettlement.company_id == current_user.company_id, CommissionSettlement.representative_id == row.representative_id, CommissionSettlement.currency == row.currency, CommissionSettlement.period > row.period, CommissionSettlement.status.in_(("approved", "paid"))).limit(1)):
        raise HTTPException(409, "Existen liquidaciones posteriores aprobadas. Las correcciones deben incorporarse en otro período.")
    if db.scalar(select(CommissionSettlement.id).where(CommissionSettlement.company_id == current_user.company_id, CommissionSettlement.representative_id == row.representative_id, CommissionSettlement.currency == row.currency, CommissionSettlement.period < row.period, CommissionSettlement.status == "calculated").limit(1)):
        raise HTTPException(409, "Primero apruebe o descarte las liquidaciones anteriores aún en revisión.")
    if db.scalar(select(CommissionObservationModel.id).where(CommissionObservationModel.company_id == current_user.company_id, CommissionObservationModel.settlement_id == row.id, CommissionObservationModel.status == "open").limit(1)):
        raise HTTPException(409, "Resuelva las observaciones antes de aprobar la liquidación.")
    data, digest = calculate_details(db, current_user, rep, row.period, row.currency)
    if data["warnings"]:
        raise HTTPException(409, " ".join(data["warnings"]))
    if digest != row.calculation_hash:
        raise HTTPException(409, "Los documentos, metas o liquidaciones previas cambiaron. Recalcule y revise la diferencia antes de aprobar.")
    row.status = "approved"
    row.approved_by = current_user.user_id
    row.version += 1
    from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
    for adjustment in data.get("manual_adjustments", []):
        artifact = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.id == UUID(adjustment["id"])).with_for_update())
        values = json.loads(artifact.data_json)
        if values.get("used_settlement_id") and values["used_settlement_id"] != str(row.id):
            raise HTTPException(409, "El ajuste ya fue reconocido en otra liquidación.")
        values["used_settlement_id"] = str(row.id)
        artifact.data_json = json.dumps(values)
    history(row, current_user, "approve", payload.reason)
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="APPROVE_COMMISSION", entity_type="CommissionSettlement", entity_id=row.id, diff={"version": row.version, "hash": digest, "reason": payload.reason})
    result = get_settlement(db, current_user, row.id)
    complete_request(record, result)
    db.commit()
    return result


def pay_commission_settlement(settlement_id, payload, current_user, db, idempotency_key):
    record, cached = claim_request(db, current_user.company_id, f"commission.pay:{settlement_id}", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    row = scoped_settlement(db, current_user, settlement_id, True)
    if row.status != "approved" or row.version != payload.expected_version:
        raise HTTPException(409, "La liquidación debe estar aprobada y conservar su versión vigente.")
    if row.payable_amount > 0 and (not payload.payout_reference or len(payload.payout_reference.strip()) < 3):
        raise HTTPException(422, "Registre la referencia del pago real de la comisión.")
    if db.scalar(select(CommissionObservationModel.id).where(CommissionObservationModel.company_id == current_user.company_id, CommissionObservationModel.settlement_id == row.id, CommissionObservationModel.status == "open").limit(1)):
        raise HTTPException(409, "Resuelva las observaciones antes de registrar el pago.")
    row.status = "paid"
    row.paid_at = datetime.now(timezone.utc)
    row.payout_reference = payload.payout_reference.strip() if payload.payout_reference else None
    row.version += 1
    history(row, current_user, "pay" if row.payable_amount > 0 else "carry_forward", payload.reason)
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="PAY_COMMISSION", entity_type="CommissionSettlement", entity_id=row.id, diff={"payable_amount": str(row.payable_amount), "carried_balance": str(row.carried_balance), "currency": row.currency, "reference": row.payout_reference, "reason": payload.reason})
    result = get_settlement(db, current_user, row.id)
    complete_request(record, result)
    db.commit()
    return result


def observe(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.observe:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = scoped_settlement(db, user, identifier, True)
    if row.version != payload.expected_version:
        raise HTTPException(409, "La liquidación cambió. Consulte sus datos antes de observarla.")
    if payload.sale_id and not db.scalar(select(CommissionEntryModel.id).where(CommissionEntryModel.company_id == user.company_id, CommissionEntryModel.settlement_id == row.id, CommissionEntryModel.sale_id == payload.sale_id)):
        raise HTTPException(422, "La venta observada no pertenece al detalle de esta liquidación.")
    observation = CommissionObservationModel(company_id=user.company_id, settlement_id=row.id, sale_id=payload.sale_id, created_by=user.user_id, reason=payload.reason, status="open", version=1)
    db.add(observation)
    db.flush()
    row.version += 1
    history(row, user, "observe", payload.reason)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="OBSERVE_COMMISSION", entity_type="CommissionObservation", entity_id=observation.id, diff={"settlement_id": str(row.id), "reason": payload.reason, "sale_id": str(payload.sale_id) if payload.sale_id else None})
    result = get_settlement(db, user, row.id)
    complete_request(record, result)
    db.commit()
    return result


def resolve_observation(db, user, identifier, observation_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"commission.resolve:{observation_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = scoped_settlement(db, user, identifier, True)
    observation = db.scalar(select(CommissionObservationModel).where(CommissionObservationModel.company_id == user.company_id, CommissionObservationModel.id == observation_id, CommissionObservationModel.settlement_id == row.id).with_for_update())
    if observation is None:
        raise HTTPException(404, "Observación no encontrada en esta liquidación.")
    if observation.created_by == user.user_id:
        raise HTTPException(403, "La observación debe resolverla otra persona autorizada.")
    if observation.version != payload.expected_version or observation.status != "open":
        raise HTTPException(409, "La observación cambió o ya fue resuelta.")
    observation.status = payload.action
    observation.version += 1
    observation.resolved_by = user.user_id
    observation.resolution = payload.resolution
    row.version += 1
    history(row, user, "resolve_observation", payload.resolution)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="RESOLVE_COMMISSION_OBSERVATION", entity_type="CommissionObservation", entity_id=observation.id, diff={"settlement_id": str(row.id), "status": observation.status, "resolution": payload.resolution})
    result = get_settlement(db, user, row.id)
    complete_request(record, result)
    db.commit()
    return result
