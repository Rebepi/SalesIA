from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)

    dataset_id: UUID

    dataset_version: Optional[int] = None

    variable_name: str = "total_amount"

    analysis_type: str = "summary"

    parameters: Optional[dict[str, Any]] = None


class AnalysisRepeatRequest(BaseModel):
    new_version: Optional[int] = None

    parameters: Optional[dict[str, Any]] = None
