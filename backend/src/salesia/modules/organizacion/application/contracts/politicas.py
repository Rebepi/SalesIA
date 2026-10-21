from decimal import Decimal
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class VolumeTierPolicy(BaseModel):
    min_quantity: Decimal = Field(gt=0, le=1000000)
    discount_percentage: Decimal = Field(ge=0, le=1)


class PricingPolicy(BaseModel):
    default_volume_discounts_enabled: bool = True
    volume_tiers: list[VolumeTierPolicy] = Field(default_factory=list, max_length=100)
    minimum_margin_percentage: Decimal = Field(default=0, ge=0, lt=100)
    maximum_manual_discount_percentage: Decimal = Field(default=100, ge=0, le=100)

    @model_validator(mode="after")
    def unique_tiers(self):
        if len({tier.min_quantity for tier in self.volume_tiers}) != len(self.volume_tiers):
            raise ValueError("No repitas cantidades mínimas en las escalas de descuento.")
        return self


class CommissionTierPolicy(BaseModel):
    minimum_attainment: Decimal = Field(ge=0)
    rate: Decimal = Field(ge=0, le=1)


class CommissionPolicy(BaseModel):
    version: int = Field(default=1, ge=1)
    tiers: list[CommissionTierPolicy] = Field(min_length=1, max_length=100)
    base: Literal["sales", "margin"] = "sales"
    include_tax: bool = True
    earned_on: Literal["sale", "collection", "delivery", "full_payment"] = "sale"
    product_ids: list[UUID] = Field(default_factory=list, max_length=500)
    category_ids: list[UUID] = Field(default_factory=list, max_length=500)
    valid_from: date = date(2000, 1, 1)
    valid_until: date | None = None

    @model_validator(mode="after")
    def validate_tiers(self):
        minimums = [tier.minimum_attainment for tier in self.tiers]
        if len(set(minimums)) != len(minimums) or Decimal("0") not in minimums:
            raise ValueError("Las escalas requieren un tramo desde cero y mínimos únicos.")
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("La vigencia final no puede preceder a la inicial.")
        if self.base == "margin" and self.include_tax:
            raise ValueError("El margen debe calcularse sin impuestos.")
        if len(set(self.product_ids)) != len(self.product_ids) or len(set(self.category_ids)) != len(self.category_ids):
            raise ValueError("No repita productos ni categorías en el alcance de comisiones.")
        return self


class ReplenishmentPolicy(BaseModel):
    default_lead_time_days: int = Field(default=7, ge=0, le=3650)
    history_days: int = Field(default=30, ge=1, le=1095)


class PurchaseMatchingPolicy(BaseModel):
    unit_price_tolerance_percentage: Decimal = Field(default=0, ge=0, le=25)
    rounding_tolerance: Decimal = Field(default=Decimal("0.01"), ge=0, le=1, decimal_places=6)


class SupplierPerformancePolicy(BaseModel):
    history_days: int = Field(default=365, ge=1, le=3650)
    minimum_samples: int = Field(default=3, ge=1, le=1000)
    on_time_weight: Decimal = Field(default=35, ge=0, le=100)
    fill_weight: Decimal = Field(default=25, ge=0, le=100)
    acceptance_weight: Decimal = Field(default=25, ge=0, le=100)
    invoice_weight: Decimal = Field(default=15, ge=0, le=100)

    @model_validator(mode="after")
    def valid_weights(self):
        if self.on_time_weight + self.fill_weight + self.acceptance_weight + self.invoice_weight <= 0:
            raise ValueError("Asigna un peso positivo a algún indicador.")
        return self
