import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, update

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.catalogo.infrastructure_models import ProductWarrantyClaimModel
from salesia.modules.clientes.infrastructure.models import CustomerActivityModel, CustomerOpportunityModel, CustomerProfileModel
from salesia.modules.finanzas.infrastructure.models.caja_chica import PettyCashAdvanceModel
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel, CashCustodyTransferModel
from salesia.modules.inventario.infrastructure_models import DeliveryIncident, InventoryPickingList
from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel
from salesia.modules.operaciones.infrastructure.models.colaboracion import CollaborationApproval, CollaborationTask
from salesia.modules.operaciones.infrastructure.models.planificacion import TaskRecurrenceModel
from salesia.modules.operaciones.infrastructure.models.politicas_aprobacion import ApprovalPolicyModel, ApprovalVoteModel, DelegationModel
from salesia.modules.pedidos.infrastructure.models.documentos import QuotationModel
from salesia.modules.seguridad.application.auxiliares.get_role_permissions import get_role_permissions
from salesia.modules.seguridad.infrastructure.sessions import revoke_user_sessions
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesRepresentative
from salesia.shared.infrastructure.models import CashSessionModel, CompanyModel, CustomerModel, JobModel, SaleModel, UserModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class HandoverRequest(BaseModel):
    preview_hash: str = Field(min_length=64, max_length=64)
    transfers: dict[str, UUID] = Field(default_factory=dict, max_length=20)
    reason: str = Field(min_length=5, max_length=2000)


def member(db, company_id, identifier, lock=False):
    query = select(UserModel).where(UserModel.company_id == company_id, UserModel.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Usuario no encontrado en la empresa activa.")
    return row


def groups(db, company_id, identifier):
    rep_ids = select(SalesRepresentative.id).where(SalesRepresentative.company_id == company_id, SalesRepresentative.user_id == identifier)
    active_customers = select(CustomerModel.id).where(CustomerModel.company_id == company_id, CustomerModel.is_active.is_(True))
    return {
        "portfolio": ("Cartera principal de clientes", CustomerProfileModel, "assigned_sales_rep_id", [CustomerProfileModel.assigned_sales_rep_id.in_(rep_ids), CustomerProfileModel.customer_id.in_(active_customers)], ["sales:write"], True),
        "backup_portfolio": ("Respaldo de cartera de clientes", CustomerProfileModel, "backup_sales_rep_id", [CustomerProfileModel.backup_sales_rep_id.in_(rep_ids), CustomerProfileModel.customer_id.in_(active_customers)], ["sales:write"], True),
        "draft_sales": ("Ventas en borrador", SaleModel, "sales_rep_id", [SaleModel.sales_rep_id.in_(rep_ids), SaleModel.status == "draft"], ["sales:write"], True),
        "tasks": ("Tareas asignadas abiertas", CollaborationTask, "assignee_id", [CollaborationTask.assignee_id == identifier, CollaborationTask.status.notin_(["completed", "cancelled", "done"])], [], False),
        "unassigned_tasks": ("Tareas propias pendientes sin destinatario", CollaborationTask, "assignee_id", [CollaborationTask.creator_id == identifier, CollaborationTask.assignee_id.is_(None), CollaborationTask.status.notin_(["completed", "cancelled", "done"])], [], False),
        "opportunities": ("Oportunidades comerciales abiertas", CustomerOpportunityModel, "assigned_to_id", [CustomerOpportunityModel.assigned_to_id == identifier, CustomerOpportunityModel.stage.notin_(["won", "lost", "closed"])], ["customers:write"], False),
        "activities": ("Actividades comerciales pendientes", CustomerActivityModel, "assigned_to_id", [CustomerActivityModel.assigned_to_id == identifier, CustomerActivityModel.status == "pending"], ["customers:write"], False),
        "warranties": ("Expedientes de garantía asignados", ProductWarrantyClaimModel, "assigned_to", [ProductWarrantyClaimModel.assigned_to == identifier, ProductWarrantyClaimModel.status.notin_(["delivered", "closed", "cancelled", "rejected"])], ["sales:write"], False),
        "picking": ("Preparaciones de almacén", InventoryPickingList, "assigned_to", [InventoryPickingList.assigned_to == identifier, InventoryPickingList.status.notin_(["COMPLETED", "CANCELLED", "completed", "cancelled"])], ["inventory:write"], False),
        "routes": ("Recorridos de reparto", DeliveryRouteModel, "responsible_id", [DeliveryRouteModel.responsible_id == identifier, DeliveryRouteModel.status.notin_(["completed", "cancelled"])], ["inventory:write"], False),
        "delivery_incidents": ("Incidencias de entrega", DeliveryIncident, "responsible_user_id", [DeliveryIncident.responsible_user_id == identifier, DeliveryIncident.resolution_status.notin_(["RESOLVED", "CLOSED", "resolved", "closed"])], ["inventory:write"], False),
        "custody_accounts": ("Puntos de custodia con saldo cero", CashCustodyAccountModel, "responsible_id", [CashCustodyAccountModel.responsible_id == identifier, CashCustodyAccountModel.is_active.is_(True), CashCustodyAccountModel.balance == 0], ["cash:register:manage"], False),
        "supervised_reps": ("Vendedores supervisados", SalesRepresentative, "supervisor_id", [SalesRepresentative.supervisor_id == identifier, SalesRepresentative.is_active.is_(True)], ["sales:write"], False),
        "quotations": ("Cotizaciones vigentes", QuotationModel, "seller_id", [QuotationModel.seller_id == identifier, QuotationModel.status.notin_(["converted", "superseded", "cancelled", "rejected", "expired"])], ["sales:write"], False),
        "representative_quotations": ("Cotizaciones vinculadas a su representación comercial", QuotationModel, "seller_id", [QuotationModel.seller_id.in_(rep_ids), QuotationModel.status.notin_(["converted", "superseded", "cancelled", "rejected", "expired"])], ["sales:write"], True),
        "policy_reviews": ("Revisión en políticas de aprobación vigentes", ApprovalPolicyModel, "config_json", [ApprovalPolicyModel.is_active.is_(True), ApprovalPolicyModel.config_json.contains(str(identifier))], ["approvals:manage"], False),
        "approval_reviews": ("Etapas pendientes de aprobación", CollaborationApproval, "policy_snapshot_json", [CollaborationApproval.status == "pending", CollaborationApproval.policy_snapshot_json.contains(str(identifier))], ["approvals:manage"], False),
        "recurrence_assignees": ("Destinatario de tareas recurrentes futuras", TaskRecurrenceModel, "template_json", [TaskRecurrenceModel.is_active.is_(True), TaskRecurrenceModel.template_json.contains(str(identifier))], [], False),
        "recurrence_owners": ("Responsabilidad de tareas recurrentes futuras", TaskRecurrenceModel, "owner_id", [TaskRecurrenceModel.owner_id == identifier, TaskRecurrenceModel.is_active.is_(True)], [], False),
    }


def snapshot(row):
    return {column.key: str(getattr(row, column.key)) for column in row.__table__.columns}


def pending_review_stages(db, company_id, row, identifier):
    result = []
    for index, stage in enumerate(json.loads(row.policy_snapshot_json or "{}").get("stages", [])):
        if index < row.stage_index or str(identifier) not in stage["approver_ids"]:
            continue
        voted = db.scalar(select(ApprovalVoteModel.id).where(ApprovalVoteModel.company_id == company_id, ApprovalVoteModel.approval_id == row.id, ApprovalVoteModel.stage == index, ApprovalVoteModel.represented_principal_id == identifier).limit(1))
        if voted is None:
            result.append(index)
    return result


def rows_for(db, company_id, definition, lock=False, group=None, identifier=None):
    _, model, _, conditions, _, _ = definition
    query = select(model).where(model.company_id == company_id, *conditions).order_by(model.id)
    rows = db.scalars(query.with_for_update() if lock else query).all()
    if group == "approval_reviews":
        rows = [row for row in rows if pending_review_stages(db, company_id, row, identifier)]
    if group == "recurrence_assignees":
        rows = [row for row in rows if str(json.loads(row.template_json).get("assignee_id")) == str(identifier)]
    return rows


def preflight(db, user, identifier):
    source = member(db, user.company_id, identifier)
    sections, fingerprints, blockers = [], [], []
    for key, definition in groups(db, user.company_id, identifier).items():
        rows = rows_for(db, user.company_id, definition, group=key, identifier=identifier)
        fingerprints.extend({"group": key, "record": snapshot(row)} for row in rows)
        sections.append({"key": key, "label": definition[0], "count": len(rows), "required_permissions": definition[4], "requires_sales_rep": definition[5], "samples": [{"id": str(row.id), "name": getattr(row, "title", None) or getattr(row, "name", None) or getattr(row, "code", None) or getattr(row, "quotation_number", None) or str(row.id)[:8]} for row in rows[:15]]})

    def block(code, label, model, conditions, guidance):
        rows = db.scalars(select(model).where(model.company_id == user.company_id, *conditions).order_by(model.id)).all()
        fingerprints.extend({"blocker": code, "record": snapshot(row)} for row in rows)
        if rows:
            blockers.append({"code": code, "label": label, "count": len(rows), "guidance": guidance, "samples": [str(row.id) for row in rows[:15]]})

    block("cash", "Cajas abiertas", CashSessionModel, [CashSessionModel.user_id == identifier, CashSessionModel.status == "open"], "Realice el arqueo y cierre o el relevo de custodia aceptado desde Caja.")
    block("money", "Efectivo bajo responsabilidad", CashCustodyAccountModel, [CashCustodyAccountModel.responsible_id == identifier, CashCustodyAccountModel.balance != 0], "Traspase el efectivo y obtenga la recepción del destinatario. Reasignar una cuenta con dinero no sustituye la entrega física.")
    block("transfers", "Entregas de efectivo pendientes", CashCustodyTransferModel, [or_(CashCustodyTransferModel.sender_id == identifier, CashCustodyTransferModel.receiver_id == identifier), CashCustodyTransferModel.status.in_(["sent", "disputed", "return_pending"])], "Resuelva la recepción, diferencia o devolución antes de suspender al custodio.")
    block("advances", "Anticipos de gastos sin rendir", PettyCashAdvanceModel, [PettyCashAdvanceModel.beneficiary_id == identifier, PettyCashAdvanceModel.status.notin_(["closed", "cancelled", "rejected"])], "Complete la rendición y la devolución o reembolso; se conserva la identidad del beneficiario original.")
    from salesia.modules.ventas.application.participacion_comercial import coverage_rows
    from salesia.modules.organizacion.application.periodos import business_date
    rep_ids = {str(value) for value in db.scalars(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == identifier)).all()}
    today = business_date(db, user.company_id).isoformat()
    for coverage in coverage_rows(db, user.company_id):
        if coverage["status"] == "active" and coverage["ends_on"] >= today and (coverage["representative_id"] in rep_ids or coverage["replacement_id"] in rep_ids):
            fingerprints.append({"blocker": "coverage", "record": coverage})
            blockers.append({"code": f"coverage:{coverage['id']}", "label": "Reemplazo comercial vigente o programado", "count": 1, "guidance": "Cancele o sustituya el reemplazo desde Equipo y comisiones antes de retirar a su participante.", "samples": [coverage["id"]]})
    if source.role == "company_admin" and source.is_active and (db.scalar(select(func.count()).select_from(UserModel).where(UserModel.company_id == user.company_id, UserModel.role == "company_admin", UserModel.is_active.is_(True))) or 0) <= 1:
        blockers.append({"code": "last_admin", "label": "Último administrador activo", "count": 1, "guidance": "Debe permanecer al menos un administrador activo de la empresa.", "samples": []})
    if identifier == user.user_id:
        blockers.append({"code": "self", "label": "La baja requiere otro administrador", "count": 1, "guidance": "Otra persona autorizada debe gestionar su baja.", "samples": []})
    result = {"user_id": str(source.id), "name": source.full_name or source.email, "email": source.email, "is_active": source.is_active, "groups": sections, "blockers": blockers, "can_suspend": source.is_active and not blockers and not any(section["count"] for section in sections), "effects": ["Las ventas confirmadas, solicitudes, votos y movimientos conservan su autoría histórica.", "Se cierran las sesiones del usuario y se cancelan sus trabajos pendientes al suspenderlo.", "Se desactiva su representación comercial, se revocan sus delegaciones y se pausan sus reportes programados."]}
    result["preview_hash"] = hashlib.sha256(json.dumps({"result": result, "source": snapshot(source), "records": fingerprints}, sort_keys=True).encode()).hexdigest()
    return result


def assert_ready(db, user, identifier):
    result = preflight(db, user, identifier)
    if not result["can_suspend"]:
        raise HTTPException(409, {"message": "Revise y traspase las responsabilidades antes de suspender al usuario.", "handover": result})
    return result


def end_operational_access(db, user, identifier, reason):
    now = datetime.now(timezone.utc)
    for rep in db.scalars(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == identifier)).all():
        rep.is_active = False
    schedules = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "report_schedule", AnalyticsArtifact.created_by == identifier, AnalyticsArtifact.status == "active")).all()
    for row in schedules:
        data = json.loads(row.data_json)
        data["is_active"] = False
        data["paused_reason"] = reason
        data["paused_by"] = str(user.user_id)
        row.status = "paused"
        row.data_json = json.dumps(data)
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="PAUSE_REPORT_SCHEDULE_ON_USER_EXIT", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"user_id": str(identifier), "reason": reason})
    delegations = db.scalars(select(DelegationModel).where(DelegationModel.company_id == user.company_id, or_(DelegationModel.principal_id == identifier, DelegationModel.delegate_id == identifier), DelegationModel.revoked_at.is_(None))).all()
    for row in delegations:
        row.revoked_at = now
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REVOKE_DELEGATION_ON_USER_EXIT", entity_type="Delegation", entity_id=row.id, diff={"user_id": str(identifier), "reason": reason})


def candidates(db, user, identifier, group, search=None, limit=20, offset=0):
    definition = groups(db, user.company_id, identifier).get(group)
    if definition is None:
        raise HTTPException(422, "Tipo de responsabilidad desconocido.")
    query = select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id != identifier, UserModel.is_active.is_(True))
    if search and search.strip():
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(or_(UserModel.email.ilike(f"%{escaped}%", escape="\\"), UserModel.full_name.ilike(f"%{escaped}%", escape="\\")))
    eligible = []
    for row in db.scalars(query.order_by(UserModel.full_name, UserModel.email)).all():
        if not set(definition[4]).issubset(set(get_role_permissions(db, user.company_id, row.role) or [])):
            continue
        if definition[5] and not db.scalar(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == row.id, SalesRepresentative.is_active.is_(True))):
            continue
        eligible.append({"id": str(row.id), "name": row.full_name or row.email, "email": row.email, "role": row.role})
    return {"items": eligible[offset:offset + limit], "total_count": len(eligible)}


def transfer_reviews(db, user, identifier, target, row, group):
    if "organization:manage" not in user.permissions:
        raise HTTPException(403, "Reasignar revisores de aprobación requiere administración de la organización además de la gestión de usuarios.")
    field = "config_json" if group == "policy_reviews" else "policy_snapshot_json"
    config = json.loads(getattr(row, field))
    stages = list(range(len(config.get("stages", [])))) if group == "policy_reviews" else pending_review_stages(db, user.company_id, row, identifier)
    if group == "approval_reviews":
        if target.id == row.requested_by:
            raise HTTPException(409, "El solicitante de una aprobación no puede recibir su revisión pendiente.")
        from salesia.modules.operaciones.application.recursos import RESOURCES
        resource = RESOURCES.get(row.resource_type)
        if resource:
            permissions = get_role_permissions(db, user.company_id, target.role) or []
            if resource[3] and resource[3] not in permissions:
                raise HTTPException(422, "El destinatario necesita permiso para la operación del documento que revisará.")
            model = resource[0]
            document = db.scalar(select(model).where(model.company_id == user.company_id, model.id == row.resource_id))
            if document and getattr(document, "created_by", None) == target.id:
                raise HTTPException(409, "El autor del documento no puede recibir la aprobación de su propia operación.")
    for index in stages:
        stage = config["stages"][index]
        if str(identifier) not in stage["approver_ids"]:
            continue
        updated = list(dict.fromkeys(str(target.id) if value == str(identifier) else value for value in stage["approver_ids"]))
        if len(updated) < stage["required_votes"]:
            raise HTTPException(409, "El destinatario ya participa en la etapa y reduciría su quórum. Seleccione otra persona.")
        if group == "approval_reviews" and db.scalar(select(ApprovalVoteModel.id).where(ApprovalVoteModel.company_id == user.company_id, ApprovalVoteModel.approval_id == row.id, ApprovalVoteModel.stage == index, or_(ApprovalVoteModel.actor_id == target.id, ApprovalVoteModel.represented_principal_id == target.id)).limit(1)):
            raise HTTPException(409, "El destinatario ya tiene un voto en esta etapa. Seleccione otra persona para conservar decisiones independientes.")
        stage["approver_ids"] = updated
    setattr(row, field, json.dumps(config))


def apply_transfer(db, user, identifier, group, target_id, definition, reason):
    if target_id == identifier:
        raise HTTPException(422, "El destinatario debe ser otra persona activa.")
    target = member(db, user.company_id, target_id)
    if not target.is_active or not set(definition[4]).issubset(set(get_role_permissions(db, user.company_id, target.role) or [])):
        raise HTTPException(422, "El destinatario no está activo o no tiene permisos para esta responsabilidad.")
    target_rep = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == target_id, SalesRepresentative.is_active.is_(True))) if definition[5] else None
    if definition[5] and target_rep is None:
        raise HTTPException(422, "Seleccione un representante comercial activo como destinatario.")
    rows = rows_for(db, user.company_id, definition, True, group, identifier)
    if group == "supervised_reps":
        ancestor, visited = target_id, set()
        while ancestor and ancestor not in visited:
            if ancestor == identifier:
                raise HTTPException(409, "Seleccione un supervisor fuera de la línea que está traspasando para evitar un ciclo de supervisión.")
            visited.add(ancestor)
            parent = db.scalar(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == ancestor))
            ancestor = parent.supervisor_id if parent else None
    for row in rows:
        previous = snapshot(row)
        if group == "portfolio" and row.backup_sales_rep_id == target_rep.id or group == "backup_portfolio" and row.assigned_sales_rep_id == target_rep.id:
            raise HTTPException(409, "El responsable principal y el respaldo de una cartera deben ser personas distintas. Revise los destinatarios.")
        if group == "supervised_reps" and row.user_id == target_id:
            raise HTTPException(409, "Un vendedor no puede quedar como su propio supervisor.")
        if group == "custody_accounts" and db.scalar(select(CashCustodyTransferModel.id).where(CashCustodyTransferModel.company_id == user.company_id, CashCustodyTransferModel.status.in_(["sent", "disputed", "return_pending"]), or_(CashCustodyTransferModel.source_account_id == row.id, CashCustodyTransferModel.destination_account_id == row.id)).limit(1)):
            raise HTTPException(409, "Resuelva primero los traspasos de efectivo vinculados al punto de custodia antes de cambiar a su responsable.")
        if group in ("policy_reviews", "approval_reviews"):
            transfer_reviews(db, user, identifier, target, row, group)
        elif group == "recurrence_assignees":
            template = json.loads(row.template_json)
            template["assignee_id"] = str(target_id)
            row.template_json = json.dumps(template)
        else:
            setattr(row, definition[2], target_rep.id if target_rep else target.id)
        if group == "portfolio":
            row.sales_team = target_rep.team
        if hasattr(row, "version"):
            row.version += 1
        if group == "draft_sales":
            row.commission_snapshot_json = None
        if group == "recurrence_owners":
            template = json.loads(row.template_json)
            from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskCreateRequest
            from salesia.modules.operaciones.application.planificacion import validate_task_structure
            from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
            target_actor = AuthenticatedUser(user_id=target.id, company_id=user.company_id, email=target.email, role=target.role, permissions=get_role_permissions(db, user.company_id, target.role) or [])
            validate_task_structure(db, target_actor, TaskCreateRequest.model_validate(template))
        if hasattr(row, "history_json"):
            history = json.loads(row.history_json or "[]")
            history.append({"action": "USER_HANDOVER", "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": reason, "from_user_id": str(identifier), "to_user_id": str(target_id), "version": getattr(row, "version", None)})
            row.history_json = json.dumps(history)
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="TRANSFER_USER_RESPONSIBILITY", entity_type=definition[1].__name__, entity_id=row.id, diff={"group": group, "from_user_id": str(identifier), "to_user_id": str(target_id), "reason": reason, "previous": previous, "current": snapshot(row)})
    return len(rows)


def execute(db, user, identifier, payload, key, suspend=False):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    record, cached = claim_request(db, user.company_id, f"user.handover:{identifier}:{suspend}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    source = member(db, user.company_id, identifier, True)
    before = preflight(db, user, identifier)
    if before["preview_hash"] != payload.preview_hash:
        raise HTTPException(409, "Los pendientes o el usuario cambiaron. Actualice la revisión antes de continuar.")
    if not source.is_active:
        raise HTTPException(409, "El usuario ya está inactivo.")
    definitions = groups(db, user.company_id, identifier)
    if set(payload.transfers) - set(definitions):
        raise HTTPException(422, "La solicitud contiene responsabilidades desconocidas.")
    moved = {}
    for group, target_id in payload.transfers.items():
        moved[group] = apply_transfer(db, user, identifier, group, target_id, definitions[group], payload.reason)
        db.flush()
    if suspend:
        assert_ready(db, user, identifier)
        source.is_active = False
        end_operational_access(db, user, identifier, payload.reason)
        db.execute(update(JobModel).where(JobModel.company_id == user.company_id, JobModel.requested_by == identifier, JobModel.status.in_(["pending", "running", "queued"])).values(status="cancelled", cancel_requested=True))
        revoke_user_sessions(db, identifier)
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SUSPEND_USER_AFTER_HANDOVER", entity_type="User", entity_id=source.id, diff={"reason": payload.reason, "transfers": moved, "review": before})
    elif not moved:
        raise HTTPException(422, "Seleccione al menos una responsabilidad para traspasar.")
    db.flush()
    result = {"user_id": str(identifier), "is_active": source.is_active, "transferred": moved, "review": preflight(db, user, identifier)}
    complete_request(record, result)
    db.commit()
    return result
