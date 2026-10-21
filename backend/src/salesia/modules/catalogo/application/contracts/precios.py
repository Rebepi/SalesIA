from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PricePreviewRequest(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(..., gt=0)

    customer_id: Optional[UUID] = None

    variant_id: Optional[UUID] = None

    coupon_code: Optional[str] = None
