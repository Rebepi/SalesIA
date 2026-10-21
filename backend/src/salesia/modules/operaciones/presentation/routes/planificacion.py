import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.planificacion import TaskRecurrenceRequest, create_recurrence
from salesia.modules.operaciones.infrastructure.models.planificacion import TaskRecurrenceModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/collaboration/task-series")


@router.get("")
def list_task_series(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    statement = select(TaskRecurrenceModel).where(TaskRecurrenceModel.company_id == user.company_id)
    if "operations:manage" not in user.permissions:
        statement = statement.where(TaskRecurrenceModel.owner_id == user.user_id)
    return [{"id": str(row.id), "title": json.loads(row.template_json)["title"], "schedule": json.loads(row.schedule_json), "next_due_at": row.next_due_at.isoformat() if row.next_due_at else None, "is_active": row.is_active} for row in db.scalars(statement.order_by(TaskRecurrenceModel.created_at.desc())).all()]


@router.post("", status_code=201)
def create_task_series(payload: TaskRecurrenceRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return create_recurrence(db, user, payload, key)


@router.post("/{identifier}/{action}")
def change_task_series(identifier: UUID, action: Literal["pause", "resume"], user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(TaskRecurrenceModel).where(TaskRecurrenceModel.company_id == user.company_id, TaskRecurrenceModel.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Serie de tareas no encontrada.")
    if row.owner_id != user.user_id and "operations:manage" not in user.permissions:
        raise HTTPException(403, "No tienes autorización para modificar esta serie.")
    if action == "resume" and row.next_due_at is None:
        raise HTTPException(409, "La serie terminó y no tiene más ocurrencias.")
    row.is_active = action == "resume"
    db.commit()
    return {"id": str(row.id), "is_active": row.is_active}
