from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import CountEntry, StockLine


class PhysicalCountRequest(BaseModel):
    warehouse_id: UUID

    scope: Literal["FULL", "CATEGORY", "LOCATION", "CYCLE"] = "FULL"

    scope_filter: Optional[str] = Field(default=None, max_length=128)

    is_blind: bool = True

    items: Optional[list[StockLine]] = None

    notes: Optional[str] = Field(default=None, max_length=2000)

    product_ids: Optional[list[UUID]] = Field(default=None, min_length=1, max_length=5000)


class CountEntriesRequest(BaseModel):
    items: list[CountEntry] = Field(min_length=1, max_length=5000)

    submit: bool = False

    version: int = Field(ge=1)
