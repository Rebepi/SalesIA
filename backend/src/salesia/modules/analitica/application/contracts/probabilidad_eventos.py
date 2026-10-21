from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.analitica.application.contracts.comunes import EventDefinitionModel, UniverseDefinitionModel


class ProbabilityEventsRequest(BaseModel):
    event_a_count: Optional[int] = Field(default=None, ge=0)

    event_b_count: Optional[int] = Field(default=None, ge=0)

    intersection_count: Optional[int] = Field(default=None, ge=0)

    sample_space_size: Optional[int] = Field(default=None, ge=0)

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    universe_definition: Optional[UniverseDefinitionModel] = None

    event_a_definition: Optional[EventDefinitionModel] = None

    event_b_definition: Optional[EventDefinitionModel] = None

    min_support_threshold: int = Field(default=30, ge=1)

    predictor_fields: Optional[list[str]] = None

    predictor_window_end: Optional[str] = None

    outcome_window_start: Optional[str] = None


class TemporalLeakageValidationRequest(BaseModel):
    predictor_fields: list[str] = Field(..., min_length=1)

    predictor_window_end: Optional[str] = None

    outcome_window_start: Optional[str] = None


class ScenarioCompareRequest(BaseModel):
    analysis_id_1: UUID

    analysis_id_2: UUID


class HypothesisTestRequest(BaseModel):
    count_1: int = Field(..., ge=0)

    total_1: int = Field(..., gt=0)

    count_2: int = Field(..., ge=0)

    total_2: int = Field(..., gt=0)

    confidence_level: Decimal = Field(default=Decimal("0.95"), ge=Decimal("0.80"), le=Decimal("0.999"))


class PreregisterHypothesisRequest(BaseModel):
    hypothesis_id: str

    h0: str

    h1: str

    variable: str

    group_a: str

    group_b: str

    direction: str = "two_sided"

    alpha: Decimal = Decimal("0.05")

    test_type: str = "welch_t"


class OperationalLiveCountsRequest(BaseModel):
    entity: str = Field(default="sales")
    period: str = Field(default="all")
    condition_a: str = Field(default="with_balance")
    condition_b: str = Field(default="high_amount")
    threshold_amount: Decimal = Field(default=Decimal("200"))