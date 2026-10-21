from typing import Optional

from pydantic import BaseModel, Field


class CustomerImportModel(BaseModel):
    import_batch_key: str = Field(..., min_length=1, max_length=128)
    dry_run: bool = False
    on_duplicate: str = Field(default="skip", pattern="^(skip|update|error)$")
    rows: list[dict] = Field(..., min_length=1, max_length=1000)


class CustomerExportModel(BaseModel):
    format: str = Field(default="json", pattern="^(json|csv)$")
    reason: str = Field(..., min_length=3, max_length=255)
    filters: Optional[dict] = None
    include_sensitive: bool = False
