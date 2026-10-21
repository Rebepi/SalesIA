from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import StockLine


class DeliveryCreateRequest(BaseModel):
    sale_id: UUID

    warehouse_id: UUID

    recipient_name: str = Field(min_length=2, max_length=255)

    delivery_address: str = Field(min_length=3, max_length=500)

    recipient_phone: Optional[str] = Field(default=None, max_length=64)

    carrier: str = Field(min_length=2, max_length=128)

    tracking_number: Optional[str] = Field(default=None, max_length=128)

    tracking_url: Optional[str] = Field(default=None, max_length=500)

    shipping_fee_charged: Decimal = Field(default=Decimal("0.000000"), ge=0, decimal_places=6)

    logistics_cost: Decimal = Field(default=Decimal("0.000000"), ge=0, decimal_places=6)

    estimated_delivery_date: Optional[datetime] = None

    is_guaranteed: bool = False

    items: Optional[list[StockLine]] = None

    notes: Optional[str] = Field(default=None, max_length=1000)


class DeliveryInterceptRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class DeliveryCompleteRequest(BaseModel):
    outside_window_reason: str = Field(default="", max_length=2000)

    received_by_id_doc: Optional[str] = Field(default=None, max_length=64)

    proof_of_delivery: str = Field(min_length=3, max_length=255)

    received_by_name: str = Field(min_length=2, max_length=128)
