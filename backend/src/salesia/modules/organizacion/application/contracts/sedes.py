from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class BranchCreateModel(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Zona horaria desconocida")
        return value


class BranchUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = Field(default=None, max_length=2000)
