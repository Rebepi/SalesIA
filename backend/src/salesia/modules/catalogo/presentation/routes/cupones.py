from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.cupones as service_cupones
from salesia.modules.catalogo.application.contracts.cupones import CouponCreateModel, CouponValidateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/coupons", status_code=status.HTTP_201_CREATED)
def create_coupon(
    req: CouponCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_cupones.create_coupon(req=req, current_user=current_user, db=db)


@router.post("/coupons/validate")
def validate_coupon_endpoint(
    req: CouponValidateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_cupones.validate_coupon_endpoint(req=req, current_user=current_user, db=db)
