from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    resource_type: str = Field(min_length=1, max_length=64)

    resource_id: UUID

    content: str = Field(min_length=1, max_length=5000)

    mentions: list[UUID] = []


class CommentUpdateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
