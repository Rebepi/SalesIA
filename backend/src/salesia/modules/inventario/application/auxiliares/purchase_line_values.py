from decimal import ROUND_HALF_EVEN, Decimal

from salesia.modules.inventario.application.contracts.comunes import StockLine


def purchase_line_values(items):

    normalized = []

    commercial = []

    subtotal = Decimal("0")

    taxes = Decimal("0")

    for item in items:
        net = (item.unit_cost * (Decimal("1") - item.discount_percentage / Decimal("100"))).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )

        amount = (net * item.quantity).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        tax = (amount * item.tax_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        normalized.append(StockLine(product_id=item.product_id, quantity=item.quantity, unit_cost=net))

        commercial.append(
            {
                "product_id": str(item.product_id),
                "unit_list_cost": str(item.unit_cost),
                "discount_percentage": str(item.discount_percentage),
                "tax_rate": str(item.tax_rate),
                "subtotal": str(amount),
                "tax_amount": str(tax),
                "total": str(amount + tax),
            }
        )

        subtotal += amount

        taxes += tax

    return normalized, {
        "commercial_lines": commercial,
        "subtotal": str(subtotal),
        "tax_total": str(taxes),
        "total": str(subtotal + taxes),
    }
