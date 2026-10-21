from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.cupones import CouponCreateModel, CouponValidateRequest
from salesia.modules.catalogo.infrastructure_models import CouponModel
from salesia.modules.catalogo.service import ensure_utc
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException


def create_coupon(req: CouponCreateModel, current_user: AuthenticatedUser, db: Session):
    normalized = req.code.strip().upper()

    existing = db.execute(
        select(CouponModel).where(CouponModel.company_id == current_user.company_id, CouponModel.code == normalized)
    ).scalar_one_or_none()

    if existing:
        raise DomainConflictException(f"Ya existe un cupón con el código '{normalized}'.")

    c = CouponModel(
        id=uuid4(),
        company_id=current_user.company_id,
        code=normalized,
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        min_purchase_amount=req.min_purchase_amount,
        start_date=req.start_date,
        end_date=req.end_date,
        max_uses=req.max_uses,
        current_uses=0,
        is_active=True,
    )

    db.add(c)

    db.commit()

    return {
        "id": str(c.id),
        "code": c.code,
        "discount_type": c.discount_type,
        "discount_value": str(c.discount_value),
        "max_uses": c.max_uses,
    }


def validate_coupon_endpoint(req: CouponValidateRequest, current_user: AuthenticatedUser, db: Session):
    normalized = req.code.strip().upper()

    now = datetime.now(timezone.utc)

    coupon = db.execute(
        select(CouponModel).where(
            CouponModel.company_id == current_user.company_id,
            CouponModel.code == normalized,
            CouponModel.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if not coupon:
        raise DomainNotFoundException("Cupón no válido o inexistente.")

    start = ensure_utc(coupon.start_date)

    end = ensure_utc(coupon.end_date)

    if now < start or now > end:
        raise DomainConflictException("El cupón se encuentra fuera de su periodo de vigencia.")

    if coupon.current_uses >= coupon.max_uses:
        raise DomainConflictException("El cupón ha agotado su cupo máximo de usos.")

    if req.amount < coupon.min_purchase_amount:
        raise DomainConflictException(f"Monto mínimo de compra no alcanzado (mínimo: {coupon.min_purchase_amount}).")

    discount = (
        (req.amount * coupon.discount_value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        if coupon.discount_type == "PERCENTAGE"
        else min(req.amount, coupon.discount_value)
    )

    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": str(coupon.discount_value),
        "calculated_discount": str(discount),
    }
