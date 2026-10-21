from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ImportJobCreateRequest(BaseModel):
    target_entity: str = Field(pattern="^(customers|products|inventory_adjustments)$")

    attachment_id: UUID

    delimiter: Optional[str] = Field(default=None, pattern="^[,;\t|]$")

    encoding: Optional[str] = Field(default=None, pattern="^(utf-8-sig|utf-8|cp1252)$")

    column_mapping: dict[str, str] = Field(default_factory=dict, max_length=100)

    corrections: dict[str, dict[str, str]] = Field(default_factory=dict, max_length=5000)

    source_import_id: Optional[UUID] = None
