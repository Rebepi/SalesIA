from uuid import UUID

from pydantic import BaseModel, Field


class WarehouseCreateModel(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
