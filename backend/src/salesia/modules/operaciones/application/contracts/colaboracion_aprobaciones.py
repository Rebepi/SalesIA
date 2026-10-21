from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovalCreateRequest(BaseModel):
    resource_type: str = Field(min_length=1, max_length=64)

    resource_id: UUID

    document_version: int = Field(ge=1)

    policy_name: str = Field(min_length=1, max_length=128)

    evidence_json: Optional[str] = None


class ApprovalDecideRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")

    reason: str = Field(min_length=1, max_length=500)

    current_document_version: int = Field(ge=1)
