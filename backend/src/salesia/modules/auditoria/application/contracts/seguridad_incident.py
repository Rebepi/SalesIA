from uuid import UUID

from pydantic import BaseModel, Field


class UserQuarantineRequest(BaseModel):
    user_id: UUID
    incident_ticket: str = Field(..., min_length=3)
    reason: str = Field(..., min_length=5)
