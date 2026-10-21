from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import historial as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/history")
def get_customer_history(
    customer_id: UUID,
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_customer_history(
        customer_id=customer_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        db=db,
    )
