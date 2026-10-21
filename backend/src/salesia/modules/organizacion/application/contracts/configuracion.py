from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field
from salesia.modules.organizacion.application.contracts.politicas import CommissionPolicy, PricingPolicy, ReplenishmentPolicy, PurchaseMatchingPolicy, SupplierPerformancePolicy


class SettingsUpdateModel(BaseModel):
    version: int = Field(ge=0)
    rounding_mode: Optional[str] = "ROUND_HALF_EVEN"
    default_tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=1)
    credit_limit_strict: Optional[bool] = True
    base_currency: Optional[str] = None
    timezone: Optional[str] = None
    tax_included_in_price: Optional[bool] = False
    branding: Optional[dict[str, Any]] = None
    closed_periods: Optional[list[str]] = None
    closed_until: Optional[str] = None
    quotas: Optional[dict[str, Any]] = None
    test_mode: Optional[bool] = False
    pricing_policy: Optional[PricingPolicy] = None
    commission_policy: Optional[CommissionPolicy] = None
    replenishment_policy: Optional[ReplenishmentPolicy] = None
    purchase_matching_policy: Optional[PurchaseMatchingPolicy] = None

    supplier_performance_policy: Optional[SupplierPerformancePolicy] = None
