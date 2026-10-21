from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class KitItemCreateModel(BaseModel):
    component_product_id: UUID

    quantity: Decimal = Field(..., gt=0)
