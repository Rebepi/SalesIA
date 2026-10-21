from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CollectionActivityRequest(BaseModel):
    adjust_to_operating_calendar: bool = False
    kind: Literal["contact", "dispute", "promise", "agreement", "reminder"]

    notes: str = Field(min_length=3, max_length=2000)

    promised_amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=6)

    next_action_at: Optional[datetime] = None
