from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.pedidos.application.contracts.pedidos_registro import DocumentLine


class QuotationCreateModel(BaseModel):
    customer_id: UUID

    branch_id: Optional[UUID] = None

    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")

    valid_until: Optional[datetime] = None

    payment_terms_days: int = Field(default=30, ge=0, le=3650)

    delivery_terms: Optional[str] = None

    notes: Optional[str] = None

    special_conditions: Optional[str] = None

    seller_id: Optional[UUID] = None

    is_draft: bool = Field(default=False)

    lines: list[DocumentLine] = Field(default_factory=list, max_length=500)
