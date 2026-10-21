from pydantic import BaseModel, Field

from salesia.modules.pedidos.application.contracts.comunes import FulfilledItem


class OrderFulfillPartialModel(BaseModel):
    fulfilled_items: list[FulfilledItem] = Field(min_length=1, max_length=500)
