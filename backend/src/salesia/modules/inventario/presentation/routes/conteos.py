from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.conteos as service_conteos
from salesia.modules.inventario.application.contracts.conteos import CountEntriesRequest, PhysicalCountRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/counts")
def list_counts(
    warehouse_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_conteos.list_counts(
        warehouse_id=warehouse_id, status=status, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.post("/inventory/counts", status_code=201)
def create_stock_count(
    payload: PhysicalCountRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_conteos.create_stock_count(payload=payload, current_user=current_user, db=db)


@router.put("/inventory/counts/{count_id}/entries")
def update_count_entries(
    count_id: UUID,
    payload: CountEntriesRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_conteos.update_count_entries(count_id=count_id, payload=payload, current_user=current_user, db=db)


@router.post("/inventory/counts/{count_id}/approve")
def approve_stock_count(
    count_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_conteos.approve_stock_count(
        count_id=count_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
