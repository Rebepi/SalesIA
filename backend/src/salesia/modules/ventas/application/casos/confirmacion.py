from typing import Optional
from uuid import UUID, uuid4

from salesia.modules.ventas.application.casos.contratos import ConfirmSaleCommand, SaleResultDTO
from salesia.modules.ventas.domain.entities import SaleStatus
from salesia.modules.ventas.domain.ports import IInventoryStockPort, IOutboxPort, ISaleRepository, ISalesUnitOfWork
from salesia.shared.domain.exceptions import InsufficientStockException, InvariantViolationException
from salesia.shared.infrastructure.outbox import OutboxRecord


class ConfirmSaleUseCase:
    def __init__(
        self,
        sale_repository: Optional[ISaleRepository] = None,
        inventory_port: Optional[IInventoryStockPort] = None,
        outbox_port: Optional[IOutboxPort] = None,
        uow: Optional[ISalesUnitOfWork] = None,
    ):
        self.sale_repository = sale_repository or (uow.sales if uow else None)
        self.inventory_port = inventory_port or (uow.inventory if uow else None)
        self.outbox_port = outbox_port or (uow.outbox if uow else None)
        self.uow = uow

    def execute(self, sale_id_or_cmd: UUID | ConfirmSaleCommand) -> SaleResultDTO:
        if isinstance(sale_id_or_cmd, ConfirmSaleCommand):
            sale_id = sale_id_or_cmd.sale_id
            cmd = sale_id_or_cmd
        else:
            sale_id = sale_id_or_cmd
            cmd = None

        repo = self.sale_repository or (self.uow.sales if self.uow else None)
        inv = self.inventory_port or (self.uow.inventory if self.uow else None)
        out = self.outbox_port or (self.uow.outbox if self.uow else None)

        if repo is None or inv is None:
            raise InvariantViolationException("Puertos de persistencia requeridos no disponibles")

        sale = repo.get_by_id(sale_id)
        if not sale:
            raise InvariantViolationException(f"Venta no encontrada con ID {sale_id}")

        if sale.status == SaleStatus.CONFIRMED:
            total = sale.calculate_total()
            return SaleResultDTO(
                sale_id=str(sale.sale_id),
                company_id=str(sale.company_id),
                branch_id=str(sale.branch_id),
                customer_id=str(sale.customer_id),
                status=sale.status.value,
                currency=sale.currency,
                total_amount=str(total.amount),
                items_count=len(sale.lines),
            )

        if cmd and cmd.is_credit_sale and self.uow and hasattr(self.uow, "credit"):
            total_amount = sale.calculate_total().amount
            has_credit = self.uow.credit.verify_and_consume_credit(
                company_id=sale.company_id, customer_id=sale.customer_id, amount=total_amount
            )
            if not has_credit:
                raise InvariantViolationException("Límite de crédito insuficiente")

        for line in sale.lines:
            has_stock = inv.check_and_deduct_stock(
                company_id=sale.company_id, branch_id=sale.branch_id, sku=line.sku, quantity=line.quantity
            )
            if not has_stock:
                raise InsufficientStockException(sku=line.sku, requested=line.quantity, available=0)

        sale.confirm()
        repo.save(sale)

        if out is not None:
            event = OutboxRecord(
                event_id=uuid4(),
                event_type="sale.confirmed",
                company_id=sale.company_id,
                payload={
                    "sale_id": str(sale.sale_id),
                    "company_id": str(sale.company_id),
                    "branch_id": str(sale.branch_id),
                    "customer_id": str(sale.customer_id),
                    "total_amount": str(sale.calculate_total().amount),
                    "currency": sale.currency,
                    "items_count": len(sale.lines),
                },
            )
            out.record_event(event)

        if self.uow and hasattr(self.uow, "audit") and cmd and cmd.actor_email:
            self.uow.audit.record_action(
                company_id=sale.company_id,
                actor_id=cmd.actor_id,
                actor_email=cmd.actor_email,
                action="CONFIRM_SALE",
                entity_type="Sale",
                entity_id=sale.sale_id,
                payload_diff='{"status": "confirmed"}',
            )

        if self.uow is not None:
            self.uow.commit()

        total = sale.calculate_total()
        return SaleResultDTO(
            sale_id=str(sale.sale_id),
            company_id=str(sale.company_id),
            branch_id=str(sale.branch_id),
            customer_id=str(sale.customer_id),
            status=sale.status.value,
            currency=sale.currency,
            total_amount=str(total.amount),
            items_count=len(sale.lines),
        )
