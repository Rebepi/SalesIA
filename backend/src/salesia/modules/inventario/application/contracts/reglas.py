from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class StockRuleRequest(BaseModel):
    warehouse_id: UUID

    product_id: UUID

    min_quantity: Decimal = Field(ge=0, decimal_places=6)

    max_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)

    reorder_point: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)

    reorder_quantity: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)

    @model_validator(mode="after")
    def consistent_limits(self):

        if self.max_quantity and self.max_quantity < max(self.min_quantity, self.reorder_point):
            raise ValueError("El máximo debe ser mayor o igual al mínimo y al punto de pedido.")

        return self
