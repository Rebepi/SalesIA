from typing import Optional

from pydantic import BaseModel, Field


class IntegrationCreateRequest(BaseModel):
    __module__ = "salesia.modules.operations.presentation.router"
    provider: str = Field(min_length=2, max_length=64, pattern="^[a-zA-Z0-9_-]+$")
    category: str = Field(default="payments", min_length=2, max_length=64, pattern="^[a-zA-Z0-9_-]+$")
    mode: str = Field(default="test", pattern="^(test|live)$")
    credential: str = Field(min_length=8, max_length=4096)


class IntegrationCredentialRequest(BaseModel):
    credential: str = Field(min_length=8, max_length=4096)

    schedule_start: Optional[str] = None

    schedule_end: Optional[str] = None


class IntegrationModeRequest(BaseModel):
    mode: str = Field(pattern="^(test|live)$")
