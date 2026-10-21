from typing import Optional

from pydantic import BaseModel, Field


class PaymentMethodCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)

    name: str = Field(..., min_length=2, max_length=128)

    is_active: bool = True

    requires_reference: bool = False

    requires_cash_session: bool = False

    allowed_currencies: str = "USD,PEN,EUR"


class PaymentMethodUpdateRequest(BaseModel):
    name: Optional[str] = None

    is_active: Optional[bool] = None

    requires_reference: Optional[bool] = None

    requires_cash_session: Optional[bool] = None

    allowed_currencies: Optional[str] = None
