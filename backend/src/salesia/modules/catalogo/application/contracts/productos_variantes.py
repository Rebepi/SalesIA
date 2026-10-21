from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VariantCreateModel(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    attributes: Dict[str, Any]

    price_delta: Decimal = Field(default=Decimal("0.000000"))
