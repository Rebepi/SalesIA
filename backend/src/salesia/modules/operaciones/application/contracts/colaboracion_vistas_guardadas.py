from typing import Optional

from pydantic import BaseModel, Field


class SavedViewCreateRequest(BaseModel):
    resource_type: str = Field(min_length=1, max_length=64)

    name: str = Field(min_length=1, max_length=128)

    config_json: str = Field(min_length=2)

    schema_version: int = Field(default=1, ge=1)

    is_shared: bool = False


class SavedViewUpdateRequest(BaseModel):
    name: Optional[str] = None

    config_json: Optional[str] = None

    schema_version: Optional[int] = None

    is_shared: Optional[bool] = None
