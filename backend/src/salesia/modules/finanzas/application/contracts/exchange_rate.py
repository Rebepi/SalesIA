from decimal import Decimal

from pydantic import BaseModel, Field


class CurrencyConvertRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)

    from_currency: str = Field(..., min_length=3, max_length=3)

    to_currency: str = Field(..., min_length=3, max_length=3)

    exchange_rate: Decimal = Field(..., gt=0)
