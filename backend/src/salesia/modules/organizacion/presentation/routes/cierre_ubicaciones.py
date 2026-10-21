from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application import cierre_ubicaciones as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/organization/locations")


@router.get("/{kind}/{identifier}/retirement")
def location_retirement_preview(kind: Literal["branch", "warehouse"], identifier: UUID, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.preview(db, user.company_id, kind, identifier)


@router.post("/{kind}/{identifier}/retirement")
def retire_location(kind: Literal["branch", "warehouse"], identifier: UUID, payload: service.RetirementRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.retire(db, user, kind, identifier, payload, key)


@router.post("/{kind}/{identifier}/reactivation")
def reactivate_location(kind: Literal["branch", "warehouse"], identifier: UUID, payload: service.RetirementRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.reactivate(db, user, kind, identifier, payload, key)
