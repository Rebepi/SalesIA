from typing import Optional

from pydantic import BaseModel, Field


class LoyaltyAccrualModel(BaseModel):
    points: int = Field(..., gt=0)
    reference_type: str = Field(default="sale", max_length=32)
    reference_id: Optional[str] = None
    reason: Optional[str] = None


class LoyaltyReversalModel(BaseModel):
    points: int = Field(..., gt=0)
    reference_type: str = Field(default="refund", max_length=32)
    reference_id: str = Field(..., min_length=1, max_length=128)
    reason: Optional[str] = None
