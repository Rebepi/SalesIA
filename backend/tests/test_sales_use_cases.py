from decimal import Decimal
from uuid import uuid4
import pytest
from salesia.shared.domain.money import Money
from salesia.shared.domain.exceptions import (
    InsufficientStockException,
    InvariantViolationException
)
from tests.support.in_memory_outbox import (
    InMemoryOutboxRepository,
    OutboxRecord
)
from salesia.modules.ventas.domain.entities import Sale, SaleStatus
from tests.support.in_memory_sales import (
    InMemorySaleRepository,
    InMemoryInventoryService,
    InMemorySalesUnitOfWork
)
from salesia.modules.ventas.application.use_cases import (
    CreateSaleDraftUseCase,
    ConfirmSaleUseCase,
    ApplyPaymentUseCase,
    ReserveStockUseCase,
    AcceptReturnUseCase,
    CreateSaleDraftCommand,
    ConfirmSaleCommand,
    ApplyPaymentCommand,
    ReserveStockCommand,
    AnnulSaleCommand,
    DraftLineInput
)


def test_create_sale_draft_success():
    repo = InMemorySaleRepository()
    use_case = CreateSaleDraftUseCase(repo)

    company_id = uuid4()
    branch_id = uuid4()
    customer_id = uuid4()

    cmd = CreateSaleDraftCommand(
        company_id=company_id,
        branch_id=branch_id,
        customer_id=customer_id,
        currency="USD",
        lines=[
            DraftLineInput(
                product_id=uuid4(),
                sku="SKU-TEST-1",
                product_name="Producto 1",
                quantity=2,
                unit_price=Decimal("100.00"),
                tax_rate=Decimal("0.18"),
                discount=Decimal("0.00"),
                cost_snapshot=Decimal("60.00")
            ),
            DraftLineInput(
                product_id=uuid4(),
                sku="SKU-TEST-2",
                product_name="Producto 2",
                quantity=1,
                unit_price=Decimal("50.00"),
                tax_rate=Decimal("0.18"),
                discount=Decimal("10.00"),
                cost_snapshot=Decimal("25.00")
            )
        ]
    )

    result = use_case.execute(cmd)

    assert result.status == SaleStatus.DRAFT.value
    assert result.items_count == 2
    assert result.total_amount == "283.20"


def test_confirm_sale_with_stock_success():
    sale_repo = InMemorySaleRepository()
    inventory_service = InMemoryInventoryService({"SKU-LAPTOP": 5})
    outbox_repo = InMemoryOutboxRepository()

    class OutboxAdapter:
        def record_event(self, event: OutboxRecord) -> None:
            outbox_repo.save(event)

    sale = Sale.create_draft(
        company_id=uuid4(),
        branch_id=uuid4(),
        customer_id=uuid4(),
        currency="USD"
    )
    sale.add_line(
        product_id=uuid4(),
        sku="SKU-LAPTOP",
        product_name="Laptop Pro",
        quantity=2,
        unit_price=Money.create("1200.00", "USD"),
        tax_rate=Decimal("0.18")
    )
    sale_repo.save(sale)

    confirm_use_case = ConfirmSaleUseCase(
        sale_repository=sale_repo,
        inventory_port=inventory_service,
        outbox_port=OutboxAdapter()
    )

    result = confirm_use_case.execute(sale.sale_id)

    assert result.status == SaleStatus.CONFIRMED.value
    assert inventory_service._stock["SKU-LAPTOP"] == 3

    pending_events = outbox_repo.get_pending()
    assert len(pending_events) == 1
    assert pending_events[0].event_type == "sale.confirmed"
    assert pending_events[0].payload["sale_id"] == str(sale.sale_id)


def test_confirm_sale_insufficient_stock_fails():
    sale_repo = InMemorySaleRepository()
    inventory_service = InMemoryInventoryService({"SKU-MOUSE": 1})
    outbox_repo = InMemoryOutboxRepository()

    class OutboxAdapter:
        def record_event(self, event: OutboxRecord) -> None:
            outbox_repo.save(event)

    sale = Sale.create_draft(
        company_id=uuid4(),
        branch_id=uuid4(),
        customer_id=uuid4(),
        currency="USD"
    )
    sale.add_line(
        product_id=uuid4(),
        sku="SKU-MOUSE",
        product_name="Mouse Inalámbrico",
        quantity=5,
        unit_price=Money.create("25.00", "USD")
    )
    sale_repo.save(sale)

    confirm_use_case = ConfirmSaleUseCase(
        sale_repository=sale_repo,
        inventory_port=inventory_service,
        outbox_port=OutboxAdapter()
    )

    with pytest.raises(InsufficientStockException):
        confirm_use_case.execute(sale.sale_id)

    saved_sale = sale_repo.get_by_id(sale.sale_id)
    assert saved_sale.status == SaleStatus.DRAFT
    assert inventory_service._stock["SKU-MOUSE"] == 1
    assert len(outbox_repo.get_pending()) == 0


def test_add_line_to_confirmed_sale_forbidden():
    sale = Sale.create_draft(
        company_id=uuid4(),
        branch_id=uuid4(),
        customer_id=uuid4(),
        currency="USD"
    )
    sale.add_line(
        product_id=uuid4(),
        sku="SKU-1",
        product_name="Item 1",
        quantity=1,
        unit_price=Money.create("10.00", "USD")
    )
    sale.confirm()

    with pytest.raises(InvariantViolationException):
        sale.add_line(
            product_id=uuid4(),
            sku="SKU-2",
            product_name="Item 2",
            quantity=1,
            unit_price=Money.create("20.00", "USD")
        )


def test_apply_payment_use_case():
    uow = InMemorySalesUnitOfWork()
    sale = Sale.create_draft(company_id=uuid4(), branch_id=uuid4(), customer_id=uuid4(), currency="USD")
    sale.add_line(product_id=uuid4(), sku="SKU-P", product_name="P", quantity=1, unit_price=Money.create("100.00", "USD"), tax_rate=Decimal("0.00"))
    sale.confirm()
    uow.sales.save(sale)

    payment_uc = ApplyPaymentUseCase(uow)
    cmd = ApplyPaymentCommand(
        sale_id=sale.sale_id,
        company_id=sale.company_id,
        amount=Decimal("100.00"),
        currency="USD",
        payment_method="CASH"
    )
    result = payment_uc.execute(cmd)

    assert result.status == SaleStatus.PAID.value
    assert result.paid_amount == "100.00"
    assert uow.committed is True

    bad_currency_cmd = ApplyPaymentCommand(
        sale_id=sale.sale_id,
        company_id=sale.company_id,
        amount=Decimal("100.00"),
        currency="EUR",
        payment_method="CASH"
    )
    with pytest.raises(InvariantViolationException):
        payment_uc.execute(bad_currency_cmd)


def test_reserve_stock_use_case():
    uow = InMemorySalesUnitOfWork(inventory_port=InMemoryInventoryService({"SKU-RES": 10}))
    company_id = uuid4()
    branch_id = uuid4()
    reserve_uc = ReserveStockUseCase(uow)

    cmd = ReserveStockCommand(
        company_id=company_id,
        branch_id=branch_id,
        items=[("SKU-RES", 4)]
    )
    res = reserve_uc.execute(cmd)
    assert res.success is True
    assert res.reserved_count == 1
    assert uow.committed is True

    over_cmd = ReserveStockCommand(
        company_id=company_id,
        branch_id=branch_id,
        items=[("SKU-RES", 10)]
    )
    with pytest.raises(InsufficientStockException):
        reserve_uc.execute(over_cmd)


def test_accept_return_use_case():
    uow = InMemorySalesUnitOfWork(inventory_port=InMemoryInventoryService({"SKU-RET": 0}))
    company_id = uuid4()
    branch_id = uuid4()
    sale = Sale.create_draft(company_id=company_id, branch_id=branch_id, customer_id=uuid4(), currency="USD")
    sale.add_line(product_id=uuid4(), sku="SKU-RET", product_name="Ret Item", quantity=3, unit_price=Money.create("50.00", "USD"), tax_rate=Decimal("0.00"))
    sale.confirm()
    uow.sales.save(sale)

    return_uc = AcceptReturnUseCase(uow)
    cmd = AnnulSaleCommand(
        sale_id=sale.sale_id,
        company_id=company_id,
        reason="Defecto de fábrica"
    )
    result = return_uc.execute(cmd)

    assert result.status == SaleStatus.CANCELLED.value
    assert uow.inventory._stock["SKU-RET"] == 3
    assert uow.committed is True

    idempotent_result = return_uc.execute(cmd)
    assert idempotent_result.status == SaleStatus.CANCELLED.value


def test_unit_of_work_rolls_back_on_error():
    uow = InMemorySalesUnitOfWork(inventory_port=InMemoryInventoryService({"SKU-FAIL": 0}))
    company_id = uuid4()
    sale = Sale.create_draft(company_id=company_id, branch_id=uuid4(), customer_id=uuid4(), currency="USD")
    sale.add_line(product_id=uuid4(), sku="SKU-FAIL", product_name="Fail", quantity=5, unit_price=Money.create("10.00", "USD"))
    uow.sales.save(sale)

    confirm_uc = ConfirmSaleUseCase(uow=uow)
    cmd = ConfirmSaleCommand(sale_id=sale.sale_id, company_id=company_id)

    try:
        with uow:
            confirm_uc.execute(cmd)
    except InsufficientStockException:
        pass

    assert uow.rolled_back is True
    saved = uow.sales.get_by_id(sale.sale_id)
    assert saved.status == SaleStatus.DRAFT
