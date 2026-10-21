import calendar
import json
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskCreateRequest
from salesia.modules.operaciones.application.recursos import entity
from salesia.modules.operaciones.infrastructure.models.planificacion import TaskOccurrenceModel, TaskRecurrenceModel
from salesia.modules.operaciones.infrastructure_models import CollaborationTask, Notification
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class TaskRecurrenceRequest(BaseModel):
    task: TaskCreateRequest
    frequency: Literal["daily", "weekly", "monthly"]
    interval: int = Field(default=1, ge=1, le=365)
    timezone: str = "America/Lima"
    until: Optional[date] = None
    skip_dates: list[date] = Field(default_factory=list, max_length=366)

    @model_validator(mode="after")
    def valid_schedule(self):
        try:
            ZoneInfo(self.timezone)
        except (ValueError, KeyError):
            raise ValueError("La zona horaria no es válida.")
        if not self.task.due_date or self.task.due_date.tzinfo is None or self.task.due_date <= datetime.now(timezone.utc):
            raise ValueError("La primera ocurrencia debe tener fecha futura con zona horaria.")
        if self.until and self.until < self.task.due_date.astimezone(ZoneInfo(self.timezone)).date():
            raise ValueError("La serie termina antes de su primera ocurrencia.")
        return self


def validate_task_structure(db, user, payload, current=None):
    if payload.resource_type or payload.resource_id:
        if not payload.resource_type or not payload.resource_id:
            raise HTTPException(422, "El vínculo de tarea requiere tipo e identificador de recurso.")
        entity(db, user, payload.resource_type, payload.resource_id)
    parent_id = getattr(payload, "parent_id", None)
    if parent_id:
        parent = entity(db, user, "task", parent_id, write=True)
        if parent.status in ("completed", "cancelled"):
            raise HTTPException(409, "No añadas subtareas a una actividad cerrada.")
    if payload.dependencies is not None:
        if len(set(payload.dependencies)) != len(payload.dependencies):
            raise HTTPException(422, "No repitas dependencias.")
        current_id = current.id if current else None
        pending = list(payload.dependencies)
        visited = set()
        while pending:
            identifier = pending.pop()
            if identifier == current_id:
                raise HTTPException(422, "La dependencia genera un ciclo entre tareas.")
            if identifier in visited:
                continue
            visited.add(identifier)
            if len(visited) > 1000:
                raise HTTPException(422, "La cadena de dependencias supera el límite de 1000 tareas.")
            dependency = entity(db, user, "task", identifier)
            if dependency.parent_id == current_id and current_id:
                raise HTTPException(422, "Una tarea no puede depender de su propia subtarea.")
            pending.extend(UUID(value) for value in json.loads(dependency.dependencies_json or "[]"))


def require_task_completion(db, user, task):
    if any(not item["done"] for item in json.loads(task.checklist_json or "[]")):
        raise HTTPException(409, "Completa la lista de comprobación antes de cerrar la tarea.")
    children = db.scalar(select(CollaborationTask.id).where(CollaborationTask.company_id == user.company_id, CollaborationTask.parent_id == task.id, CollaborationTask.status.notin_(("completed", "cancelled"))).limit(1))
    if children:
        raise HTTPException(409, "La tarea tiene subtareas pendientes.")
    for identifier in json.loads(task.dependencies_json or "[]"):
        dependency = db.scalar(select(CollaborationTask).where(CollaborationTask.company_id == user.company_id, CollaborationTask.id == UUID(identifier)))
        if dependency is None or dependency.status != "completed":
            raise HTTPException(409, "Falta completar una tarea de la que depende esta actividad.")


def next_occurrence(previous, config):
    zone = ZoneInfo(config["timezone"])
    local = previous.astimezone(zone)
    interval = config["interval"]
    if config["frequency"] == "monthly":
        ordinal = local.year * 12 + local.month - 1 + interval
        year, month = divmod(ordinal, 12)
        day = min(config["anchor_day"], calendar.monthrange(year, month + 1)[1])
        candidate = local.replace(year=year, month=month + 1, day=day)
    else:
        candidate = local + timedelta(days=interval * (7 if config["frequency"] == "weekly" else 1))
    if config.get("until") and candidate.date() > date.fromisoformat(config["until"]):
        return None
    return candidate.astimezone(timezone.utc)


def create_recurrence(db, user, payload, key):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    record, cached = claim_request(db, user.company_id, "tasks.recurrence.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    validate_task_structure(db, user, payload.task)
    if payload.task.assignee_id:
        target = db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == payload.task.assignee_id, UserModel.is_active.is_(True)))
        if target is None:
            raise HTTPException(422, "El responsable no está activo.")
    config = payload.model_dump(mode="json", exclude={"task"})
    config["anchor_day"] = payload.task.due_date.astimezone(ZoneInfo(payload.timezone)).day
    row = TaskRecurrenceModel(company_id=user.company_id, owner_id=user.user_id, template_json=json.dumps(payload.task.model_dump(mode="json")), schedule_json=json.dumps(config), next_due_at=payload.task.due_date, is_active=True)
    db.add(row)
    db.flush()
    result = {"id": str(row.id), "next_due_at": row.next_due_at.isoformat()}
    complete_request(record, result)
    db.commit()
    return result


def process_task_recurrences(limit=100, at=None):
    from salesia.shared.infrastructure.database import sync_session_factory
    from salesia.shared.infrastructure.tenant_scope import bind_company
    current = at or datetime.now(timezone.utc)
    processed = 0
    with sync_session_factory() as db:
        companies = db.scalars(select(CompanyModel.id).where(CompanyModel.is_active.is_(True))).all()
    for company_id in companies:
        if processed >= limit:
            break
        with sync_session_factory() as db:
            bind_company(db, company_id)
            db.scalar(select(CompanyModel).where(CompanyModel.id == company_id).with_for_update())
            rules = db.scalars(select(TaskRecurrenceModel).where(TaskRecurrenceModel.company_id == company_id, TaskRecurrenceModel.is_active.is_(True), TaskRecurrenceModel.next_due_at <= current).order_by(TaskRecurrenceModel.next_due_at).limit(limit - processed).with_for_update(skip_locked=True)).all()
            for rule in rules:
                template, config = json.loads(rule.template_json), json.loads(rule.schedule_json)
                due = rule.next_due_at.replace(tzinfo=timezone.utc) if rule.next_due_at.tzinfo is None else rule.next_due_at
                exists = db.scalar(select(TaskOccurrenceModel.id).where(TaskOccurrenceModel.company_id == company_id, TaskOccurrenceModel.recurrence_id == rule.id, TaskOccurrenceModel.due_at == due))
                if exists:
                    rule.next_due_at = next_occurrence(due, config)
                    rule.is_active = rule.next_due_at is not None
                    continue
                owner = db.scalar(select(UserModel).where(UserModel.company_id == company_id, UserModel.id == rule.owner_id, UserModel.is_active.is_(True)))
                assignee_id = UUID(template["assignee_id"]) if template.get("assignee_id") else None
                assignee = db.scalar(select(UserModel).where(UserModel.company_id == company_id, UserModel.id == assignee_id, UserModel.is_active.is_(True))) if assignee_id else None
                if owner is None or (assignee_id and assignee is None):
                    rule.is_active = False
                    continue
                from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
                from salesia.modules.seguridad.infrastructure.sessions import permissions_for
                actor = AuthenticatedUser(user_id=owner.id, company_id=company_id, email=owner.email, role=owner.role, permissions=permissions_for(db, owner))
                try:
                    validate_task_structure(db, actor, TaskCreateRequest.model_validate(template))
                except HTTPException:
                    rule.is_active = False
                    db.add(Notification(company_id=company_id, user_id=owner.id, title="Serie periódica pausada", message="Una relación o permiso de la actividad dejó de estar disponible. Revisa la serie antes de reanudarla.", event_type="TASK_SERIES_PAUSED", category="operations"))
                    continue
                local_date = due.astimezone(ZoneInfo(config["timezone"])).date().isoformat()
                if local_date in config.get("skip_dates", []):
                    db.add(TaskOccurrenceModel(company_id=company_id, recurrence_id=rule.id, due_at=due, status="skipped"))
                else:
                    task = CollaborationTask(company_id=company_id, title=template["title"], description=template.get("description"), assignee_id=assignee_id, creator_id=rule.owner_id, due_date=due, priority=template["priority"], resource_type=template.get("resource_type"), resource_id=UUID(template["resource_id"]) if template.get("resource_id") else None, parent_id=UUID(template["parent_id"]) if template.get("parent_id") else None, checklist_json=json.dumps([{**item, "done": False} for item in template.get("checklist", [])]), dependencies_json=json.dumps(template.get("dependencies", [])), recurrence_id=rule.id, status="pending", version=1)
                    db.add(task)
                    db.flush()
                    db.add(TaskOccurrenceModel(company_id=company_id, recurrence_id=rule.id, task_id=task.id, due_at=due, status="created"))
                    db.add(Notification(company_id=company_id, user_id=assignee_id or rule.owner_id, title="Actividad periódica disponible", message=task.title, event_type="TASK_OCCURRENCE_CREATED", resource_type="task", resource_id=task.id, category="operations"))
                rule.next_due_at = next_occurrence(due, config)
                rule.is_active = rule.next_due_at is not None
                processed += 1
            db.commit()
    return processed
