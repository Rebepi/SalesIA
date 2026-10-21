from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.pedidos.application.contracts.pedidos_registro import DocumentLine


class QuotationVersionModel(BaseModel):
    lines: list[DocumentLine] = Field(min_length=1, max_length=500)

    valid_until: Optional[datetime] = None

    delivery_terms: Optional[str] = None

    notes: Optional[str] = None

    special_conditions: Optional[str] = None

    seller_id: Optional[UUID] = None


class AcceptQuotationRequest(BaseModel):
    conditions: Optional[str] = None
