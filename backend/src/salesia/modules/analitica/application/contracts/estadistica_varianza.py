from decimal import Decimal

from pydantic import BaseModel


class VarianceDetailedRequest(BaseModel):
    values: list[Decimal]

    is_sample: bool = True

    variable_unit: str = "USD"
