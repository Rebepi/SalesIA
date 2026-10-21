from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class IntegrationCreateRequest(BaseModel):
    __module__ = "salesia.modules.finance.presentation.router"
    provider: str = Field(pattern="^(stripe|mercadopago|culqi|niubiz|custom)$")


class PaymentIntentCreateRequest(BaseModel):
    sale_id: UUID

    provider: str = Field(..., min_length=2, max_length=32)

    amount: Decimal = Field(..., gt=0)

    currency: str = Field(default="USD", min_length=3, max_length=3)


class PaymentIntentConfirmRequest(BaseModel):
    gateway_token: str = Field(..., min_length=1, max_length=255)


class PaymentIntentSyncRequest(BaseModel):
    gateway_response: str = Field(..., min_length=1, max_length=255)
