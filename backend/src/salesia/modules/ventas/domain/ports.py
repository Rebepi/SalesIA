from decimal import Decimal
from typing import Optional, Protocol
from uuid import UUID

from salesia.modules.ventas.domain.entities import Sale
from salesia.shared.infrastructure.outbox import OutboxRecord


class ISaleRepository(Protocol):
    def save(self, sale: Sale) -> None: ...

    def get_by_id(self, sale_id: UUID, company_id: Optional[UUID] = None) -> Optional[Sale]: ...


class IInventoryStockPort(Protocol):
    def check_and_deduct_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool: ...

    def restore_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> None: ...

    def reserve_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool: ...


class IOutboxPort(Protocol):
    def record_event(self, event: OutboxRecord) -> None: ...


class IAuditPort(Protocol):
    def record_action(
        self,
        company_id: UUID,
        actor_id: Optional[UUID],
        actor_email: str,
        action: str,
        entity_type: str,
        entity_id: UUID,
        payload_diff: str,
    ) -> None: ...


class ICustomerCreditPort(Protocol):
    def verify_and_consume_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> bool: ...

    def restore_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> None: ...


class ISalesUnitOfWork(Protocol):
    sales: ISaleRepository
    inventory: IInventoryStockPort
    outbox: IOutboxPort
    audit: IAuditPort
    credit: ICustomerCreditPort

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __enter__(self) -> "ISalesUnitOfWork": ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
