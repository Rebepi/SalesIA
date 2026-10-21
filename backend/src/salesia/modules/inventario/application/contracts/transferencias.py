from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from salesia.modules.inventario.application.contracts.comunes import StockLine, TransferReceiveItem


class TransferReceiveRequest(BaseModel):
    items: Optional[list[TransferReceiveItem]] = None

    notes: Optional[str] = Field(default=None, max_length=2000)


class TransferCreateRequest(BaseModel):
    source_warehouse_id: UUID

    destination_warehouse_id: UUID

    items: list[StockLine] = Field(min_length=1, max_length=500)

    notes: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def different_warehouses(self):

        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("Los almacenes deben ser distintos")

        return self
