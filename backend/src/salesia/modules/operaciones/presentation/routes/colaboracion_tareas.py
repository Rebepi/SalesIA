from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.colaboracion_tareas as service_colaboracion_tareas
from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskCreateRequest, TaskUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/collaboration/tasks", status_code=201)
def create_task(
    payload: TaskCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_tareas.create_task(payload=payload, current_user=current_user, db=db)


@router.get("/collaboration/tasks")
def list_tasks(
    status: Optional[str] = None,
    assignee_id: Optional[UUID] = None,
    search: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_tareas.list_tasks(
        status=status, assignee_id=assignee_id, search=search, current_user=current_user, db=db
    )


@router.patch("/collaboration/tasks/{task_id}")
def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_colaboracion_tareas.update_task(task_id=task_id, payload=payload, current_user=current_user, db=db)


@router.delete("/collaboration/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_colaboracion_tareas.delete_task(task_id=task_id, current_user=current_user, db=db)
