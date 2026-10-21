from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4

from salesia.shared.domain.exceptions import InvariantViolationException
from salesia.shared.domain.money import Money


class SaleStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass(frozen=True)
class SaleLine:
    line_id: UUID
    product_id: UUID
    sku: str
    product_name: str
    quantity: Union[int, Decimal]
    unit_price: Money
    tax_rate: Decimal
    discount: Money
    cost_snapshot: Money

    def calculate_subtotal(self) -> Money:
        base = self.unit_price * Decimal(str(self.quantity))
        sub = base - self.discount
        return sub.round_to(2)

    def calculate_tax(self) -> Money:
        sub = self.calculate_subtotal()
        tax_amt = sub * self.tax_rate
        return tax_amt.round_to(2)

    def calculate_total(self) -> Money:
        return self.calculate_subtotal() + self.calculate_tax()


@dataclass
class Sale:
    sale_id: UUID
    company_id: UUID
    branch_id: UUID
    customer_id: UUID
    currency: str = "USD"
    status: SaleStatus = SaleStatus.DRAFT
    lines: list[SaleLine] = field(default_factory=list)

    @classmethod
    def create_draft(
        cls, company_id: UUID, branch_id: UUID, customer_id: UUID, currency: str = "USD", sale_id: Optional[UUID] = None
    ) -> "Sale":
        return cls(
            sale_id=sale_id or uuid4(),
            company_id=company_id,
            branch_id=branch_id,
            customer_id=customer_id,
            currency=currency,
            status=SaleStatus.DRAFT,
        )

    def add_line(
        self,
        product_id: UUID,
        sku: str,
        product_name: str,
        quantity: Union[int, Decimal],
        unit_price: Money,
        tax_rate: Decimal = Decimal("0.18"),
        discount: Optional[Money] = None,
        cost_snapshot: Optional[Money] = None,
        line_id: Optional[UUID] = None,
    ) -> SaleLine:
        if self.status != SaleStatus.DRAFT:
            raise InvariantViolationException("Solo se pueden agregar productos a una venta en estado borrador")

        if Decimal(str(quantity)) <= Decimal("0"):
            raise InvariantViolationException(f"La cantidad debe ser mayor a cero, recibido {quantity}")

        if unit_price.currency != self.currency:
            raise InvariantViolationException(
                f"La moneda del precio ({unit_price.currency}) no coincide con la venta ({self.currency})"
            )

        disc = discount or Money.zero(self.currency)
        cost = cost_snapshot or Money.zero(self.currency)

        line = SaleLine(
            line_id=line_id or uuid4(),
            product_id=product_id,
            sku=sku,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=tax_rate,
            discount=disc,
            cost_snapshot=cost,
        )
        self.lines.append(line)
        return line

    def calculate_total(self) -> Money:
        if not self.lines:
            return Money.zero(self.currency)
        total = Money.zero(self.currency)
        for line in self.lines:
            total = total + line.calculate_total()
        return total.round_to(2)

    def confirm(self) -> None:
        if self.status != SaleStatus.DRAFT:
            raise InvariantViolationException(f"No se puede confirmar una venta en estado {self.status.value}")
        if not self.lines:
            raise InvariantViolationException("No se puede confirmar una venta sin líneas de producto")
        self.status = SaleStatus.CONFIRMED

    def cancel(self) -> None:
        if self.status == SaleStatus.CONFIRMED:
            raise InvariantViolationException(
                "Una venta confirmada debe anularse mediante proceso de devolución formal"
            )
        self.status = SaleStatus.CANCELLED

    def annul(self) -> None:
        if self.status not in (SaleStatus.DRAFT, SaleStatus.CONFIRMED):
            raise InvariantViolationException(f"No se puede anular una venta en estado {self.status.value}")
        self.status = SaleStatus.CANCELLED
