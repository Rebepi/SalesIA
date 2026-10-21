from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from salesia.modules.finanzas.infrastructure_models import ReturnLineModel, ReturnModel
from salesia.shared.infrastructure.models import SaleLineModel, SaleModel


def returned_quantity_expression(company_id):
    return (
        select(func.coalesce(func.sum(ReturnLineModel.quantity), 0))
        .join(ReturnModel, ReturnModel.id == ReturnLineModel.return_id)
        .where(ReturnModel.company_id == company_id, ReturnModel.sale_id == SaleModel.id, ReturnModel.status == "accepted")
        .correlate(SaleModel)
        .scalar_subquery()
    )


def sold_quantity_expression(company_id):
    return (
        select(func.coalesce(func.sum(SaleLineModel.quantity), 0))
        .where(SaleLineModel.company_id == company_id, SaleLineModel.sale_id == SaleModel.id)
        .correlate(SaleModel)
        .scalar_subquery()
    )


def sale_return_quantities(db, company_id, sales):
    if not sales:
        return {}
    rows = db.scalars(select(ReturnModel).options(selectinload(ReturnModel.lines)).where(ReturnModel.company_id == company_id, ReturnModel.sale_id.in_([sale.id for sale in sales]), ReturnModel.status == "accepted")).all()
    direct = defaultdict(lambda: Decimal("0"))
    legacy = defaultdict(lambda: Decimal("0"))
    for record in rows:
        for line in record.lines:
            if line.sale_line_id:
                direct[(record.sale_id, line.sale_line_id)] += line.quantity
            else:
                legacy[(record.sale_id, line.product_id)] += line.quantity
    result = {}
    for sale in sales:
        quantities = {}
        for line in sorted(sale.lines, key=lambda item: item.line_number):
            from_legacy = min(max(Decimal("0"), line.quantity - direct[(sale.id, line.id)]), legacy[(sale.id, line.product_id)])
            legacy[(sale.id, line.product_id)] -= from_legacy
            quantities[line.id] = min(line.quantity, direct[(sale.id, line.id)] + from_legacy)
        result[sale.id] = quantities
    return result


def sale_return_status(sale, quantities):
    returned = sum(quantities.values(), Decimal("0"))
    sold = sum((line.quantity for line in sale.lines), Decimal("0"))
    if sale.status == "refunded" or sold > 0 and returned >= sold:
        return "Total"
    return "Parcial" if returned > 0 else "Sin devolución"
