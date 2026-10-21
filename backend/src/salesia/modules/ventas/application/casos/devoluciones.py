from uuid import uuid4

from salesia.modules.ventas.application.casos.contratos import AnnulSaleCommand, SaleResultDTO
from salesia.modules.ventas.domain.entities import SaleStatus
from salesia.modules.ventas.domain.ports import ISalesUnitOfWork
from salesia.shared.domain.exceptions import InvariantViolationException
from salesia.shared.infrastructure.outbox import OutboxRecord


class AcceptReturnUseCase:
    def __init__(self, uow: ISalesUnitOfWork):
        self.uow = uow

    def execute(self, command: AnnulSaleCommand) -> SaleResultDTO:
        sale = self.uow.sales.get_by_id(command.sale_id, command.company_id)
        if sale is None:
            raise InvariantViolationException(f"Venta no encontrada con ID {command.sale_id}")

        if sale.status == SaleStatus.CANCELLED:
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

        for line in sale.lines:
            self.uow.inventory.restore_stock(
                company_id=sale.company_id, branch_id=sale.branch_id, sku=line.sku, quantity=line.quantity
            )

        if hasattr(self.uow, "credit"):
            total_amount = sale.calculate_total().amount
            self.uow.credit.restore_credit(
                company_id=sale.company_id, customer_id=sale.customer_id, amount=total_amount
            )

        sale.annul()
        self.uow.sales.save(sale)

        event = OutboxRecord(
            event_id=uuid4(),
            event_type="sale.annulled",
            company_id=command.company_id,
            payload={"sale_id": str(command.sale_id), "reason": command.reason},
        )
        self.uow.outbox.record_event(event)

        if hasattr(self.uow, "audit") and command.actor_email:
            self.uow.audit.record_action(
                company_id=command.company_id,
                actor_id=command.actor_id,
                actor_email=command.actor_email,
                action="ANNUL_SALE",
                entity_type="Sale",
                entity_id=command.sale_id,
                payload_diff=f'{{"reason": "{command.reason}"}}',
            )

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
