from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogCreateRequest(BaseModel):
    action: str = Field(..., min_length=2)
    entity_type: str = Field(..., min_length=2)
    entity_id: UUID
    payload_diff: dict[str, Any] = Field(default_factory=dict)


class AuditRetentionPurgeRequest(BaseModel):
    category: str = Field(default="GENERAL")
    retention_days: int = Field(default=365, ge=30)
