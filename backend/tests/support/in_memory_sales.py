from decimal import Decimal
from typing import Optional
from uuid import UUID
from salesia.modules.ventas.domain.entities import Sale
from salesia.modules.ventas.domain.ports import (
    ISaleRepository,
    IInventoryStockPort,
    IOutboxPort,
    IAuditPort,
    ICustomerCreditPort,
    ISalesUnitOfWork
)
from tests.support.in_memory_outbox import InMemoryOutboxRepository


class InMemorySaleRepository(ISaleRepository):
    def __init__(self):
        self._sales: dict[UUID, Sale] = {}

    def save(self, sale: Sale) -> None:
        self._sales[sale.sale_id] = sale

    def get_by_id(self, sale_id: UUID, company_id: Optional[UUID] = None) -> Optional[Sale]:
        sale = self._sales.get(sale_id)
        if sale and company_id and sale.company_id != company_id:
            return None
        return sale


class InMemoryInventoryService(IInventoryStockPort):
    def __init__(self, initial_stock: Optional[dict[str, int]] = None):
        self._stock: dict[str, int] = initial_stock or {}
        self._reserved: dict[str, int] = {}

    def set_stock(self, sku: str, quantity: int) -> None:
        self._stock[sku] = quantity

    def check_and_deduct_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool:
        current = self._stock.get(sku, 0)
        if current >= quantity:
            self._stock[sku] = current - quantity
            return True
        return False

    def restore_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> None:
        current = self._stock.get(sku, 0)
        self._stock[sku] = current + quantity

    def reserve_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool:
        current = self._stock.get(sku, 0)
        reserved = self._reserved.get(sku, 0)
        if current - reserved >= quantity:
            self._reserved[sku] = reserved + quantity
            return True
        return False


class InMemoryAuditPort(IAuditPort):
    def __init__(self):
        self.actions: list[dict] = []

    def record_action(
        self,
        company_id: UUID,
        actor_id: Optional[UUID],
        actor_email: str,
        action: str,
        entity_type: str,
        entity_id: UUID,
        payload_diff: str
    ) -> None:
        self.actions.append({
            "company_id": company_id,
            "actor_id": actor_id,
            "actor_email": actor_email,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload_diff": payload_diff
        })


class InMemoryCustomerCreditPort(ICustomerCreditPort):
    def __init__(self, balances: Optional[dict[UUID, Decimal]] = None, limits: Optional[dict[UUID, Decimal]] = None):
        self.balances = balances or {}
        self.limits = limits or {}

    def verify_and_consume_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> bool:
        limit = self.limits.get(customer_id, Decimal("10000.00"))
        current = self.balances.get(customer_id, Decimal("0.00"))
        if current + amount <= limit:
            self.balances[customer_id] = current + amount
            return True
        return False

    def restore_credit(self, company_id: UUID, customer_id: UUID, amount: Decimal) -> None:
        current = self.balances.get(customer_id, Decimal("0.00"))
        self.balances[customer_id] = max(Decimal("0.00"), current - amount)


class InMemoryOutboxAdapter(IOutboxPort):
    def __init__(self, repo: Optional[InMemoryOutboxRepository] = None):
        self.repo = repo or InMemoryOutboxRepository()

    def record_event(self, event) -> None:
        self.repo.save(event)


class InMemorySalesUnitOfWork(ISalesUnitOfWork):
    def __init__(
        self,
        sales_repo: Optional[InMemorySaleRepository] = None,
        inventory_port: Optional[InMemoryInventoryService] = None,
        outbox_port: Optional[IOutboxPort] = None
    ):
        self.sales = sales_repo or InMemorySaleRepository()
        self.inventory = inventory_port or InMemoryInventoryService()
        self.outbox = outbox_port or InMemoryOutboxAdapter()
        self.audit = InMemoryAuditPort()
        self.credit = InMemoryCustomerCreditPort()
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def __enter__(self) -> "InMemorySalesUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
