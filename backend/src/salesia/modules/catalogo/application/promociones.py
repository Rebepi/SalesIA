from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.promociones import PromotionCreateModel, PromotionUpdateModel
from salesia.modules.catalogo.infrastructure_models import PromotionModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_promotion(req: PromotionCreateModel, current_user: AuthenticatedUser, db: Session):
    promo = PromotionModel(
        id=uuid4(),
        company_id=current_user.company_id,
        name=req.name,
        code=req.code,
        priority=req.priority,
        is_exclusive=req.is_exclusive,
        start_date=req.start_date,
        end_date=req.end_date,
        product_id=req.product_id,
        min_quantity=req.min_quantity,
        discount_percentage=req.discount_percentage,
        max_quota=req.max_quota,
        current_uses=0,
        is_active=True,
    )

    db.add(promo)

    db.commit()

    return {
        "id": str(promo.id),
        "code": promo.code,
        "name": promo.name,
        "discount_percentage": str(promo.discount_percentage),
        "is_exclusive": promo.is_exclusive,
        "max_quota": promo.max_quota,
    }


def list_promotions(current_user: AuthenticatedUser, db: Session):
    query = (
        select(PromotionModel)
        .where(PromotionModel.company_id == current_user.company_id)
        .order_by(PromotionModel.priority.desc())
    )

    rows = db.scalars(query).all()

    return [
        {
            "id": str(pr.id),
            "code": pr.code,
            "name": pr.name,
            "priority": pr.priority,
            "is_exclusive": pr.is_exclusive,
            "start_date": pr.start_date.isoformat()
            if hasattr(pr.start_date, "isoformat")
            else (str(pr.start_date) if pr.start_date else None),
            "end_date": pr.end_date.isoformat()
            if hasattr(pr.end_date, "isoformat")
            else (str(pr.end_date) if pr.end_date else None),
            "product_id": str(pr.product_id) if pr.product_id else None,
            "min_quantity": pr.min_quantity,
            "discount_percentage": str(pr.discount_percentage) if pr.discount_percentage is not None else "0",
            "max_quota": pr.max_quota,
            "current_uses": pr.current_uses,
            "is_active": pr.is_active,
        }
        for pr in rows
    ]


def update_promotion(promo_id: UUID, req: PromotionUpdateModel, current_user: AuthenticatedUser, db: Session):
    promo = db.execute(
        select(PromotionModel).where(
            PromotionModel.id == promo_id, PromotionModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()

    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promoción no encontrada")

    if req.is_active is not None:
        promo.is_active = req.is_active

    if req.name is not None:
        promo.name = req.name

    if req.priority is not None:
        promo.priority = req.priority

    if req.is_exclusive is not None:
        promo.is_exclusive = req.is_exclusive

    if req.max_quota is not None:
        promo.max_quota = req.max_quota

    if req.end_date is not None:
        promo.end_date = req.end_date

    db.commit()

    db.refresh(promo)

    return {
        "id": str(promo.id),
        "code": promo.code,
        "name": promo.name,
        "priority": promo.priority,
        "is_exclusive": promo.is_exclusive,
        "is_active": promo.is_active,
        "current_uses": promo.current_uses,
        "max_quota": promo.max_quota,
    }


def delete_promotion(promo_id: UUID, current_user: AuthenticatedUser, db: Session):
    promo = db.execute(
        select(PromotionModel).where(
            PromotionModel.id == promo_id, PromotionModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()

    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promoción no encontrada")

    if promo.current_uses > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la promoción '{promo.code}' porque ya tiene {promo.current_uses} transacciones registradas. Desactívela para suspender su aplicación sin alterar el historial contable.",
        )

    db.delete(promo)

    db.commit()

    return {"message": f"Promoción '{promo.code}' eliminada exitosamente", "id": str(promo_id)}
