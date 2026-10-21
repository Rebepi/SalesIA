from typing import Any, Optional

from pydantic import BaseModel, Field


class AiQueryRequest(BaseModel):
    query: str = Field(..., min_length=2)

    context: Optional[dict[str, Any]] = None


class AiSimulationRequest(BaseModel):
    action_type: str = Field(..., min_length=2)

    parameters: dict[str, Any] = Field(default_factory=dict)


class EmergencyPauseRequest(BaseModel):
    reason: str = Field(..., min_length=3)
