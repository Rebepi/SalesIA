from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from salesia.modules.analitica.application import perspectivas_operacion as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/analytics/operating-perspective")


@router.get("")
def operating_perspective(start: date, end: date, basis: Literal["sale", "collection", "delivery"] = "sale", currency: str | None = None, branch_id: UUID | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("analytics:dataset:read")), db: Session = Depends(get_db)):
    try:
        payload = service.PerspectiveRequest(start=start, end=end, basis=basis, currency=currency, branch_id=branch_id, limit=limit, offset=offset)
    except ValidationError as error:
        raise HTTPException(422, "; ".join(item["msg"] for item in error.errors()))
    return service.calculate(db, user, payload)


@router.get("/options")
def operating_perspective_options(user: AuthenticatedUser = Depends(require_permission("analytics:dataset:read")), db: Session = Depends(get_db)):
    return service.options(db, user)
