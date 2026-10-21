from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.ports import ICustomerCreditPort
from salesia.shared.infrastructure.models import CustomerModel


class SqlCustomerCreditPort(ICustomerCreditPort):
    def __init__(self, session: Session):
        self.session = session

    def verify_and_consume_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> bool:
        customer = self.session.scalar(
            select(CustomerModel)
            .where(
                CustomerModel.id == customer_id,
                CustomerModel.company_id == company_id,
                CustomerModel.is_active.is_(True),
            )
            .with_for_update()
        )
        if customer is None:
            return False
        if customer.current_balance + amount > customer.credit_limit:
            return False
        customer.current_balance = customer.current_balance + amount
        self.session.flush()
        return True

    def restore_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> None:
        customer = self.session.scalar(
            select(CustomerModel)
            .where(CustomerModel.id == customer_id, CustomerModel.company_id == company_id)
            .with_for_update()
        )
        if customer is not None:
            customer.current_balance = max(Decimal("0.00"), customer.current_balance - amount)
            self.session.flush()
