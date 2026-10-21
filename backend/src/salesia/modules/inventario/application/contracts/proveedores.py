from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SupplierCreateRequest(BaseModel):
    tax_id: str = Field(min_length=3, max_length=32)

    legal_name: str = Field(min_length=2, max_length=255)

    contact_name: Optional[str] = Field(default=None, max_length=255)

    email: Optional[EmailStr] = None

    phone: Optional[str] = Field(default=None, max_length=64)

    payment_terms_days: int = Field(default=30, ge=0, le=365)

    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")

    bank_name: Optional[str] = Field(default=None, max_length=128)

    bank_account: Optional[str] = Field(default=None, max_length=64)

    notes: Optional[str] = Field(default=None, max_length=1000)


class SupplierUpdateRequest(BaseModel):
    version: Optional[int] = Field(default=None, ge=1)

    change_reason: Optional[str] = Field(default=None, min_length=5, max_length=2000)

    legal_name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    contact_name: Optional[str] = Field(default=None, max_length=255)

    email: Optional[EmailStr] = None

    phone: Optional[str] = Field(default=None, max_length=64)

    payment_terms_days: Optional[int] = Field(default=None, ge=0, le=365)

    currency: Optional[str] = Field(default=None, pattern="^[A-Z]{3}$")

    bank_name: Optional[str] = Field(default=None, max_length=128)

    bank_account: Optional[str] = Field(default=None, max_length=64)

    notes: Optional[str] = Field(default=None, max_length=1000)

    is_active: Optional[bool] = None
