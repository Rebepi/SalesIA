from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.ventas.domain.ports import IInventoryStockPort
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel, ProductModel


class SqlInventoryPort(IInventoryStockPort):
    def __init__(self, session: Session):
        self.session = session

    def check_and_deduct_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool:
        from salesia.modules.organizacion.application.periodos import business_date, require_open_period
        require_open_period(self.session, company_id, business_date(self.session, company_id), ["inventory"])
        product = self.session.scalar(
            select(ProductModel).where(
                ProductModel.company_id == company_id, ProductModel.sku == sku, ProductModel.is_active.is_(True)
            )
        )
        if product is None:
            return False

        stock = self.session.scalar(
            select(InventoryStockModel)
            .where(InventoryStockModel.company_id == company_id, InventoryStockModel.product_id == product.id)
            .with_for_update()
        )
        if stock is None:
            return False

        available = stock.physical_quantity - stock.reserved_quantity
        if available < quantity:
            return False

        stock.physical_quantity = stock.physical_quantity - Decimal(quantity)
        self.session.add(
            KardexMovementModel(
                id=uuid4(),
                company_id=company_id,
                warehouse_id=stock.warehouse_id,
                product_id=product.id,
                movement_type="VENTA",
                reference_doc_type="SALE",
                quantity_delta=-Decimal(quantity),
                resulting_physical_qty=stock.physical_quantity,
                unit_cost=product.unit_cost,
                moving_average_cost=product.unit_cost,
                occurred_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()
        return True

    def restore_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> None:
        product = self.session.scalar(
            select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.sku == sku)
        )
        if product is None:
            return

        stock = self.session.scalar(
            select(InventoryStockModel)
            .where(InventoryStockModel.company_id == company_id, InventoryStockModel.product_id == product.id)
            .with_for_update()
        )
        if stock is None:
            return

        stock.physical_quantity = stock.physical_quantity + Decimal(quantity)
        self.session.add(
            KardexMovementModel(
                id=uuid4(),
                company_id=company_id,
                warehouse_id=stock.warehouse_id,
                product_id=product.id,
                movement_type="ANULACION_VENTA",
                reference_doc_type="SALE_ANNUL",
                quantity_delta=Decimal(quantity),
                resulting_physical_qty=stock.physical_quantity,
                unit_cost=product.unit_cost,
                moving_average_cost=product.unit_cost,
                occurred_at=datetime.now(timezone.utc),
            )
        )
        self.session.flush()

    def reserve_stock(self, company_id: UUID, branch_id: UUID, sku: str, quantity: int) -> bool:
        product = self.session.scalar(
            select(ProductModel).where(
                ProductModel.company_id == company_id, ProductModel.sku == sku, ProductModel.is_active.is_(True)
            )
        )
        if product is None:
            return False

        stock = self.session.scalar(
            select(InventoryStockModel)
            .where(InventoryStockModel.company_id == company_id, InventoryStockModel.product_id == product.id)
            .with_for_update()
        )
        if stock is None:
            return False

        available = stock.physical_quantity - stock.reserved_quantity
        if available < quantity:
            return False

        stock.reserved_quantity = stock.reserved_quantity + Decimal(quantity)
        self.session.flush()
        return True
