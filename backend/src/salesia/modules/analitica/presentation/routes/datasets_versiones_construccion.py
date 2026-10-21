from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.datasets_versiones_construccion as service_datasets_versiones_construccion
from salesia.modules.analitica.application.contracts.datasets_versiones_construccion import (
    DatasetVersionCreateRequest,
    OperationalDatasetExtractRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/datasets/{dataset_id}/versions", status_code=status.HTTP_201_CREATED)
def create_dataset_version(
    dataset_id: UUID,
    payload: Optional[DatasetVersionCreateRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_versiones_construccion.create_dataset_version(
        dataset_id=dataset_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/datasets/{dataset_id}/versions")
def list_dataset_versions(
    dataset_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_datasets_versiones_construccion.list_dataset_versions(
        dataset_id=dataset_id, current_user=current_user, db=db
    )


@router.get("/datasets/{dataset_id}/versions/{version}")
def get_dataset_version(
    dataset_id: UUID,
    version: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_versiones_construccion.get_dataset_version(
        dataset_id=dataset_id, version=version, current_user=current_user, db=db
    )


@router.delete("/datasets/{dataset_id}/versions/{version}")
def delete_dataset_version(
    dataset_id: UUID,
    version: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_versiones_construccion.delete_dataset_version(
        dataset_id=dataset_id, version=version, current_user=current_user, db=db
    )


@router.post("/datasets/{dataset_id}/rebuild")
def rebuild_dataset(
    dataset_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_datasets_versiones_construccion.rebuild_dataset(
        dataset_id=dataset_id, current_user=current_user, db=db
    )


@router.post("/datasets/extract-operational")
def extract_operational_dataset(
    payload: OperationalDatasetExtractRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_datasets_versiones_construccion.extract_operational_dataset(
        payload=payload, current_user=current_user, db=db
    )
