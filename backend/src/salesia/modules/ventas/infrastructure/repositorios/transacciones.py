from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.ports import ISalesUnitOfWork
from salesia.modules.ventas.infrastructure.repositorios.auditoria import SqlAuditPort
from salesia.modules.ventas.infrastructure.repositorios.credito import SqlCustomerCreditPort
from salesia.modules.ventas.infrastructure.repositorios.eventos import SqlOutboxAdapter
from salesia.modules.ventas.infrastructure.repositorios.inventario import SqlInventoryPort
from salesia.modules.ventas.infrastructure.repositorios.ventas import SqlSaleRepository


class SqlSalesUnitOfWork(ISalesUnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self.sales = SqlSaleRepository(session)
        self.inventory = SqlInventoryPort(session)
        self.outbox = SqlOutboxAdapter(session)
        self.audit = SqlAuditPort(session)
        self.credit = SqlCustomerCreditPort(session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __enter__(self) -> "SqlSalesUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
