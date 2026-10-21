from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.importaciones as service_importaciones
from salesia.modules.operaciones.application.contracts.importaciones import ImportJobCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/imports/inspect")
def inspect_import(
    payload: ImportJobCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_importaciones.inspect_import(payload=payload, current_user=current_user, db=db)


@router.post("/imports", status_code=202)
def create_import_job(
    payload: ImportJobCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_importaciones.create_import_job(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/imports")
def list_import_jobs(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_importaciones.list_import_jobs(current_user=current_user, db=db)


@router.post("/imports/{import_id}/commit", status_code=202)
def commit_import_job(
    import_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):

    return service_importaciones.commit_import_job(
        import_id=import_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
