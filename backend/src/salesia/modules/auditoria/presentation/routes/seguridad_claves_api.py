from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.seguridad_claves_api as service_seguridad_claves_api
from salesia.modules.auditoria.application.contracts.seguridad_claves_api import ApiKeyCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/security/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_seguridad_claves_api.create_api_key(payload=payload, current_user=current_user, db=db)


@router.get("/security/api-keys")
def list_api_keys(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_seguridad_claves_api.list_api_keys(current_user=current_user, db=db)


@router.delete("/security/api-keys/{key_id}")
def revoke_api_key(
    key_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_seguridad_claves_api.revoke_api_key(key_id=key_id, current_user=current_user, db=db)


@router.post("/security/api-keys/verify")
def verify_api_key_endpoint(
    required_scope: Optional[str] = Query(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    return service_seguridad_claves_api.verify_api_key_endpoint(
        required_scope=required_scope, x_api_key=x_api_key, db=db
    )
