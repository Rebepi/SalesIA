import json
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskCreateRequest, TaskUpdateRequest
from salesia.modules.operaciones.infrastructure_models import CollaborationTask
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CompanyModel, CustomerModel, OrderModel, ProductModel, SaleModel, UserModel
from salesia.modules.operaciones.application.planificacion import require_task_completion, validate_task_structure


def create_task(payload: TaskCreateRequest, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    validate_task_structure(db, current_user, payload)
    if payload.assignee_id:
        target = db.scalar(
            select(UserModel).where(
                UserModel.id == payload.assignee_id, UserModel.company_id == current_user.company_id
            )
        )

        if not target or not target.is_active:
            raise HTTPException(422, "No se puede asignar una tarea a una membresía inactiva o inexistente.")

    task = CollaborationTask(
        company_id=current_user.company_id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
        creator_id=current_user.user_id,
        due_date=payload.due_date,
        priority=payload.priority,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        status="pending",
        parent_id=payload.parent_id,
        checklist_json=json.dumps([item.model_dump() for item in payload.checklist]),
        dependencies_json=json.dumps([str(identifier) for identifier in payload.dependencies]),
        version=1,
        created_at=now(),
        updated_at=now(),
    )

    db.add(task)

    db.commit()

    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


def list_tasks(
    status: Optional[str],
    assignee_id: Optional[UUID],
    search: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
):
    q = select(CollaborationTask).where(CollaborationTask.company_id == current_user.company_id)

    if current_user.role not in ("company_admin", "manager", "platform_admin") and "operations:manage" not in current_user.permissions:
        q = q.where((CollaborationTask.creator_id == current_user.user_id) | (CollaborationTask.assignee_id == current_user.user_id))

    if status:
        q = q.where(CollaborationTask.status == status)

    if assignee_id:
        q = q.where(CollaborationTask.assignee_id == assignee_id)

    if search:
        pattern = f"%{search}%"

        q = q.where(or_(CollaborationTask.title.ilike(pattern), CollaborationTask.description.ilike(pattern)))

    rows = db.scalars(q.order_by(CollaborationTask.created_at.desc())).all()

    results = []

    for r in rows:
        assignee_active = True

        if r.assignee_id:
            assignee = db.scalar(select(UserModel.is_active).where(UserModel.id == r.assignee_id))

            assignee_active = bool(assignee)

        res_name = None

        if r.resource_type == "customer" and r.resource_id:
            res_name = db.scalar(select(CustomerModel.legal_name).where(CustomerModel.id == r.resource_id))

        elif r.resource_type == "order" and r.resource_id:
            res_name = db.scalar(select(OrderModel.order_number).where(OrderModel.id == r.resource_id))

        elif r.resource_type == "product" and r.resource_id:
            res_name = db.scalar(
                select(ProductModel.name).where(
                    ProductModel.id == r.resource_id, ProductModel.company_id == current_user.company_id
                )
            )

        elif r.resource_type == "sale" and r.resource_id:
            sale = db.scalar(
                select(SaleModel).where(SaleModel.id == r.resource_id, SaleModel.company_id == current_user.company_id)
            )

            res_name = f"{sale.series}-{sale.number:08d}" if sale else None

        results.append(
            {
                "id": str(r.id),
                "title": r.title,
                "description": r.description,
                "status": r.status,
                "priority": r.priority,
                "due_date": r.due_date.isoformat() if r.due_date else None,
                "assignee_id": str(r.assignee_id) if r.assignee_id else None,
                "creator_id": str(r.creator_id) if r.creator_id else None,
                "resource_type": r.resource_type,
                "resource_id": str(r.resource_id) if r.resource_id else None,
                "resource_name": res_name,
                "resolution_notes": r.resolution_notes,
                "assignee_active": assignee_active,
                "inactive_assignee_warning": not assignee_active,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "parent_id": str(r.parent_id) if r.parent_id else None,
                "checklist": json.loads(r.checklist_json or "[]"),
                "dependencies": json.loads(r.dependencies_json or "[]"),
                "recurrence_id": str(r.recurrence_id) if r.recurrence_id else None,
                "version": r.version,
            }
        )

    return {"items": results, "total_count": len(results)}


def update_task(task_id: UUID, payload: TaskUpdateRequest, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    task = db.scalar(
        select(CollaborationTask)
        .where(CollaborationTask.id == task_id, CollaborationTask.company_id == current_user.company_id)
        .with_for_update()
    )

    if not task:
        raise HTTPException(404, "Tarea no encontrada.")

    is_authorized = (
        task.assignee_id == current_user.user_id
        or task.creator_id == current_user.user_id
        or current_user.role in ("company_admin", "manager", "platform_admin")
        or "operations:manage" in current_user.permissions
        or "approvals:manage" in current_user.permissions
    )

    if not is_authorized:
        raise DomainForbiddenException("No tiene permiso para modificar esta tarea.")

    if payload.version is not None and task.version != payload.version:
        raise HTTPException(409, "La tarea cambió; recarga antes de guardarla.")
    validate_task_structure(db, current_user, payload, task)
    if payload.checklist is not None:
        task.checklist_json = json.dumps([item.model_dump() for item in payload.checklist])
    if payload.dependencies is not None:
        task.dependencies_json = json.dumps([str(identifier) for identifier in payload.dependencies])
    if payload.status == "completed":
        require_task_completion(db, current_user, task)
    if task.status in ("completed", "cancelled") and payload.status and payload.status != task.status and not payload.resolution_notes:
        raise HTTPException(422, "Indica el motivo para reabrir una actividad cerrada.")
    task.version += 1

    if payload.assignee_id:
        target = db.scalar(
            select(UserModel).where(
                UserModel.id == payload.assignee_id, UserModel.company_id == current_user.company_id
            )
        )

        if not target or not target.is_active:
            raise HTTPException(422, "No se puede reasignar a una membresía inactiva.")

        task.assignee_id = payload.assignee_id

    if "assignee_id" in payload.model_fields_set and payload.assignee_id is None:
        task.assignee_id = None

    if payload.title is not None:
        task.title = payload.title

    if payload.description is not None:
        task.description = payload.description

    if "due_date" in payload.model_fields_set:
        task.due_date = payload.due_date

    if payload.status:
        task.status = payload.status

    if payload.priority:
        task.priority = payload.priority

    if payload.resolution_notes:
        task.resolution_notes = payload.resolution_notes

    if payload.resource_type is not None:
        task.resource_type = payload.resource_type

    if payload.resource_id is not None:
        task.resource_id = payload.resource_id

    task.updated_at = now()

    db.commit()

    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "creator_id": str(task.creator_id) if task.creator_id else None,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "resolution_notes": task.resolution_notes,
        "resource_type": task.resource_type,
        "resource_id": str(task.resource_id) if task.resource_id else None,
    }


def delete_task(task_id: UUID, current_user: AuthenticatedUser, db: Session):
    task = db.scalar(
        select(CollaborationTask)
        .where(CollaborationTask.id == task_id, CollaborationTask.company_id == current_user.company_id)
        .with_for_update()
    )

    if not task:
        raise HTTPException(404, "Tarea no encontrada.")

    is_authorized = (
        task.assignee_id == current_user.user_id
        or task.creator_id == current_user.user_id
        or current_user.role in ("company_admin", "manager", "platform_admin")
        or "operations:manage" in current_user.permissions
        or "approvals:manage" in current_user.permissions
    )

    if not is_authorized:
        raise DomainForbiddenException("No tiene permiso para eliminar esta tarea.")

    child = db.scalar(select(CollaborationTask.id).where(CollaborationTask.company_id == current_user.company_id, CollaborationTask.parent_id == task.id).limit(1))
    if child or task.recurrence_id:
        raise HTTPException(409, "Conserva la tarea con subtareas o recurrencia. Cancélala para mantener el historial.")
    dependencies = db.scalars(select(CollaborationTask.dependencies_json).where(CollaborationTask.company_id == current_user.company_id)).all()
    if any(str(task.id) in json.loads(value or "[]") for value in dependencies):
        raise HTTPException(409, "Otras tareas dependen de esta actividad. Conserva su historial y resuelve sus vínculos.")
    db.delete(task)

    db.commit()

    return None
