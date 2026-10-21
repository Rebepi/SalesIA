from decimal import Decimal

from pydantic import BaseModel


class MathExpectationRequest(BaseModel):
    values: list[Decimal]

    probabilities: list[Decimal]

    is_continuous: bool = False
