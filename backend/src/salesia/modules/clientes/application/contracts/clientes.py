from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreateModel(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=64)
    doc_type: str = Field(..., min_length=2, max_length=16)
    doc_number: str = Field(..., min_length=1, max_length=32)
    legal_name: str = Field(..., min_length=2, max_length=255)
    address: Optional[str] = Field(default=None, min_length=3, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    credit_limit: Decimal = Field(default=Decimal("0.000000"), ge=0)
    status: Optional[str] = "active"
    assigned_sales_rep_id: Optional[UUID] = None
    sales_team: Optional[str] = None
    payment_terms_days: Optional[int] = Field(default=30, ge=0, le=365)
    preferred_currency: Optional[str] = "USD"


class CustomerUpdateModel(BaseModel):
    version: Optional[int] = None
    legal_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = None
    assigned_sales_rep_id: Optional[UUID] = None
    sales_team: Optional[str] = None
    backup_sales_rep_id: Optional[UUID] = None
    price_list_id: Optional[str] = None
    payment_terms_days: Optional[int] = None
    preferred_currency: Optional[str] = None
    is_credit_blocked: Optional[bool] = None
    credit_block_until: Optional[datetime] = None
    credit_block_reason: Optional[str] = None


class ArchiveRestoreModel(BaseModel):
    reason: Optional[str] = None
    version: Optional[int] = None


class CustomerStatusUpdateModel(BaseModel):
    status: str = Field(..., pattern="^(prospect|active|blocked|archived)$")
    reason: Optional[str] = None
    block_until: Optional[datetime] = None
