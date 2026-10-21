from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.promociones as service_promociones
from salesia.modules.catalogo.application.contracts.promociones import PromotionCreateModel, PromotionUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/promotions", status_code=status.HTTP_201_CREATED)
def create_promotion(
    req: PromotionCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_promociones.create_promotion(req=req, current_user=current_user, db=db)


@router.get("/promotions")
def list_promotions(
    current_user: AuthenticatedUser = Depends(require_permission("products:read")), db: Session = Depends(get_db)
):

    return service_promociones.list_promotions(current_user=current_user, db=db)


@router.patch("/promotions/{promo_id}")
def update_promotion(
    promo_id: UUID,
    req: PromotionUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_promociones.update_promotion(promo_id=promo_id, req=req, current_user=current_user, db=db)


@router.delete("/promotions/{promo_id}")
def delete_promotion(
    promo_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_promociones.delete_promotion(promo_id=promo_id, current_user=current_user, db=db)
