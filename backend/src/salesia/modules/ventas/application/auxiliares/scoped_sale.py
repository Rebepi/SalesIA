import json

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import OrderModel, SaleModel


def scoped_sale(db, sale_id, user, lock=False):

    query = select(SaleModel).where(SaleModel.id == sale_id, SaleModel.company_id == user.company_id)

    if lock:
        source_order = db.scalar(select(SaleModel.order_id).where(SaleModel.id == sale_id, SaleModel.company_id == user.company_id))
        if source_order:
            db.scalar(select(OrderModel).where(OrderModel.id == source_order, OrderModel.company_id == user.company_id).with_for_update())
        query = query.with_for_update()

    sale = db.scalar(query)

    if sale is None:
        other = db.scalar(select(SaleModel.id).where(SaleModel.id == sale_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Venta no encontrada.")

    if user.role == "salesperson":
        rep = db.scalar(
            select(SalesRepresentative).where(
                SalesRepresentative.company_id == user.company_id,
                SalesRepresentative.user_id == user.user_id,
                SalesRepresentative.is_active.is_(True),
            )
        )

        if rep and sale.sales_rep_id and sale.sales_rep_id != rep.id:
            participants = json.loads(sale.commission_snapshot_json or "{}").get("participants", [])
            if lock or not any(row["representative_id"] == str(rep.id) for row in participants):
                raise DomainForbiddenException("No tiene permisos para acceder a ventas de otros vendedores.")

    return sale
