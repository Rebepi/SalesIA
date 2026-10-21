from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application import campos, expedientes
from salesia.modules.operaciones.application import navegacion
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/business", tags=["Expedientes y campos del negocio"])


@router.get("/favorites")
def list_favorites(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return navegacion.favorites(db, user)


@router.put("/favorites/{kind}/{identifier}")
def set_favorite(kind: str, identifier: UUID, payload: navegacion.FavoriteRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return navegacion.set_favorite(db, user, kind, identifier, payload)


@router.get("/record-views")
def list_record_views(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return navegacion.record_views(db, user)


@router.put("/record-views")
def save_record_view(payload: navegacion.RecordViewRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return navegacion.save_record_view(db, user, payload)


@router.delete("/record-views/{identifier}")
def delete_record_view(identifier: UUID, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return navegacion.delete_record_view(db, user, identifier)


@router.get("/resources")
def resource_catalog(user: AuthenticatedUser = Depends(get_current_user)):
    return expedientes.resource_catalog(user)


@router.get("/records/{kind}")
def list_records(kind: str, q: str = Query("", max_length=100), limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), field_key: Optional[str] = None, field_value: Optional[str] = None, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return expedientes.list_records(db, user, kind, q, limit, offset, field_key, field_value)


@router.get("/records/{kind}/{identifier}")
def get_dossier(kind: str, identifier: UUID, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return expedientes.dossier(db, user, kind, identifier)


@router.get("/field-definitions/{kind}")
def list_definitions(kind: str, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return campos.list_definitions(db, user, kind)


@router.put("/field-definitions/{kind}")
def save_definition(kind: str, payload: campos.FieldDefinitionRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return campos.save_definition(db, user, kind, payload, key)


@router.get("/fields/{kind}/{identifier}")
def get_field_values(kind: str, identifier: UUID, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return campos.get_values(db, user, kind, identifier)


@router.put("/fields/{kind}/{identifier}")
def save_field_values(kind: str, identifier: UUID, payload: campos.FieldValuesRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return campos.save_values(db, user, kind, identifier, payload, key)
