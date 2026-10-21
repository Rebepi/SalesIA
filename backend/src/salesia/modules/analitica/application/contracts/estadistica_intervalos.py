from decimal import Decimal

from pydantic import BaseModel


class ConfidenceIntervalRequest(BaseModel):
    values: list[Decimal]

    confidence_level: Decimal = Decimal("0.95")

    method: str = "student_t"
