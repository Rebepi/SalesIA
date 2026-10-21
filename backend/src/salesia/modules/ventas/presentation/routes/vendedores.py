from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

import salesia.modules.ventas.application.vendedores as service_vendedores
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.ventas.application.contracts.vendedores import (
    ReassignPortfolioRequest,
    SalesRepCreateRequest,
    SalesRepUpdateRequest,
)
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/sales")


@router.get("/reps/list")
def list_sales_reps(
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str = Query("", max_length=128),
    period: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_vendedores.list_sales_reps(
        period=period, team=team, branch_id=branch_id, current_user=current_user, db=db, limit=limit, offset=offset, search=search
    )


@router.post("/reps", status_code=status.HTTP_201_CREATED)
def create_sales_rep(
    req: SalesRepCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):

    return service_vendedores.create_sales_rep(req=req, current_user=current_user, db=db)


@router.get("/reps/{rep_id}")
def get_sales_rep(
    rep_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_vendedores.get_sales_rep(rep_id=rep_id, current_user=current_user, db=db)


@router.patch("/reps/{rep_id}")
def update_sales_rep(
    rep_id: UUID,
    req: SalesRepUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):

    return service_vendedores.update_sales_rep(rep_id=rep_id, req=req, current_user=current_user, db=db)


@router.get("/reps/{rep_id}/portfolio")
def preview_sales_rep_portfolio(
    rep_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_vendedores.preview_sales_rep_portfolio(rep_id=rep_id, current_user=current_user, db=db)


@router.post("/reps/{rep_id}/reassign-portfolio")
def reassign_sales_rep_portfolio(
    rep_id: UUID,
    req: ReassignPortfolioRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):

    return service_vendedores.reassign_sales_rep_portfolio(rep_id=rep_id, req=req, current_user=current_user, db=db)
