from pydantic import BaseModel, Field


class SupportGrantCreateRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=255)
    scope: str = Field(pattern="^(diagnostics|audit|full_support)$")
    duration_minutes: int = Field(default=60, ge=5, le=480)
