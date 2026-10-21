from sqlalchemy import select

from salesia.shared.infrastructure.models import ProductModel, SaleLineModel, SaleModel


def sale_row(sale, value=None, **extra):
    return {"id": str(sale.id), "documento": f"{sale.series}-{sale.number}", "sede": str(sale.branch_id), "moneda": sale.currency, "estado": sale.status, "importe": str(sale.total_amount if value is None else value), **extra}


def sales(db, user, filters):
    return [sale_row(sale) for sale in db.scalars(select(SaleModel).where(*filters).order_by(SaleModel.id)).all()]


def lines(db, user, commercial_ids, zero_only=False):
    query = select(SaleLineModel, SaleModel, ProductModel).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).join(ProductModel, ProductModel.id == SaleLineModel.product_id).where(SaleLineModel.company_id == user.company_id, SaleModel.company_id == user.company_id, ProductModel.company_id == user.company_id, SaleLineModel.sale_id.in_(commercial_ids))
    if zero_only:
        query = query.where(SaleLineModel.unit_cost_snapshot <= 0)
    return [sale_row(sale, line.total_amount, id=str(line.id), venta_id=str(sale.id), producto=product.name, sku=product.sku, cantidad=str(line.quantity), costo_unitario=str(line.unit_cost_snapshot), base_comercial=str(line.subtotal_amount), costo_total=str(line.quantity * line.unit_cost_snapshot)) for line, sale, product in db.execute(query.order_by(SaleLineModel.id)).all()]
