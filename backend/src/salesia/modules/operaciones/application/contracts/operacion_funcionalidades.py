from pydantic import BaseModel, Field


class FeatureToggleRequest(BaseModel):
    flag_key: str = Field(pattern="^[a-z][a-z0-9_]{1,63}$")

    enabled: bool
