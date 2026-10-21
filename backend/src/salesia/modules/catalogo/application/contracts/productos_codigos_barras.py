from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BarcodeCreateModel(BaseModel):
    barcode: str = Field(..., min_length=3, max_length=64)

    barcode_type: str = Field(default="EAN13", max_length=32)

    variant_id: Optional[UUID] = None
