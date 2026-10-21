import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, inspect, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.operaciones.application.recursos import entity
from salesia.modules.operaciones.infrastructure_models import CollaborationApproval, Notification
from salesia.modules.operaciones.infrastructure.models.politicas_aprobacion import ApprovalPolicyModel, ApprovalVoteModel, DelegationModel
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class ApprovalStageRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    approver_ids: list[UUID] = Field(min_length=1, max_length=50)
    required_votes: int = Field(default=1, ge=1, le=50)
    due_hours: int = Field(default=48, ge=1, le=8760)

    @model_validator(mode="after")
    def unique_approvers(self):
        if len(set(self.approver_ids)) != len(self.approver_ids) or self.required_votes > len(self.approver_ids):
            raise ValueError("Indica responsables distintos y un número de votos que puedan alcanzar.")
        return self


class ApprovalPolicyRequest(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
    resource_type: Literal["sale", "order", "purchase_order", "expense", "return"]
    action: Literal["confirm", "approve", "accept", "dispatch", "submit"]
    metric: Literal["always", "total_amount", "discount_percentage", "margin_percentage"] = "total_amount"
    comparison: Literal["gt", "gte", "lt", "lte"] = "gt"
    threshold: Decimal = Field(default=0, ge=0)
    stages: list[ApprovalStageRequest] = Field(min_length=1, max_length=10)
    is_active: bool = True
    version: int = Field(default=0, ge=0)


class DelegationRequest(BaseModel):
    principal_id: UUID
    delegate_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def valid_period(self):
        if self.principal_id == self.delegate_id:
            raise ValueError("La delegación requiere dos personas diferentes.")
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None or self.ends_at <= self.starts_at or self.ends_at <= datetime.now(timezone.utc):
            raise ValueError("Indica un período válido con zona horaria y vencimiento futuro.")
        return self


def document_hash(row, db=None):
    data = {column.key: getattr(row, column.key) for column in inspect(row).mapper.column_attrs if column.key not in ("updated_at", "history_json", "communication_log_json")}
    if hasattr(row, "lines"):
        data["lines"] = [{column.key: getattr(line, column.key) for column in inspect(line).mapper.column_attrs if column.key not in ("updated_at", "created_at")} for line in sorted(row.lines, key=lambda value: str(value.id))]
    if db is not None:
        from salesia.modules.operaciones.infrastructure.models.campos import BusinessFieldValuesModel
        data["business_fields"] = list(db.scalars(select(BusinessFieldValuesModel.values_json).where(BusinessFieldValuesModel.company_id == row.company_id, BusinessFieldValuesModel.resource_id == row.id).order_by(BusinessFieldValuesModel.resource_type)).all())
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def metric_value(row, name):
    if name == "always":
        return Decimal("1")
    if name == "total_amount":
        value = getattr(row, "total_amount", getattr(row, "amount", None))
        if value is None and hasattr(row, "details_json"):
            details = json.loads(row.details_json or "{}")
            value = details.get("total", details.get("total_amount"))
        if value is None and hasattr(row, "lines"):
            value = sum((line.quantity * line.unit_cost for line in row.lines), Decimal("0"))
        return Decimal(str(value or "0"))
    if hasattr(row, "lines_json"):
        lines = json.loads(row.lines_json or "[]")
        if name == "discount_percentage":
            return max((Decimal(str(line.get("discount_pct", "0"))) for line in lines), default=Decimal("0"))
        net = sum((Decimal(str(line.get("line_subtotal", "0"))) for line in lines), Decimal("0"))
        cost = sum((Decimal(str(line.get("unit_cost", "0"))) * Decimal(str(line.get("quantity", "0"))) for line in lines), Decimal("0"))
    elif hasattr(row, "lines"):
        if name == "discount_percentage":
            return max((line.discount_amount / (line.subtotal_amount + line.discount_amount) * 100 if line.subtotal_amount + line.discount_amount else Decimal("0") for line in row.lines if hasattr(line, "discount_amount")), default=Decimal("0"))
        net = sum((line.subtotal_amount for line in row.lines if hasattr(line, "subtotal_amount")), Decimal("0"))
        cost = sum((line.quantity * line.unit_cost_snapshot for line in row.lines if hasattr(line, "unit_cost_snapshot")), Decimal("0"))
    else:
        raise HTTPException(422, "La métrica no está disponible para este tipo de documento.")
    return (net - cost) / net * 100 if net else Decimal("0")


def matches(row, config):
    if config["metric"] == "always":
        return True
    value, threshold = metric_value(row, config["metric"]), Decimal(config["threshold"])
    return {"gt": value > threshold, "gte": value >= threshold, "lt": value < threshold, "lte": value <= threshold}[config["comparison"]]


def notify_stage(db, user, approval, config):
    stage = config["stages"][approval.stage_index]
    for identifier in stage["approver_ids"]:
        db.add(Notification(company_id=user.company_id, user_id=UUID(identifier), title="Aprobación pendiente", message=f"{approval.policy_name} · {stage['name']}", event_type="APPROVAL_REQUIRED", category="operations", priority="high", resource_type="approval", resource_id=approval.id))


def enforce_policies(db, user, kind, identifier, action):
    policies = db.scalars(select(ApprovalPolicyModel).where(ApprovalPolicyModel.company_id == user.company_id, ApprovalPolicyModel.resource_type == kind, ApprovalPolicyModel.action == action, ApprovalPolicyModel.is_active.is_(True))).all()
    if not policies:
        return
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = entity(db, user, kind, identifier, write=True, lock=True)
    completed = {"confirm": {"confirmed", "paid", "fulfilled", "partially_fulfilled"}, "approve": {"approved"}, "accept": {"accepted"}, "dispatch": {"dispatched", "delivered"}}
    if getattr(row, "status", "") in completed.get(action, set()):
        return
    fingerprint = document_hash(row, db)
    missing = []
    for policy in policies:
        config = json.loads(policy.config_json)
        if not matches(row, config):
            continue
        policy_name = f"{policy.code}:v{policy.version}:{action}"
        obsolete = db.scalars(select(CollaborationApproval).where(CollaborationApproval.company_id == user.company_id, CollaborationApproval.resource_type == kind, CollaborationApproval.resource_id == identifier, CollaborationApproval.status == "pending", CollaborationApproval.policy_name.startswith(f"{policy.code}:v", autoescape=True), CollaborationApproval.policy_name.endswith(f":{action}"))).all()
        for previous in obsolete:
            if previous.document_hash != fingerprint or previous.policy_name != policy_name:
                previous.status, previous.decision_reason = "stale", "El contenido del documento o la política cambió y requiere revisión vigente."
        existing = db.scalar(select(CollaborationApproval).where(CollaborationApproval.company_id == user.company_id, CollaborationApproval.resource_type == kind, CollaborationApproval.resource_id == identifier, CollaborationApproval.document_hash == fingerprint, CollaborationApproval.policy_name == policy_name, CollaborationApproval.policy_snapshot_json == policy.config_json).order_by(CollaborationApproval.created_at.desc()).limit(1))
        if existing and existing.status == "approved":
            continue
        if existing is None or existing.status in ("stale", "cancelled"):
            approval = CollaborationApproval(company_id=user.company_id, resource_type=kind, resource_id=identifier, document_version=getattr(row, "version", 1), policy_name=policy_name, evidence_json=json.dumps({"metric": config["metric"], "value": str(metric_value(row, config["metric"])), "threshold": config["threshold"]}), requested_by=user.user_id, status="pending", document_hash=fingerprint, policy_snapshot_json=policy.config_json, stage_index=0, due_at=datetime.now(timezone.utc) + timedelta(hours=config["stages"][0]["due_hours"]))
            db.add(approval)
            db.flush()
            notify_stage(db, user, approval, config)
            existing = approval
        missing.append({"approval_id": str(existing.id), "policy": policy.code, "status": existing.status})
    if missing:
        db.commit()
        raise HTTPException(409, {"title": "La operación requiere aprobación antes de continuar.", "approvals": missing})


def save_policy(db, user, payload, key):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "Se requiere administrar la organización para configurar políticas.")
    record, cached = claim_request(db, user.company_id, "approval_policies.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    allowed = {"sale": {"confirm"}, "order": {"confirm", "approve"}, "purchase_order": {"approve"}, "expense": {"submit", "approve"}, "return": {"accept"}}
    if payload.action not in allowed[payload.resource_type]:
        raise HTTPException(422, "La acción no corresponde al proceso de este documento.")
    if payload.metric in ("margin_percentage", "discount_percentage") and payload.resource_type not in ("sale", "order"):
        raise HTTPException(422, "El margen y descuento se configuran sobre ventas o pedidos.")
    ids = {identifier for stage in payload.stages for identifier in stage.approver_ids}
    users = db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id.in_(ids), UserModel.is_active.is_(True))).all()
    if len(users) != len(ids):
        raise HTTPException(422, "Todos los responsables deben estar activos en la empresa.")
    from salesia.modules.seguridad.infrastructure.sessions import permissions_for
    if any("approvals:manage" not in permissions_for(db, member) for member in users):
        raise HTTPException(422, "Los responsables necesitan permiso para gestionar aprobaciones.")
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = db.scalar(select(ApprovalPolicyModel).where(ApprovalPolicyModel.company_id == user.company_id, ApprovalPolicyModel.code == payload.code).with_for_update())
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "La política cambió; recarga antes de guardarla.")
    config = payload.model_dump(mode="json", exclude={"version", "is_active"})
    if row is None:
        row = ApprovalPolicyModel(company_id=user.company_id, code=payload.code, version=0)
        db.add(row)
    row.resource_type, row.action, row.config_json, row.is_active, row.version = payload.resource_type, payload.action, json.dumps(config), payload.is_active, row.version + 1
    db.flush()
    result = {"id": str(row.id), "version": row.version}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_APPROVAL_POLICY", entity_type="ApprovalPolicy", entity_id=row.id, diff=config)
    complete_request(record, result)
    db.commit()
    return result


def list_policies(db, user):
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "No tienes permiso para consultar la configuración de políticas.")
    return [{**json.loads(row.config_json), "id": str(row.id), "version": row.version, "is_active": row.is_active} for row in db.scalars(select(ApprovalPolicyModel).where(ApprovalPolicyModel.company_id == user.company_id).order_by(ApprovalPolicyModel.code)).all()]


def resolve_vote(db, user, approval, payload):
    resource = entity(db, user, approval.resource_type, approval.resource_id, lock=True)
    if approval.document_hash is None:
        approval.status = "stale"
        db.commit()
        raise HTTPException(409, "La solicitud histórica no conserva el contenido revisado. Solicita una autorización nueva.")
    if getattr(resource, "version", 1) != approval.document_version or (approval.document_hash and document_hash(resource, db) != approval.document_hash):
        approval.status = "stale"
        db.commit()
        raise HTTPException(409, "El documento real cambió; solicita una aprobación sobre su contenido vigente.")
    if user.user_id == approval.requested_by:
        raise HTTPException(403, "No puedes aprobar tu propia solicitud.")
    creator_id = getattr(resource, "created_by", None)
    if creator_id == user.user_id:
        raise HTTPException(403, "El autor del documento no puede aprobar su propia operación.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, user, "workflow", [approval.requested_by, creator_id], "CollaborationApproval", approval.id)
    config = json.loads(approval.policy_snapshot_json or "{}")
    if not config:
        return True
    stage = config["stages"][approval.stage_index]
    represented = {str(user.user_id)}
    current = datetime.now(timezone.utc)
    delegations = db.scalars(select(DelegationModel).where(DelegationModel.company_id == user.company_id, DelegationModel.delegate_id == user.user_id, DelegationModel.revoked_at.is_(None), DelegationModel.starts_at <= current, DelegationModel.ends_at > current)).all()
    represented |= {str(item.principal_id) for item in delegations}
    if not represented.intersection(stage["approver_ids"]):
        raise HTTPException(403, "No eres responsable de la etapa actual ni tienes una delegación vigente.")
    used = set(str(value) for value in db.scalars(select(ApprovalVoteModel.represented_principal_id).where(ApprovalVoteModel.company_id == user.company_id, ApprovalVoteModel.approval_id == approval.id, ApprovalVoteModel.stage == approval.stage_index)).all())
    available = represented.intersection(stage["approver_ids"]) - used - {str(approval.requested_by), str(creator_id)}
    if not available:
        raise HTTPException(409, "Tu representación ya tiene una decisión o corresponde al solicitante.")
    represented_principal = str(user.user_id) if str(user.user_id) in available else sorted(available)[0]
    duplicate = db.scalar(select(ApprovalVoteModel.id).where(ApprovalVoteModel.company_id == user.company_id, ApprovalVoteModel.approval_id == approval.id, ApprovalVoteModel.stage == approval.stage_index, ApprovalVoteModel.actor_id == user.user_id))
    if duplicate:
        raise HTTPException(409, "Ya registraste una decisión en esta etapa.")
    db.add(ApprovalVoteModel(company_id=user.company_id, approval_id=approval.id, stage=approval.stage_index, actor_id=user.user_id, represented_principal_id=UUID(represented_principal), decision=payload.decision, reason=payload.reason))
    db.flush()
    if payload.decision == "rejected":
        return True
    count = db.scalar(select(func.count()).select_from(ApprovalVoteModel).where(ApprovalVoteModel.company_id == user.company_id, ApprovalVoteModel.approval_id == approval.id, ApprovalVoteModel.stage == approval.stage_index, ApprovalVoteModel.decision == "approved")) or 0
    if count < stage["required_votes"]:
        return False
    if approval.stage_index + 1 < len(config["stages"]):
        approval.stage_index += 1
        approval.due_at = current + timedelta(hours=config["stages"][approval.stage_index]["due_hours"])
        notify_stage(db, user, approval, config)
        return False
    return True


def create_delegation(db, user, payload, key):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "La administración de la organización autoriza las delegaciones.")
    record, cached = claim_request(db, user.company_id, "delegations.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    from salesia.modules.seguridad.infrastructure.sessions import permissions_for
    for identifier in (payload.principal_id, payload.delegate_id):
        member = db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == identifier, UserModel.is_active.is_(True)))
        if not member or "approvals:manage" not in permissions_for(db, member):
            raise HTTPException(422, "La delegación requiere miembros activos autorizados para gestionar aprobaciones.")
    row = DelegationModel(company_id=user.company_id, **payload.model_dump())
    db.add(row)
    db.flush()
    result = {"id": str(row.id)}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="CREATE_APPROVAL_DELEGATION", entity_type="ApprovalDelegation", entity_id=row.id, diff=payload.model_dump(mode="json"))
    complete_request(record, result)
    db.commit()
    return result


def revoke_delegation(db, user, identifier):
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "No puedes revocar esta delegación.")
    row = db.scalar(select(DelegationModel).where(DelegationModel.company_id == user.company_id, DelegationModel.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Delegación no encontrada.")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REVOKE_APPROVAL_DELEGATION", entity_type="ApprovalDelegation", entity_id=row.id)
        db.commit()
    return {"id": str(row.id), "status": "revoked"}


def list_delegations(db, user):
    statement = select(DelegationModel).where(DelegationModel.company_id == user.company_id)
    if "organization:manage" not in user.permissions:
        statement = statement.where((DelegationModel.principal_id == user.user_id) | (DelegationModel.delegate_id == user.user_id))
    rows = db.scalars(statement.order_by(DelegationModel.starts_at.desc())).all()
    current = datetime.now(timezone.utc)
    result = []
    for row in rows:
        start = row.starts_at.replace(tzinfo=timezone.utc) if row.starts_at.tzinfo is None else row.starts_at
        end = row.ends_at.replace(tzinfo=timezone.utc) if row.ends_at.tzinfo is None else row.ends_at
        result.append({"id": str(row.id), "principal_id": str(row.principal_id), "delegate_id": str(row.delegate_id), "starts_at": start.isoformat(), "ends_at": end.isoformat(), "reason": row.reason, "status": "revoked" if row.revoked_at else "expired" if end <= current else "scheduled" if start > current else "active"})
    return result
