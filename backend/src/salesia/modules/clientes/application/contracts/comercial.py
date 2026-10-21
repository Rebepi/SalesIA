from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCommercialTermsModel(BaseModel):
    price_list_id: Optional[str] = None
    payment_terms_days: int = Field(default=30, ge=0, le=365)
    preferred_currency: str = Field(default="USD", min_length=3, max_length=3)
    credit_limit: Decimal = Field(default=Decimal("0.000000"), ge=0)
    is_credit_blocked: bool = False
    credit_block_until: Optional[datetime] = None
    credit_block_reason: Optional[str] = None


class CreditCheckRequest(BaseModel):
    amount: Decimal = Field(..., ge=0)


class CustomerAssignmentModel(BaseModel):
    assigned_sales_rep_id: Optional[UUID] = None
    sales_team: Optional[str] = None
    backup_sales_rep_id: Optional[UUID] = None
    reason: Optional[str] = None


class CustomerSegmentCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    min_frequency: int = 0
    min_spend: Decimal = Decimal("0.000000")
    max_recency_days: int = 3650
    zone: Optional[str] = None


class CustomerNoteCreateModel(BaseModel):
    category: str = Field(default="comercial", pattern="^(comercial|personal|interno)$")
    content: str = Field(..., min_length=1)
    attachments: Optional[list[str]] = None
