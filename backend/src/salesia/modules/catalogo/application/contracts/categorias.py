from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)

    code: Optional[str] = Field(default=None, min_length=2, max_length=64)

    parent_id: Optional[UUID] = None

    sort_order: int = Field(default=0, ge=0)


class CategoryUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    code: Optional[str] = Field(default=None, min_length=2, max_length=64)

    parent_id: Optional[UUID] = None

    sort_order: Optional[int] = Field(default=None, ge=0)

    is_active: Optional[bool] = None


class CategoryRestoreRequest(BaseModel):
    category_ids: list[UUID] = Field(min_length=1, max_length=5000)
