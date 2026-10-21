from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_clientes as service_analitica_clientes
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/analytics/customers")
def get_customer_analytics(
    period: str = "30d",
    branch_id: Optional[UUID] = None,
    category: Optional[str] = None,
    segment: Optional[str] = None,
    currency: Optional[str] = None,
    limit: int = 50,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_clientes.get_customer_analytics(
        period=period,
        branch_id=branch_id,
        category=category,
        segment=segment,
        currency=currency,
        limit=limit,
        current_user=current_user,
        db=db,
    )
