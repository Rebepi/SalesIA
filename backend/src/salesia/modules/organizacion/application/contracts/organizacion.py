from decimal import Decimal
from datetime import date
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class OnboardingSetupModel(BaseModel):
    tax_id: str = Field(min_length=8, max_length=20)
    legal_name: str = Field(min_length=1, max_length=255)
    trade_name: Optional[str] = Field(default=None, max_length=255)
    base_currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    branch_code: str = Field(default="PRINCIPAL", min_length=1, max_length=32)
    branch_name: str = Field(default="Sede Principal", min_length=1, max_length=255)
    timezone: str = "America/Lima"
    warehouse_code: str = Field(default="ALM-01", min_length=1, max_length=32)
    warehouse_name: str = Field(default="Almacén Principal", min_length=1, max_length=255)
    series: str = Field(default="F001", min_length=1, max_length=16)

    @field_validator("timezone")
    @classmethod
    def valid_tz(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Zona horaria desconocida")
        return value


class ContextSwitchModel(BaseModel):
    branch_id: UUID


class PreferenceResetModel(BaseModel):
    key: str


class PeriodCloseModel(BaseModel):
    closed_until: str = Field(pattern="^\\d{4}-\\d{2}-\\d{2}$")
    reason: str = Field(default="Cierre contable regular", min_length=5, max_length=2000)

    @field_validator("closed_until")
    @classmethod
    def valid_close_date(cls, value: str) -> str:
        return date.fromisoformat(value).isoformat()


class PeriodReopenModel(BaseModel):
    reopen_date: str = Field(pattern="^\\d{4}-\\d{2}-\\d{2}$")
    reopen_end: date | None = None
    hours: int = Field(default=24, ge=1, le=168)
    reason: str = Field(min_length=5)

    @field_validator("reopen_date")
    @classmethod
    def valid_reopen_date(cls, value: str) -> str:
        return date.fromisoformat(value).isoformat()


class TaxRuleModel(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    rate: Decimal = Field(ge=0, le=1)
    name: str = Field(min_length=1, max_length=128)
    is_active: bool = True


class BrandingPreviewModel(BaseModel):
    logo_url: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    footer_text: Optional[str] = None


class QuotaCheckModel(BaseModel):
    resource: str
    requested_quantity: int = Field(gt=0)
