from decimal import Decimal

from pydantic import BaseModel, Field


class AdvancedStatisticsRequest(BaseModel):
    values: list[Decimal] = Field(..., min_length=1)

    is_sample: bool = Field(default=True)
