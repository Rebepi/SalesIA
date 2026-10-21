from salesia.modules.ventas.application.casos.contratos import ReservationResultDTO, ReserveStockCommand
from salesia.modules.ventas.domain.ports import ISalesUnitOfWork
from salesia.shared.domain.exceptions import InsufficientStockException


class ReserveStockUseCase:
    def __init__(self, uow: ISalesUnitOfWork):
        self.uow = uow

    def execute(self, command: ReserveStockCommand) -> ReservationResultDTO:
        for sku, quantity in command.items:
            success = self.uow.inventory.reserve_stock(
                company_id=command.company_id, branch_id=command.branch_id, sku=sku, quantity=quantity
            )
            if not success:
                raise InsufficientStockException(sku=sku, requested=quantity, available=0)
        self.uow.commit()
        return ReservationResultDTO(success=True, reserved_count=len(command.items))
