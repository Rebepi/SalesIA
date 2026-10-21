from decimal import ROUND_HALF_EVEN, Decimal

from salesia.modules.finanzas.application.contracts.exchange_rate import CurrencyConvertRequest


def convert_currency(payload: CurrencyConvertRequest):
    converted = (payload.amount * payload.exchange_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    return {
        "original_amount": str(payload.amount),
        "from_currency": payload.from_currency,
        "to_currency": payload.to_currency,
        "exchange_rate": str(payload.exchange_rate),
        "converted_amount": str(converted),
    }
