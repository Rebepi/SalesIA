from typing import Any, Optional

from pydantic import BaseModel, Field


class DatasetVersionCreateRequest(BaseModel):
    row_count: Optional[int] = Field(default=None, ge=0)

    data_hash: Optional[str] = Field(default=None, min_length=8)

    schema_snapshot: Optional[dict[str, Any]] = None

    watermark: Optional[str] = None

    cutoff_date: Optional[str] = None

    parameters: Optional[dict[str, Any]] = None


class OperationalDatasetExtractRequest(BaseModel):
    grain: str = Field(default="ticket", pattern="^(ticket|lines|customer_daily)$")

    limit: int = Field(default=100, ge=1, le=1000)
