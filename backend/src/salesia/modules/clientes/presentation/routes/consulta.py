from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import consulta as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("")
def list_customers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sales_rep_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: Optional[str] = Query(None),
    order: Literal["recent", "random"] = Query("recent"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_customers(
        search=search,
        status=status,
        is_active=is_active,
        sales_rep_id=sales_rep_id,
        limit=limit,
        offset=offset,
        cursor=cursor,
        order=order,
        current_user=current_user,
        db=db,
    )


@router.get("/{customer_id}")
def get_customer(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_customer(customer_id=customer_id, current_user=current_user, db=db)
