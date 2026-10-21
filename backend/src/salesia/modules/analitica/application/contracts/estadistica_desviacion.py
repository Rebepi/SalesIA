from decimal import Decimal

from pydantic import BaseModel


class StdevDetailedRequest(BaseModel):
    values: list[Decimal]

    is_sample: bool = True

    variable_unit: str = "USD"
