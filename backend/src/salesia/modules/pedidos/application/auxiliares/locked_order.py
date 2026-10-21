from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CompanyModel, OrderModel


def locked_order(db, user, order_id):
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())

    row = db.scalar(
        select(OrderModel).where(OrderModel.id == order_id, OrderModel.company_id == user.company_id).with_for_update()
    )

    if not row:
        other = db.scalar(select(OrderModel.id).where(OrderModel.id == order_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Pedido no encontrado.")

    return row
