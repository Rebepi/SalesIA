from typing import Optional

from salesia.modules.ventas.application.casos.contratos import CreateSaleDraftCommand, SaleResultDTO
from salesia.modules.ventas.domain.entities import Sale
from salesia.modules.ventas.domain.ports import ISaleRepository, ISalesUnitOfWork
from salesia.shared.domain.exceptions import InvariantViolationException
from salesia.shared.domain.money import Money


class CreateSaleDraftUseCase:
    def __init__(self, sale_repository: Optional[ISaleRepository] = None, uow: Optional[ISalesUnitOfWork] = None):
        self.sale_repository = sale_repository or (uow.sales if uow else None)
        self.uow = uow

    def execute(self, command: CreateSaleDraftCommand) -> SaleResultDTO:
        sale = Sale.create_draft(
            company_id=command.company_id,
            branch_id=command.branch_id,
            customer_id=command.customer_id,
            currency=command.currency,
        )

        for line_input in command.lines:
            sale.add_line(
                product_id=line_input.product_id,
                sku=line_input.sku,
                product_name=line_input.product_name,
                quantity=line_input.quantity,
                unit_price=Money.create(line_input.unit_price, command.currency),
                tax_rate=line_input.tax_rate,
                discount=Money.create(line_input.discount, command.currency),
                cost_snapshot=Money.create(line_input.cost_snapshot, command.currency),
            )

        repo = self.sale_repository or (self.uow.sales if self.uow else None)
        if repo is None:
            raise InvariantViolationException("Repositorio de ventas no provisto")
        repo.save(sale)

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
