from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_ventas as service_analitica_ventas
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/analytics/sales")
def get_sales_analytics(
    period: str = "30d",
    granularity: str = "day",
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_ventas.get_sales_analytics(
        period=period,
        granularity=granularity,
        branch_id=branch_id,
        currency=currency,
        category=category,
        current_user=current_user,
        db=db,
    )
