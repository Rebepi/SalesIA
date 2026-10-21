from uuid import UUID

from pydantic import BaseModel, Field


class LegalHoldRequest(BaseModel):
    entity_type: str = Field(..., min_length=2)
    entity_id: UUID
    hold_reason: str = Field(..., min_length=5)
    action: str = Field(default="place", pattern="^(place|lift)$")
