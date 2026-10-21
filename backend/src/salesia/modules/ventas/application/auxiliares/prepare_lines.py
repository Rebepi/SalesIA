import json
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.catalogo.service import resolve_product_price, validate_unit_fraction
from salesia.shared.infrastructure.models import ProductModel, SaleLineModel
from salesia.modules.ventas.application.pedidos_facturacion import locked_billing_order, validate_billing_capacity


def prepare_lines(db, payload, company_id, sale_id):

    lines = []

    explanations = []
    source = None
    source_lines = {}
    if payload.order_id:
        source = locked_billing_order(db, company_id, payload.order_id)
        if (str(source.customer_id), str(source.branch_id), str(source.warehouse_id), source.currency) != (str(payload.customer_id), str(payload.branch_id), str(payload.warehouse_id), payload.currency.upper()):
            raise HTTPException(422, "Conserva el cliente, sede, almacén y moneda del pedido al facturarlo.")
        if payload.coupon_code:
            raise HTTPException(422, "Modifica los descuentos en el pedido antes de facturarlo; su venta conserva el precio acordado.")
        source_lines = validate_billing_capacity(db, company_id, source, payload.lines, sale_id)

    for index, item in enumerate(payload.lines, 1):
        query = select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.is_active.is_(True))

        query = (
            query.where(ProductModel.id == item.product_id)
            if item.product_id
            else query.where(ProductModel.sku == item.sku)
        )

        product = db.scalar(query)

        if not product:
            raise HTTPException(422, "Producto inexistente, inactivo o de otra empresa.")

        prof = db.scalar(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == company_id, ProductProfileModel.product_id == product.id
            )
        )

        if prof and prof.status in ("archived", "suspended"):
            raise HTTPException(422, f"El producto {product.sku} se encuentra {prof.status} y no puede venderse.")

        validate_unit_fraction(db, company_id, product.unit_of_measure, Decimal(str(item.quantity)))

        quantity = Decimal(item.quantity)

        pricing = None
        if not source:
            pricing = resolve_product_price(db, company_id, product.id, quantity, payload.customer_id, coupon_code=payload.coupon_code)
        if source:
            original = source_lines[item.order_line_number]
            original_quantity = Decimal(original["quantity"])
            net_unit = Decimal(original["line_subtotal"]) / original_quantity
            net_subtotal = (net_unit * quantity).quantize(Decimal("0.000001"))
            tax_amount = (Decimal(original["line_tax"]) / original_quantity * quantity).quantize(Decimal("0.000001"))
            pricing = {"product_id": str(product.id), "sku": product.sku, "quantity": str(quantity), "final_unit_price": str(net_unit), "subtotal": str(net_subtotal), "tax_amount": str(tax_amount), "discount_applied": str(max(Decimal("0"), (Decimal(original["unit_price"]) - net_unit) * quantity)), "rules_applied": [{"rule_type": "ORDER_PRICE", "order_id": str(source.id), "order_number": source.order_number, "line_number": item.order_line_number}]}

        final_unit_price = Decimal(pricing["final_unit_price"])

        net = Decimal(pricing["subtotal"])

        tax = Decimal(pricing["tax_amount"])

        discount = Decimal(pricing["discount_applied"])

        selected_serials = [value.strip() for value in item.serial_numbers if value.strip()]

        if len(selected_serials) != len(set(selected_serials)):
            raise HTTPException(422, f"La selección de series de {product.sku} contiene valores repetidos.")

        if not source and selected_serials and (quantity != quantity.to_integral_value() or len(selected_serials) != int(quantity)):
            raise HTTPException(422, f"Selecciona una serie distinta por cada unidad de {product.sku}.")

        lines.append(
            SaleLineModel(
                id=uuid4(),
                company_id=company_id,
                sale_id=sale_id,
                product_id=product.id,
                line_number=index,
                sku_snapshot=product.sku,
                name_snapshot=product.name,
                unit_of_measure_snapshot=product.unit_of_measure,
                quantity=quantity,
                unit_price_snapshot=final_unit_price,
                unit_cost_snapshot=product.unit_cost,
                discount_amount=discount,
                tax_rate_snapshot=Decimal(original["tax_rate"]) if source else product.tax_rate,
                subtotal_amount=net,
                tax_amount=tax,
                total_amount=net + tax,
                serial_numbers_json=json.dumps(selected_serials),
                warranty_months_snapshot=prof.warranty_period_months if prof else 0,
                warranty_policy_snapshot=prof.warranty_policy if prof else None,
                order_line_number=item.order_line_number if source else None,
                fulfilled_quantity=Decimal("0"),
            )
        )

        explanations.append(pricing)

    return lines, explanations
