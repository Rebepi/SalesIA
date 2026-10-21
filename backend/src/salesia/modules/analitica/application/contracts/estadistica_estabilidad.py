from decimal import Decimal

from pydantic import BaseModel


class NumericalStabilityRequest(BaseModel):
    values: list[Decimal]

    oracle_comparison: bool = True
