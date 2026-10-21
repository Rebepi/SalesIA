from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_sellers as service_analitica_sellers
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/analytics/sellers")
def get_seller_analytics(
    period: str = "30d",
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_sellers.get_seller_analytics(
        period=period, branch_id=branch_id, currency=currency, category=category, current_user=current_user, db=db
    )
