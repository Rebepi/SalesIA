from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class MeanRequest(BaseModel):
    values: Optional[list[Decimal]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_name: Optional[str] = "total_amount"

    null_policy: str = Field(default="skip", pattern="^(skip|error|zero)$")

    record_run: bool = False

    @model_validator(mode="after")
    def validate_values_not_empty(self):

        if self.values is not None and len(self.values) == 0:
            raise ValueError("La lista de valores no puede estar vacia")

        return self


class MedianRequest(BaseModel):
    values: Optional[list[Decimal]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_name: Optional[str] = "total_amount"

    null_policy: str = Field(default="skip", pattern="^(skip|error|zero)$")

    record_run: bool = False


class DescriptiveSummaryRequest(BaseModel):
    dataset_id: UUID

    dataset_version: Optional[int] = None

    variable_name: str = Field(default="total_amount", min_length=1, max_length=128)

    null_policy: str = Field(default="skip", pattern="^(skip|error|zero)$")

    precision: int = Field(default=4, ge=0, le=12)


class CompareRequest(BaseModel):
    label_a: str = Field(default="Serie A")

    values_a: Optional[list[Decimal]] = None

    label_b: str = Field(default="Serie B")

    values_b: Optional[list[Decimal]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_a: Optional[str] = None

    variable_b: Optional[str] = None


class WeightedMeanRequest(BaseModel):
    values: list[Decimal] = Field(..., min_length=1)

    weights: list[Decimal] = Field(..., min_length=1)

    method: str = Field(default="weighted_by_units", pattern="^(weighted_by_units|simple_average_per_sale)$")
