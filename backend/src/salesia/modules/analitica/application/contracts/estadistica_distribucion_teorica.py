from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TheoreticalDistributionRequest(BaseModel):
    values: list[Decimal]

    candidate_family: Optional[str] = "normal"
