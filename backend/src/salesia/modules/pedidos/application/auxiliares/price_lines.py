from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.pedidos.application.auxiliares.money import money
from salesia.shared.infrastructure.models import ProductModel


def price_lines(db, company_id, requested):

    ids = [item.product_id for item in requested]

    products = db.scalars(
        select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.id.in_(ids))
    ).all()

    by_id = {row.id: row for row in products}

    if len(by_id) != len(set(ids)):
        raise HTTPException(422, "Uno o más productos no existen en esta empresa.")

    lines, subtotal, tax_total = [], Decimal("0"), Decimal("0")

    for item in requested:
        product = by_id[item.product_id]

        gross = money(item.quantity * product.unit_price)

        net = money(gross - money(gross * item.discount_pct / Decimal("100")))

        tax = money(net * product.tax_rate)

        subtotal += net

        tax_total += tax

        lines.append(
            {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "quantity": str(money(item.quantity)),
                "unit_price": str(product.unit_price),
                "unit_cost": str(product.unit_cost),
                "discount_pct": str(item.discount_pct),
                "tax_rate": str(product.tax_rate),
                "line_subtotal": str(net),
                "line_tax": str(tax),
                "reserved_quantity": "0.000000",
                "fulfilled_quantity": "0.000000",
            }
        )

    subtotal, tax_total = money(subtotal), money(tax_total)

    return lines, subtotal, tax_total, money(subtotal + tax_total)
