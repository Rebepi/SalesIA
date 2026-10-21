from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.analitica.application.contracts.comunes import EventDefinitionModel, UniverseDefinitionModel


class ProbabilityAnalysisSaveRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    universe_definition: Optional[UniverseDefinitionModel] = None

    event_a_definition: Optional[EventDefinitionModel] = None

    event_b_definition: Optional[EventDefinitionModel] = None

    mode: str = Field(default="proportion", pattern="^(proportion|percentage)$")

    counts: Optional[dict[str, int]] = None

    probabilities: Optional[dict[str, Any]] = None

    smoothing_enabled: bool = Field(default=False)

    alpha: Decimal = Field(default=Decimal("1.0"))

    is_simulation: bool = Field(default=False)

    scenario_type: str = Field(default="observed", pattern="^(observed|simulation)$")


class DuplicateScenarioRequest(BaseModel):
    scenario_name: str = Field(..., min_length=2, max_length=128)

    modified_prior_a: Optional[Decimal] = Field(default=None, ge=0, le=100)

    modified_evidence_b: Optional[Decimal] = Field(default=None, ge=0, le=100)

    modified_likelihood_b_given_a: Optional[Decimal] = Field(default=None, ge=0, le=100)

    modified_alpha: Optional[Decimal] = Field(default=None, ge=0)

    smoothing_enabled: Optional[bool] = None
