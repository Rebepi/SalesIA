import json
from datetime import date, datetime, timedelta, timezone
from salesia.modules.organizacion.application.periodos import business_date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.inventario.infrastructure_models import PurchaseInvoiceMatch, Supplier, SupplyDocument
from salesia.modules.operaciones.application.recursos import entity_statement
from salesia.modules.operaciones.infrastructure_models import CollaborationTask
from salesia.modules.organizacion.application.politicas import effective_policy
from salesia.shared.infrastructure.models import CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def aware(moment):
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


def rate(numerator, denominator):
    return min(Decimal("100"), max(Decimal("0"), numerator / denominator * 100)).quantize(Decimal("0.01")) if denominator else None


def supplier_performance(db, user, identifier):
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == identifier))
    if supplier is None:
        raise HTTPException(404, "Proveedor no encontrado.")
    policy = effective_policy(db, user.company_id, "supplier_performance_policy")
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(policy.get("history_days", 365)))
    orders = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.supplier_id == identifier, SupplyDocument.kind == "PURCHASE_ORDER", SupplyDocument.supplier_claim_id.is_(None), SupplyDocument.status.in_(("approved", "partially_received", "received", "closed")), SupplyDocument.created_at >= cutoff)).all()
    ordered, received, accepted, damaged, on_time, dated = [Decimal("0") for _ in range(6)]
    samples = []
    for order in orders:
        ordered += sum((max(Decimal("0"), line.quantity - line.cancelled_quantity) for line in order.lines), Decimal("0"))
        details = json.loads(order.details_json or "{}")
        promise = details.get("delivery_date")
        promised = (date.fromisoformat(promise) if len(promise) == 10 else business_date(db, user.company_id, datetime.fromisoformat(promise))) if promise else None
        receipts = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "GOODS_RECEIPT", SupplyDocument.parent_id == order.id)).all()
        for receipt in receipts:
            inspections = {item["product_id"]: item for item in json.loads(receipt.details_json or "{}").get("inspections", [])}
            for line in receipt.lines:
                inspection = inspections.get(str(line.product_id), {})
                state = inspection.get("status", receipt.status)
                good = state == "accepted" or inspection.get("resolution") == "RESTOCK"
                quantity = line.quantity
                received += quantity
                accepted += quantity if good else Decimal("0")
                damaged += quantity if state == "rejected" else Decimal("0")
                timely = business_date(db, user.company_id, receipt.created_at) <= promised if promised else None
                if timely is not None:
                    dated += quantity
                    on_time += quantity if timely else Decimal("0")
                samples.append({"receipt_id": str(receipt.id), "product_id": str(line.product_id), "purchase_order_id": str(order.id), "promised_date": promised.isoformat() if promised else None, "actual_date": receipt.created_at.isoformat(), "is_on_time": timely, "ordered_quantity": str(next(item.quantity - item.cancelled_quantity for item in order.lines if item.product_id == line.product_id)), "received_quantity": str(quantity), "accepted_quantity": str(quantity if good else 0), "rejected_quantity": str(quantity if state == "rejected" else 0), "inspection_status": state})
    matches = db.scalars(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.purchase_order_id.in_([order.id for order in orders]), PurchaseInvoiceMatch.status != "VOIDED")).all() if orders else []
    matches = [match for match in matches if json.loads(match.lines_snapshot_json or "[]")]
    indicators = {"on_time": rate(on_time, dated), "fill": rate(received, ordered), "acceptance": rate(accepted, received), "invoice": rate(Decimal(sum(1 for item in matches if item.status == "MATCHED")), Decimal(len(matches)))}
    weights = {"on_time": Decimal(str(policy.get("on_time_weight", 35))), "fill": Decimal(str(policy.get("fill_weight", 25))), "acceptance": Decimal(str(policy.get("acceptance_weight", 25))), "invoice": Decimal(str(policy.get("invoice_weight", 15)))}
    usable = {key: value for key, value in indicators.items() if value is not None and weights[key] > 0}
    sufficient = len(samples) >= int(policy.get("minimum_samples", 3))
    score = sum((value * weights[key] for key, value in usable.items()), Decimal("0")) / sum((weights[key] for key in usable), Decimal("0")) if usable and sufficient else None
    tasks = db.scalars(entity_statement("task", user).where(CollaborationTask.resource_type == "supplier", CollaborationTask.resource_id == identifier).order_by(CollaborationTask.created_at.desc())).all()
    return {"supplier_id": str(supplier.id), "legal_name": supplier.legal_name, "sample_size": len(samples), "data_sufficient": sufficient, "weighted_score": str(score.quantize(Decimal("0.01"))) if score is not None else None, "on_time_delivery_rate": str(indicators["on_time"]) if indicators["on_time"] is not None else None, "fill_rate": str(indicators["fill"]) if indicators["fill"] is not None else None, "quality_rate": str(indicators["acceptance"]) if indicators["acceptance"] is not None else None, "invoice_conformity_rate": str(indicators["invoice"]) if indicators["invoice"] is not None else None, "rejection_rate": str(rate(damaged, received)) if received else None, "sample_records": samples, "policy": policy, "warning": None if sufficient else "Muestra insuficiente para asignar una puntuación global.", "corrective_tasks": [{"id": str(task.id), "title": task.title, "status": task.status, "due_date": task.due_date.isoformat() if task.due_date else None, "version": task.version, "resolution_notes": task.resolution_notes, "can_edit": task.creator_id == user.user_id or task.assignee_id == user.user_id or "operations:manage" in user.permissions} for task in tasks]}


class SupplierCorrectiveRequest(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=5, max_length=2000)
    due_date: datetime


def create_corrective(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier.corrective:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    if not db.scalar(select(Supplier.id).where(Supplier.company_id == user.company_id, Supplier.id == identifier)):
        raise HTTPException(404, "Proveedor no encontrado.")
    if payload.due_date.tzinfo is None or payload.due_date <= datetime.now(timezone.utc):
        raise HTTPException(422, "La acción correctiva necesita un vencimiento futuro con zona horaria.")
    row = CollaborationTask(company_id=user.company_id, title=payload.title, description=payload.description, due_date=payload.due_date, creator_id=user.user_id, assignee_id=user.user_id, resource_type="supplier", resource_id=identifier, status="pending", priority="high", version=1, checklist_json="[]", dependencies_json="[]")
    db.add(row)
    db.flush()
    result = {"id": str(row.id), "title": row.title, "status": row.status}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="CREATE_SUPPLIER_CORRECTIVE", entity_type="Supplier", entity_id=identifier, diff={"task_id": str(row.id), "description": payload.description, "due_date": payload.due_date.isoformat()})
    complete_request(record, result)
    db.commit()
    return result
