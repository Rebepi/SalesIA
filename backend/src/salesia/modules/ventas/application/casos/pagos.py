from decimal import Decimal
from uuid import uuid4

from salesia.modules.ventas.application.casos.contratos import ApplyPaymentCommand, PaymentResultDTO
from salesia.modules.ventas.domain.entities import SaleStatus
from salesia.modules.ventas.domain.ports import ISalesUnitOfWork
from salesia.shared.domain.exceptions import InvariantViolationException
from salesia.shared.infrastructure.outbox import OutboxRecord


class ApplyPaymentUseCase:
    def __init__(self, uow: ISalesUnitOfWork):
        self.uow = uow

    def execute(self, command: ApplyPaymentCommand) -> PaymentResultDTO:
        sale = self.uow.sales.get_by_id(command.sale_id, command.company_id)
        if sale is None:
            raise InvariantViolationException(f"Venta no encontrada con ID {command.sale_id}")

        if sale.status != SaleStatus.CONFIRMED:
            raise InvariantViolationException("Solo se pueden registrar cobros sobre ventas confirmadas")

        if command.currency.upper() != sale.currency:
            raise InvariantViolationException(
                f"La divisa del pago ({command.currency}) no coincide con la venta ({sale.currency})"
            )

        if command.amount <= Decimal("0.00"):
            raise InvariantViolationException("El importe del cobro debe ser mayor a cero")

        total = sale.calculate_total().amount
        if command.amount > total:
            raise InvariantViolationException("El importe pagado excede el saldo pendiente")

        sale.status = SaleStatus.PAID
        self.uow.sales.save(sale)

        event = OutboxRecord(
            event_id=uuid4(),
            event_type="payment.applied",
            company_id=command.company_id,
            payload={
                "sale_id": str(command.sale_id),
                "amount": str(command.amount),
                "currency": command.currency,
                "payment_method": command.payment_method,
            },
        )
        self.uow.outbox.record_event(event)
        self.uow.commit()

        return PaymentResultDTO(
            sale_id=str(command.sale_id),
            amount=str(command.amount),
            currency=command.currency,
            status=sale.status.value,
            paid_amount=str(command.amount),
        )
