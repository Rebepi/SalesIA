from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.ventas.application.metas as service_metas
from salesia.modules.ventas.application import metas_combinadas as combined
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.ventas.application.contracts.metas import SalesTargetCreateRequest
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/sales")


@router.post("/targets", status_code=status.HTTP_201_CREATED)
def create_sales_target(
    req: SalesTargetCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):

    return service_metas.create_sales_target(req=req, current_user=current_user, db=db)


@router.get("/targets")
def list_sales_targets(
    period: Optional[str] = Query(None),
    representative_id: Optional[UUID] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_metas.list_sales_targets(
        period=period, representative_id=representative_id, current_user=current_user, db=db
    )


@router.get("/performance-targets")
def list_performance_targets(period: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), current_user: AuthenticatedUser = Depends(require_permission("sales:read", "organization:manage")), db: Session = Depends(get_db)):
    return combined.list_targets(db, current_user, period, limit, offset)


@router.post("/performance-targets")
def save_performance_target(payload: combined.CombinedTargetSave, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return combined.save_target(db, current_user, payload, idempotency_key)
