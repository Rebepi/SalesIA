from typing import Optional

from pydantic import BaseModel, Field


class CompanyUpdateModel(BaseModel):
    trade_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    base_currency: Optional[str] = Field(default=None, pattern="^[A-Z]{3}$")
