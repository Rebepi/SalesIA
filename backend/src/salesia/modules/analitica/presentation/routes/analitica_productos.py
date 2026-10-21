from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_productos as service_analitica_productos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/analytics/products")
def get_product_analytics(
    period: str = "30d",
    category: Optional[str] = None,
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    limit: int = 50,
    metric: str = "revenue",
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_analitica_productos.get_product_analytics(
        period=period,
        category=category,
        branch_id=branch_id,
        currency=currency,
        limit=limit,
        metric=metric,
        current_user=current_user,
        db=db,
    )
