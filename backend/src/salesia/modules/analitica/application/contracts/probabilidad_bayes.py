from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class BayesCalculationRequest(BaseModel):
    prior_a: Optional[Decimal] = Field(default=None, ge=0, le=100)

    likelihood_b_given_a: Optional[Decimal] = Field(default=None, ge=0, le=100)

    likelihood_b_given_not_a: Optional[Decimal] = Field(default=None, ge=0, le=100)

    evidence_b: Optional[Decimal] = Field(default=None, ge=0, le=100)

    mode: str = Field(default="proportion", pattern="^(proportion|percentage)$")

    sample_space_size: Optional[int] = Field(default=None, ge=0)

    event_a_count: Optional[int] = Field(default=None, ge=0)

    event_b_count: Optional[int] = Field(default=None, ge=0)

    intersection_count: Optional[int] = Field(default=None, ge=0)

    smoothing_enabled: bool = Field(default=False)

    alpha: Decimal = Field(default=Decimal("1.0"), ge=0)

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    min_support_threshold: int = Field(default=30, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self):

        if self.mode == "proportion":
            if self.prior_a is not None and self.prior_a > Decimal("1"):
                raise ValueError("En modo proporcion prior_a debe estar en [0, 1]")

            if self.likelihood_b_given_a is not None and self.likelihood_b_given_a > Decimal("1"):
                raise ValueError("En modo proporcion likelihood_b_given_a debe estar en [0, 1]")

            if self.likelihood_b_given_not_a is not None and self.likelihood_b_given_not_a > Decimal("1"):
                raise ValueError("En modo proporcion likelihood_b_given_not_a debe estar en [0, 1]")

            if self.evidence_b is not None and self.evidence_b > Decimal("1"):
                raise ValueError("En modo proporcion evidence_b debe estar en [0, 1]")

        return self


class SmoothedBayesRequest(BaseModel):
    count_a_and_b: int = Field(..., ge=0)

    count_not_a_and_b: int = Field(..., ge=0)

    total_a: int = Field(..., gt=0)

    total_not_a: int = Field(..., gt=0)

    prior_a: Decimal = Field(..., ge=0, le=1)

    alpha: Decimal = Field(default=Decimal("1.0"), ge=0)
