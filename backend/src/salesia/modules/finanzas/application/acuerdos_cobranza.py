import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentModel, PaymentReversalModel, TransferProofModel
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact, CollaborationTask
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import SaleModel
from salesia.shared.infrastructure.transactions import RefundModel, claim_request, complete_request


class AgreementChange(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)
    promised_amount: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=6)
    due_at: datetime | None = None


def aware(value):
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result


def applications(db, company_id, sale_id, currency):
    db.flush()
    target_ids = db.scalars(select(PaymentAllocationModel.payment_id).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.sale_id == sale_id)).all()
    proofs = db.scalars(select(TransferProofModel).join(PaymentModel, PaymentModel.id == TransferProofModel.payment_id).where(TransferProofModel.company_id == company_id, PaymentModel.company_id == company_id, PaymentModel.sale_id == sale_id, TransferProofModel.verified.is_(True))).all()
    proof_by_payment = {row.payment_id: row for row in proofs}
    identifiers = set(target_ids) | set(proof_by_payment)
    if not identifiers:
        return []
    payments = db.scalars(select(PaymentModel).where(PaymentModel.company_id == company_id, PaymentModel.id.in_(identifiers), PaymentModel.currency == currency, PaymentModel.status == "confirmed")).all()
    allocations = db.scalars(select(PaymentAllocationModel).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.payment_id.in_(identifiers)).order_by(PaymentAllocationModel.created_at, PaymentAllocationModel.id)).all()
    refunds = db.scalars(select(RefundModel).where(RefundModel.company_id == company_id, RefundModel.payment_id.in_(identifiers), RefundModel.status == "confirmed", RefundModel.unapplied_only.is_(False))).all()
    reversals = db.scalars(select(PaymentReversalModel).where(PaymentReversalModel.company_id == company_id, PaymentReversalModel.payment_id.in_(identifiers))).all()
    deducted = defaultdict(lambda: Decimal("0"))
    for row in [*refunds, *reversals]:
        deducted[row.payment_id] += row.amount
    grouped = defaultdict(list)
    for row in allocations:
        grouped[row.payment_id].append(row)
    results = []
    for payment in payments:
        available = max(Decimal("0"), payment.amount - deducted[payment.id])
        proof = proof_by_payment.get(payment.id)
        verified_at = aware(proof.verified_at) if proof and proof.verified_at else aware(payment.created_at)
        for allocation in grouped[payment.id]:
            used = min(available, allocation.allocated_amount)
            available -= used
            if allocation.sale_id == sale_id and used > 0:
                results.append({"id": str(allocation.id), "payment_id": str(payment.id), "amount": used, "at": max(aware(allocation.created_at), verified_at), "reference": payment.reference_code or "Cobro confirmado", "method": payment.payment_method})
        if not grouped[payment.id] and proof and payment.sale_id == sale_id and available > 0:
            results.append({"id": str(payment.id), "payment_id": str(payment.id), "amount": available, "at": verified_at, "reference": payment.reference_code or "Transferencia verificada", "method": payment.payment_method})
    return sorted(results, key=lambda item: (item["at"], item["id"]))


def evaluate(data, receipts, now=None):
    if data.get("status") in ("renegotiated", "cancelled"):
        return data
    current = now or datetime.now(timezone.utc)
    start, due = aware(data["started_at"]), aware(data["due_at"])
    target = Decimal(data["promised_amount"])
    until = min(current, aware(data["evaluation_end_at"])) if data.get("evaluation_end_at") else current
    selected = [item for item in receipts if item.get("method") not in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT") and start <= item["at"] <= current and (not data.get("evaluation_end_at") or item["at"] < until)]
    paid = sum((item["amount"] for item in selected), Decimal("0"))
    on_time = sum((item["amount"] for item in selected if item["at"] <= due), Decimal("0"))
    status = "fulfilled" if paid >= target else "broken" if current > due else "partial" if paid > 0 else "pending"
    fulfilled_at, accumulated = None, Decimal("0")
    for item in selected:
        accumulated += item["amount"]
        if accumulated >= target:
            fulfilled_at = item["at"].isoformat()
            break
    return {**data, "status": status, "applied_amount": str(min(paid, target)), "remaining_amount": str(max(Decimal("0"), target - paid)), "paid_on_time": str(min(on_time, target)), "fulfilled_at": fulfilled_at, "fulfilled_late": bool(fulfilled_at and aware(fulfilled_at) > due), "overdue": current > due and paid < target, "applications": [{**item, "amount": str(item["amount"]), "at": item["at"].isoformat()} for item in selected], "calculated_at": current.isoformat()}


def initial_data(activity, currency, identifier=None):
    return {"id": str(identifier or activity["id"]), "source_activity_id": activity["id"], "kind": activity["kind"], "currency": currency, "promised_amount": activity["promised_amount"], "due_at": activity["next_action_at"], "started_at": activity["created_at"], "notes": activity["notes"], "responsible": activity["responsible"], "status": "pending", "version": 1, "history": [], "legacy": identifier is None}


def all_agreements(db, user, sale):
    receipts = applications(db, user.company_id, sale.id, sale.currency)
    records = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.artifact_key == str(sale.id), AnalyticsArtifact.kind.in_(("collection_activity", "collection_agreement"))).order_by(AnalyticsArtifact.created_at)).all()
    agreements, adopted = [], set()
    for row in records:
        if row.kind == "collection_agreement":
            data = json.loads(row.data_json)
            adopted.add(data.get("source_activity_id"))
            agreements.append(data)
    for row in records:
        data = json.loads(row.data_json)
        if row.kind == "collection_activity" and data.get("kind") in ("promise", "agreement") and data.get("promised_amount") and data.get("next_action_at") and str(row.id) not in adopted:
            agreements.append(initial_data(data, sale.currency))
    ordered = sorted(agreements, key=lambda item: (aware(item["started_at"]), item["id"]))
    for index, data in enumerate(ordered):
        if index + 1 < len(ordered):
            data["evaluation_end_at"] = ordered[index + 1]["started_at"]
    return [evaluate(data, receipts) for data in reversed(ordered)]


def artifact_sequence(db, user, sale_id):
    db.flush()
    return (db.scalar(select(func.max(AnalyticsArtifact.version)).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.artifact_key == str(sale_id))) or 0) + 1


def register_activity_agreement(db, user, sale, activity):
    existing = all_agreements(db, user, sale)
    if any(row["status"] not in ("fulfilled", "renegotiated", "cancelled") for row in existing):
        raise HTTPException(409, "La deuda tiene un compromiso pendiente o incumplido. Renegocia el acuerdo anterior para conservar su historial y evitar contar un cobro en dos compromisos.")
    identifier = uuid4()
    data = initial_data(activity, sale.currency, identifier)
    task = CollaborationTask(id=uuid4(), company_id=user.company_id, title=f"Compromiso de cobro {sale.series}-{sale.number:08d}", description=activity["notes"], creator_id=user.user_id, assignee_id=user.user_id, due_date=aware(activity["next_action_at"]), priority="high", resource_type="sale", resource_id=sale.id, status="pending", version=1)
    data["task_id"] = str(task.id)
    db.add(task)
    db.add(AnalyticsArtifact(id=identifier, company_id=user.company_id, kind="collection_agreement", artifact_key=str(sale.id), version=artifact_sequence(db, user, sale.id), status="pending", data_json=json.dumps(data), created_by=user.user_id))
    return data


def synchronize_agreements(db, user, sale_id):
    db.flush()
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == sale_id))
    if sale is None:
        return
    calculated = {item["id"]: item for item in all_agreements(db, user, sale)}
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.artifact_key == str(sale.id), AnalyticsArtifact.status.notin_(("renegotiated", "cancelled"))).with_for_update()).all()
    for row in rows:
        data = json.loads(row.data_json)
        evaluated = calculated[str(row.id)]
        if data.get("status") == evaluated["status"] and data.get("applied_amount", "0") == evaluated["applied_amount"]:
            continue
        history = data.get("history", [])
        history.append({"action": "EVALUATED", "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "before": data.get("status"), "status": evaluated["status"], "applied_amount": evaluated["applied_amount"]})
        evaluated["history"], evaluated["version"] = history, data.get("version", 1) + 1
        task = db.scalar(select(CollaborationTask).where(CollaborationTask.company_id == user.company_id, CollaborationTask.id == UUID(data["task_id"]))) if data.get("task_id") else None
        if task and evaluated["status"] == "fulfilled" and task.status != "done":
            task.status, task.resolution_notes, task.version = "done", "Compromiso cumplido mediante aplicaciones confirmadas de cobros.", task.version + 1
        elif task and evaluated["status"] != "fulfilled" and task.status == "done":
            task.status, task.resolution_notes, task.version = "pending", "El compromiso volvió a tener saldo tras revisar sus cobros efectivos.", task.version + 1
        row.data_json, row.status = json.dumps(evaluated), evaluated["status"]
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="EVALUATE_COLLECTION_AGREEMENT", entity_type="Sale", entity_id=sale.id, diff={"agreement_id": str(row.id), "status": evaluated["status"], "applied_amount": evaluated["applied_amount"]})


def synchronize_company_agreements(db, user):
    sale_ids = db.scalars(select(AnalyticsArtifact.artifact_key).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.status.notin_(("renegotiated", "cancelled"))).distinct()).all()
    for identifier in sale_ids:
        synchronize_agreements(db, user, UUID(identifier))


def change_agreement(db, user, sale_id, identifier, action, payload, key):
    record, cached = claim_request(db, user.company_id, f"collection_agreement.{action}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == sale_id).with_for_update())
    if sale is None:
        raise HTTPException(404, "La cuenta por cobrar no existe en la empresa activa.")
    agreements = all_agreements(db, user, sale)
    data = next((item for item in agreements if item["id"] == str(identifier)), None)
    if data is None:
        raise HTTPException(404, "Acuerdo de pago no encontrado.")
    if data["version"] != payload.version or data["status"] in ("renegotiated", "cancelled"):
        raise HTTPException(409, "El acuerdo cambió o ya fue reemplazado o cancelado.")
    if action == "renegotiate" and data["status"] == "fulfilled":
        raise HTTPException(409, "El compromiso ya se cumplió; registra un nuevo compromiso para el saldo restante.")
    if action == "renegotiate":
        if any(item["id"] != data["id"] and item["status"] not in ("fulfilled", "renegotiated", "cancelled") for item in agreements):
            raise HTTPException(409, "Resuelve primero los compromisos históricos superpuestos; no se puede contar el mismo cobro en dos acuerdos vigentes.")
        if payload.promised_amount is None or payload.due_at is None or payload.due_at.tzinfo is None or payload.due_at <= datetime.now(timezone.utc):
            raise HTTPException(422, "Indica un importe y vencimiento futuro con zona horaria para la renegociación.")
        if sale.status not in ("confirmed", "paid") or payload.promised_amount > sale.total_amount - sale.paid_amount:
            raise HTTPException(409, "El nuevo compromiso supera el saldo pendiente real.")
    if data.get("legacy"):
        row = AnalyticsArtifact(id=uuid4(), company_id=user.company_id, kind="collection_agreement", artifact_key=str(sale.id), version=artifact_sequence(db, user, sale.id), status=data["status"], created_by=user.user_id)
        data["id"], data["legacy"] = str(row.id), False
        db.add(row)
    else:
        row = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.id == identifier).with_for_update())
    old_task = db.scalar(select(CollaborationTask).where(CollaborationTask.company_id == user.company_id, CollaborationTask.id == UUID(data["task_id"]))) if data.get("task_id") else None
    if old_task and old_task.status not in ("done", "cancelled"):
        old_task.status, old_task.resolution_notes, old_task.version = "cancelled", payload.reason, old_task.version + 1
    replacement_id = uuid4() if action == "renegotiate" else None
    data["status"], data["version"] = "renegotiated" if replacement_id else "cancelled", data["version"] + 1
    data.setdefault("history", []).append({"action": action.upper(), "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": payload.reason, "applied_amount": data["applied_amount"]})
    data["replacement_id"] = str(replacement_id) if replacement_id else None
    row.data_json, row.status = json.dumps(data), data["status"]
    if replacement_id:
        now = datetime.now(timezone.utc).isoformat()
        replacement = {"id": str(replacement_id), "source_activity_id": None, "kind": data["kind"], "currency": sale.currency, "promised_amount": str(payload.promised_amount), "due_at": payload.due_at.isoformat(), "started_at": now, "notes": payload.reason, "responsible": user.email, "status": "pending", "version": 1, "history": [], "legacy": False, "previous_id": data["id"]}
        task_id = uuid4()
        replacement["task_id"] = str(task_id)
        db.add(AnalyticsArtifact(id=replacement_id, company_id=user.company_id, kind="collection_agreement", artifact_key=str(sale.id), version=artifact_sequence(db, user, sale.id), status="pending", data_json=json.dumps(replacement), created_by=user.user_id))
        db.add(CollaborationTask(id=task_id, company_id=user.company_id, title=f"Acuerdo renegociado {sale.series}-{sale.number:08d}", description=f'{payload.reason}\nCompromiso {sale.currency} {payload.promised_amount}.', creator_id=user.user_id, assignee_id=user.user_id, due_date=payload.due_at, priority="high", resource_type="sale", resource_id=sale.id, status="pending"))
    db.flush()
    result = {"items": all_agreements(db, user, sale)}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="CHANGE_COLLECTION_AGREEMENT", entity_type="Sale", entity_id=sale.id, diff={"agreement_id": data["id"], "action": action, "reason": payload.reason, "replacement_id": data["replacement_id"]})
    complete_request(record, result)
    db.commit()
    return result


def process_collection_agreements(limit=100):
    from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
    from salesia.shared.infrastructure.database import sync_session_factory
    from salesia.shared.infrastructure.models import CompanyModel
    from salesia.shared.infrastructure.tenant_scope import bind_company
    candidates = []
    with sync_session_factory() as db:
        companies = db.scalars(select(CompanyModel.id).where(CompanyModel.is_active.is_(True))).all()
    for company_id in companies:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            rows = db.execute(select(AnalyticsArtifact.artifact_key, func.min(AnalyticsArtifact.updated_at).label("last_checked")).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.status.notin_(("renegotiated", "cancelled"))).group_by(AnalyticsArtifact.artifact_key).order_by(func.min(AnalyticsArtifact.updated_at), AnalyticsArtifact.artifact_key).limit(limit)).all()
            candidates.extend((aware(last_checked), company_id, sale_key) for sale_key, last_checked in rows)
    processed = 0
    for _, company_id, sale_key in sorted(candidates, key=lambda value: (value[0], str(value[1]), value[2]))[:limit]:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            agreement = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.artifact_key == sale_key).order_by(AnalyticsArtifact.created_at.desc()).limit(1))
            if agreement is None or agreement.created_by is None:
                continue
            actor = AuthenticatedUser(user_id=agreement.created_by, email="Sistema: evaluación automática de compromisos", company_id=company_id, role="system", permissions=[])
            synchronize_agreements(db, actor, UUID(sale_key))
            records = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "collection_agreement", AnalyticsArtifact.artifact_key == sale_key, AnalyticsArtifact.status.notin_(("renegotiated", "cancelled")))).all()
            for record in records:
                record.updated_at = datetime.now(timezone.utc)
            db.commit()
            processed += 1
    return processed
