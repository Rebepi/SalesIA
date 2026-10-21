import json
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument
from salesia.modules.organizacion.application.periodos import business_date
from salesia.shared.infrastructure.models import AttachmentModel, CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def supplier_qualified(supplier, today):
    return supplier.is_active and supplier.qualification_status == "approved" and (supplier.qualification_until is None or supplier.qualification_until >= today)


def require_supplier_qualified(db, user, supplier):
    if supplier is None or not supplier_qualified(supplier, business_date(db, user.company_id)):
        raise HTTPException(409, "El proveedor requiere homologación vigente para nuevos compromisos. Sus compras ya comprometidas conservan el circuito de recepción.")


class QualificationRequest(BaseModel):
    version: int = Field(ge=1)
    action: Literal["evaluate", "approve", "suspend", "reject"]
    valid_until: date | None = None
    reason: str = Field(min_length=5, max_length=4000)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=30)


def qualification_data(db, user, supplier):
    today = business_date(db, user.company_id)
    status = supplier.qualification_status
    if status == "approved" and supplier.qualification_until and supplier.qualification_until < today:
        status = "expired"
    open_orders = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.supplier_id == supplier.id, SupplyDocument.kind == "PURCHASE_ORDER", SupplyDocument.status.in_(("submitted", "approved", "partially_received", "reopened")))).all()
    attachments = db.scalars(select(AttachmentModel).where(AttachmentModel.company_id == user.company_id, AttachmentModel.related_entity_type == "supplier", AttachmentModel.related_entity_id == supplier.id, AttachmentModel.verified.is_(True), AttachmentModel.scan_status == "clean")).all()
    return {"available_documents": [{"id": str(item.id), "file_name": item.file_name, "mime_type": item.mime_type} for item in attachments], "id": str(supplier.id), "legal_name": supplier.legal_name, "status": status, "stored_status": supplier.qualification_status, "valid_until": supplier.qualification_until.isoformat() if supplier.qualification_until else None, "version": supplier.version, "can_create_commitments": supplier_qualified(supplier, today), "history": json.loads(supplier.qualification_history_json or "[]"), "documents": json.loads(supplier.qualification_documents_json or "[]"), "existing_orders": [{"id": str(row.id), "status": row.status, "version": row.version} for row in open_orders]}


def qualification_action(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier.qualification:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Proveedor no encontrado.")
    if row.version != payload.version:
        raise HTTPException(409, "La ficha del proveedor cambió; recarga antes de decidir.")
    if payload.action != "evaluate" and not ({"purchases:approve", "approvals:manage", "organization:manage"} & set(user.permissions)):
        raise HTTPException(403, "La aprobación o suspensión requiere autorización de compras o administración.")
    if payload.action == "approve" and (payload.valid_until is None or payload.valid_until < business_date(db, user.company_id)):
        raise HTTPException(422, "La aprobación requiere una fecha de vigencia actual o futura.")
    attachments = db.scalars(select(AttachmentModel).where(AttachmentModel.company_id == user.company_id, AttachmentModel.id.in_(payload.attachment_ids))).all() if payload.attachment_ids else []
    if len(attachments) != len(set(payload.attachment_ids)) or any(not item.verified or item.scan_status != "clean" or item.related_entity_type != "supplier" or item.related_entity_id != row.id for item in attachments):
        raise HTTPException(422, "Selecciona documentos internos verificados y vinculados a este proveedor.")
    before = qualification_data(db, user, row)
    state = {"evaluate": "pending_evaluation", "approve": "approved", "suspend": "suspended", "reject": "rejected"}[payload.action]
    row.qualification_status = state
    if payload.action == "approve":
        row.qualification_until, row.is_active = payload.valid_until, True
    history = json.loads(row.qualification_history_json or "[]")
    history.append({"action": payload.action, "before": before["status"], "status": state, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": payload.reason, "valid_until": payload.valid_until.isoformat() if payload.valid_until else None, "attachment_ids": [str(item.id) for item in attachments]})
    row.qualification_history_json = json.dumps(history)
    documents = {item["id"]: item for item in json.loads(row.qualification_documents_json or "[]")}
    documents.update({str(item.id): {"id": str(item.id), "file_name": item.file_name, "mime_type": item.mime_type} for item in attachments})
    row.qualification_documents_json = json.dumps(list(documents.values()))
    row.version += 1
    result = qualification_data(db, user, row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SUPPLIER_QUALIFICATION", entity_type="Supplier", entity_id=row.id, diff={"before": before, "after": result, "reason": payload.reason})
    complete_request(record, result)
    db.commit()
    return result
