from decimal import ROUND_HALF_EVEN, Decimal


def money(value):

    return Decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
