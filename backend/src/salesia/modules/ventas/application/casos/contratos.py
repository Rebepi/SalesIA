from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID


@dataclass(frozen=True)
class DraftLineInput:
    product_id: UUID
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0.18")
    discount: Decimal = Decimal("0.00")
    cost_snapshot: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class CreateSaleDraftCommand:
    company_id: UUID
    branch_id: UUID
    customer_id: UUID
    currency: str
    lines: Sequence[DraftLineInput]


@dataclass(frozen=True)
class ConfirmSaleCommand:
    sale_id: UUID
    company_id: UUID
    is_credit_sale: bool = False
    actor_id: Optional[UUID] = None
    actor_email: str = ""


@dataclass(frozen=True)
class ApplyPaymentCommand:
    sale_id: UUID
    company_id: UUID
    amount: Decimal
    currency: str
    payment_method: str
    reference_code: Optional[str] = None


@dataclass(frozen=True)
class ReserveStockCommand:
    company_id: UUID
    branch_id: UUID
    items: Sequence[tuple[str, int]]


@dataclass(frozen=True)
class AnnulSaleCommand:
    sale_id: UUID
    company_id: UUID
    reason: str
    actor_id: Optional[UUID] = None
    actor_email: str = ""


@dataclass(frozen=True)
class SaleResultDTO:
    sale_id: str
    company_id: str
    branch_id: str
    customer_id: str
    status: str
    currency: str
    total_amount: str
    items_count: int


@dataclass(frozen=True)
class PaymentResultDTO:
    sale_id: str
    amount: str
    currency: str
    status: str
    paid_amount: str


@dataclass(frozen=True)
class ReservationResultDTO:
    success: bool
    reserved_count: int
