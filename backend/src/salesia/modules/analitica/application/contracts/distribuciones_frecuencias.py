from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FrequenciesRequest(BaseModel):
    values: Optional[list[Any]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_name: Optional[str] = None

    order: Optional[list[str]] = None


class DistributionRequest(BaseModel):
    values: Optional[list[Decimal]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_name: Optional[str] = None

    num_bins: Optional[int] = Field(default=None, ge=1, le=100)

    bin_width: Optional[Decimal] = None

    bin_policy: str = Field(default="sturges", pattern="^(sturges|sqrt|manual)$")


class OutliersAnalysisRequest(BaseModel):
    values: list[Decimal] = Field(..., min_length=1)

    null_policy: str = Field(default="skip", pattern="^(skip|error|zero)$")
