from uuid import UUID
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.colaboracion_aprobaciones import (
    ApprovalCreateRequest,
    ApprovalDecideRequest,
)
from salesia.modules.operaciones.infrastructure_models import CollaborationApproval
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.modules.operaciones.application.recursos import entity
from salesia.modules.operaciones.application.politicas_aprobacion import document_hash, resolve_vote


def create_approval(payload: ApprovalCreateRequest, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    if ":v" in payload.policy_name:
        raise HTTPException(422, "Ese nombre está reservado para solicitudes generadas por las políticas del sistema.")
    resource = entity(db, current_user, payload.resource_type, payload.resource_id, write=True, lock=True)
    if payload.document_version != getattr(resource, "version", 1):
        raise HTTPException(409, "La versión solicitada no coincide con el documento real.")
    approval = CollaborationApproval(
        company_id=current_user.company_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        document_version=payload.document_version,
        policy_name=payload.policy_name,
        evidence_json=payload.evidence_json,
        requested_by=current_user.user_id,
        status="pending",
        created_at=now(),
        document_hash=document_hash(resource, db),
    )

    db.add(approval)

    db.commit()

    return {
        "id": str(approval.id),
        "resource_type": approval.resource_type,
        "document_version": approval.document_version,
        "status": approval.status,
    }


def list_approvals(current_user: AuthenticatedUser, db: Session):
    query = select(CollaborationApproval).where(CollaborationApproval.company_id == current_user.company_id)

    if "approvals:manage" not in current_user.permissions:
        query = query.where(CollaborationApproval.requested_by == current_user.user_id)

    rows = db.scalars(query.order_by(CollaborationApproval.created_at.desc())).all()

    items = []

    for row in rows:
        current_version = 0
        changed = True
        try:
            current_document = entity(db, current_user, row.resource_type, row.resource_id)
            current_version = getattr(current_document, "version", 1)
            changed = not row.document_hash or document_hash(current_document, db) != row.document_hash or current_version != row.document_version
        except HTTPException as failure:
            if failure.status_code not in (403, 404, 422):
                raise
        config = json.loads(row.policy_snapshot_json or "{}")
        stage = config.get("stages", [])[row.stage_index] if config.get("stages") else None
        requester = db.scalar(
            select(UserModel).where(UserModel.id == row.requested_by, UserModel.company_id == current_user.company_id)
        )

        items.append(
            {
                "id": str(row.id),
                "code": f"APR-{str(row.id).split('-')[0].upper()}",
                "resource_type": row.resource_type,
                "resource_id": str(row.resource_id),
                "document_version": row.document_version,
                "server_document_version": current_version,
                "document_changed": changed,
                "policy_name": row.policy_name,
                "evidence": row.evidence_json or "",
                "status": row.status,
                "requested_by": str(row.requested_by),
                "requester_name": requester.email.split("@")[0] if requester else str(row.requested_by),
                "requester_email": requester.email if requester else "",
                "created_at": row.created_at.isoformat(),
                "decision_reason": row.decision_reason,
                "decided_by": str(row.decided_by) if row.decided_by else None,
                "decided_at": row.decided_at.isoformat() if row.decided_at else None,
                "stage_index": row.stage_index,
                "due_at": row.due_at.isoformat() if row.due_at else None,
                "stage_name": stage["name"] if stage else "Revisión",
                "stage_count": len(config.get("stages", [])) or 1,
            }
        )

    return {"items": items, "count": len(items)}


def decide_approval(approval_id: UUID, payload: ApprovalDecideRequest, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    approval = db.scalar(
        select(CollaborationApproval)
        .where(CollaborationApproval.id == approval_id, CollaborationApproval.company_id == current_user.company_id)
        .with_for_update()
    )

    if not approval:
        raise HTTPException(404, "Aprobación no encontrada.")

    if approval.status != "pending":
        raise HTTPException(409, "La aprobación ya fue resuelta previamente.")

    if payload.current_document_version != approval.document_version:
        raise HTTPException(
            409, "El documento fue modificado con posterioridad; requiere revalidación antes de aprobar."
        )

    final_decision = resolve_vote(db, current_user, approval, payload)

    if not final_decision:
        db.commit()
        return {"id": str(approval.id), "status": "pending", "decision_reason": payload.reason, "stage_index": approval.stage_index, "decided_at": None}

    approval.status = payload.decision

    approval.decision_reason = payload.reason

    approval.decided_by = current_user.user_id

    approval.decided_at = now()

    db.commit()

    return {
        "id": str(approval.id),
        "status": approval.status,
        "decision_reason": approval.decision_reason,
        "decided_at": approval.decided_at.isoformat(),
    }
