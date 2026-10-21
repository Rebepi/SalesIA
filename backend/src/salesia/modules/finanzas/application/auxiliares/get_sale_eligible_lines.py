import json
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.finanzas.infrastructure_models import ReturnModel
from salesia.modules.catalogo.infrastructure_models import UnitOfMeasureModel
from salesia.shared.infrastructure.models import SaleLineModel, SaleModel
from salesia.modules.finanzas.application.politicas_devolucion import assess, line_policy
from salesia.modules.organizacion.application.periodos import business_date


def _get_sale_eligible_lines(db, sale_id, company_id):
    sale = db.scalar(select(SaleModel).where(SaleModel.id == sale_id, SaleModel.company_id == company_id).with_for_update())
    if sale is None:
        raise HTTPException(404, "Venta no encontrada en la empresa activa.")
    if sale.status not in ("confirmed", "paid"):
        raise HTTPException(422, "La venta no está en un estado apto para devolución.")
    lines = db.scalars(select(SaleLineModel).where(SaleLineModel.company_id == company_id, SaleLineModel.sale_id == sale_id).order_by(SaleLineModel.line_number)).all()
    unit_codes = {getattr(line, "unit_of_measure_snapshot", "NIU").upper() for line in lines}
    units = db.execute(select(UnitOfMeasureModel).where(UnitOfMeasureModel.company_id == company_id, UnitOfMeasureModel.code.in_(unit_codes))).scalars().all()
    fractions = {unit.code.upper(): unit.allow_fractions for unit in units}
    by_line = defaultdict(lambda: Decimal("0"))
    legacy_by_product = defaultdict(lambda: Decimal("0"))
    returned_serials = set()
    returns = db.scalars(select(ReturnModel).where(ReturnModel.company_id == company_id, ReturnModel.sale_id == sale_id, ReturnModel.status.in_(("requested", "accepted")))).all()
    for previous in returns:
        for line in previous.lines:
            if line.sale_line_id:
                by_line[line.sale_line_id] += line.quantity
            else:
                legacy_by_product[line.product_id] += line.quantity
            returned_serials.update(json.loads(line.serial_numbers_json or "[]"))
    result = []
    for line in lines:
        legacy = min(max(Decimal("0"), line.quantity - by_line[line.id]), legacy_by_product[line.product_id])
        legacy_by_product[line.product_id] -= legacy
        returned = by_line[line.id] + legacy
        delivered = line.fulfilled_quantity if line.fulfilled_quantity is not None else line.quantity
        eligible = max(Decimal("0"), min(line.quantity, delivered) - returned)
        net_unit = (line.subtotal_amount / line.quantity).quantize(Decimal("0.000001"))
        snapshot = line_policy(db, sale, line)
        result.append({"unit_of_measure": getattr(line, "unit_of_measure_snapshot", "NIU"), "allow_fractions": fractions.get(getattr(line, "unit_of_measure_snapshot", "NIU").upper(), getattr(line, "unit_of_measure_snapshot", "NIU").upper() not in {"NIU", "UNIT", "UNIDAD", "PIECE", "SERIAL"}), "return_policy": snapshot, "policy_evaluation": assess(snapshot, business_date(db, company_id)), "product_id": line.product_id, "sale_line_id": line.id, "sku": line.sku_snapshot, "product_name": line.name_snapshot, "sold_quantity": line.quantity, "delivered_quantity": delivered, "returned_quantity": returned, "eligible_quantity": eligible, "unit_price_snapshot": net_unit, "unit_cost_snapshot": line.unit_cost_snapshot, "discount_amount": line.discount_amount, "prorated_discount_per_unit": Decimal("0"), "net_unit_price": net_unit, "tax_rate_snapshot": line.tax_rate_snapshot, "serial_numbers": [number for number in json.loads(line.serial_numbers_json or "[]") if number not in returned_serials]})
    return sale, result
