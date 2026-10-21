from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, Field


class ReportRunRequest(BaseModel):
    report_type: str = Field(..., min_length=2, validation_alias=AliasChoices("report_type", "template_code"))

    parameters: dict[str, Any] = Field(default_factory=dict)

    format: str = Field(default="csv", pattern="^(csv|json|pdf|xlsx)$")

    limit: int = Field(default=50000, ge=1, le=50000)

    async_execution: bool = Field(default=False)

    timezone: Optional[str] = Field(default="America/Lima")

    currency: Optional[str] = Field(default=None)
