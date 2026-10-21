from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.datasets_gestion as service_datasets_gestion
from salesia.modules.analitica.application.contracts.datasets_gestion import (
    DatasetCreateRequest,
    DatasetExpireRequest,
    SamplingRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_gestion.create_dataset(payload=payload, current_user=current_user, db=db)


@router.get("/datasets")
def list_datasets(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_datasets_gestion.list_datasets(current_user=current_user, db=db)


@router.get("/datasets/{dataset_id}")
def get_dataset(
    dataset_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_datasets_gestion.get_dataset(dataset_id=dataset_id, current_user=current_user, db=db)


@router.post("/datasets/{dataset_id}/versions/{version}/expire")
def expire_dataset_version(
    dataset_id: UUID,
    version: int,
    payload: Optional[DatasetExpireRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_gestion.expire_dataset_version(
        dataset_id=dataset_id, version=version, payload=payload, current_user=current_user, db=db
    )


@router.post("/datasets/sample")
def post_dataset_sample(payload: SamplingRequest):

    return service_datasets_gestion.post_dataset_sample(payload=payload)
