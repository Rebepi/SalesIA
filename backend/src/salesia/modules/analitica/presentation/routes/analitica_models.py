from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_models as service_analitica_models
from salesia.modules.analitica.application.contracts.analitica_models import ModelMonitorRequest, ModelRegisterRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/analytics/models", status_code=status.HTTP_201_CREATED)
def post_model_registration(
    payload: ModelRegisterRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_models.post_model_registration(payload=payload, current_user=current_user, db=db)


@router.get("/analytics/models")
def get_models_list(
    name: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_models.get_models_list(name=name, current_user=current_user, db=db)


@router.get("/analytics/models/{model_id}")
def get_model_by_id(
    model_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_analitica_models.get_model_by_id(model_id=model_id, current_user=current_user, db=db)


@router.post("/analytics/models/{model_id}/monitor")
def post_model_monitoring(
    model_id: UUID,
    payload: ModelMonitorRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_models.post_model_monitoring(
        model_id=model_id, payload=payload, current_user=current_user, db=db
    )
