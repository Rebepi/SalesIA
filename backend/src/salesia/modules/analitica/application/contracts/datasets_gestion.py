from typing import Any, Optional

from pydantic import BaseModel, Field

from salesia.modules.analitica.domain.statistics import VariableScale


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)

    description: Optional[str] = None

    variable_scale: VariableScale = VariableScale.QUANTITATIVE_CONTINUOUS

    grain: str = Field(default="ticket", pattern="^(ticket|lines|customer_daily|payments|movements)$")

    source_entity: str = Field(default="sales")

    filters: Optional[dict[str, Any]] = None

    variables: Optional[list[dict[str, Any]]] = None


class DatasetExpireRequest(BaseModel):
    retention_reason: str = Field(default="politica_retencion_vigente", min_length=2)


class SamplingRequest(BaseModel):
    rows: list[dict[str, Any]]

    size: Optional[int] = None

    fraction: Optional[float] = None

    seed: int = 42

    replace: bool = False

    strata_column: Optional[str] = None
