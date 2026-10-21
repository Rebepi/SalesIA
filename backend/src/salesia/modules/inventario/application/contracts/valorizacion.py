from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    product_id: Optional[UUID] = None

    costing_method: Literal["AVERAGE_WEIGHTED", "FIFO", "STANDARD"] = "AVERAGE_WEIGHTED"

    rounding_decimals: int = Field(default=6, ge=2, le=6)
