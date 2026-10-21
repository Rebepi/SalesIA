from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.devoluciones_consulta as service_devoluciones_consulta
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/returns/sales/{sale_id}/eligible")
def get_sale_return_eligibility(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_consulta.get_sale_return_eligibility(sale_id=sale_id, current_user=current_user, db=db)


@router.get("/returns", operation_id="inventory_list_returns")
def list_returns(
    sale_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_consulta.list_returns(sale_id=sale_id, status=status, current_user=current_user, db=db)


@router.get("/returns/{return_id}", operation_id="inventory_get_return")
def get_return(
    return_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_consulta.get_return(return_id=return_id, current_user=current_user, db=db)
