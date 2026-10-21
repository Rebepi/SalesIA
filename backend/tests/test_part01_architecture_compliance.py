import os
import sys
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pytest

from salesia.shared.domain.money import Money
from salesia.shared.domain.datetime_utils import (
    now_utc,
    parse_iso_utc,
    to_commercial_date,
    is_within_period
)
from salesia.shared.domain.exceptions import (
    DomainException,
    CurrencyMismatchException,
    NegativeAmountException,
    InsufficientStockException,
    InvariantViolationException
)
from salesia.modules.ventas.domain.entities import Sale, SaleStatus
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
from tests.support.in_memory_sales import (
    InMemorySaleRepository,
    InMemoryInventoryService,
    InMemorySalesUnitOfWork
)
from salesia.shared.domain.provider_ports import (
    ResilientEmailNotifier,
    CircuitBreaker
)
from salesia.shared.infrastructure.celery_app import celery_app
from salesia.shared.infrastructure.workers import compute_jitter_backoff


def test_ts_001_backend_modules_extensions():
    src_dir = Path(__file__).resolve().parent.parent / "src"
    py_files = list(src_dir.glob("**/*.py"))
    assert len(py_files) > 20
    ts_files_in_backend = list(src_dir.glob("**/*.ts")) + list(src_dir.glob("**/*.tsx"))
    assert len(ts_files_in_backend) == 0


def test_ts_002_typing_and_domain_annotations():
    sale = Sale.create_draft(
        company_id=uuid4(),
        branch_id=uuid4(),
        customer_id=uuid4(),
        currency="USD"
    )
    assert isinstance(sale.status, SaleStatus)
    assert sale.currency == "USD"
    assert isinstance(sale.lines, list)


def test_ts_006_nomenclature_and_units_integrity():
    sale = Sale.create_draft(
        company_id=uuid4(),
        branch_id=uuid4(),
        customer_id=uuid4(),
        currency="USD"
    )
    line = sale.add_line(
        product_id=uuid4(),
        sku="SKU-UNIT-TEST",
        product_name="Producto de prueba",
        quantity=5,
        unit_price=Money.create("20.00", "USD"),
        tax_rate=Decimal("0.18"),
        discount=Money.create("10.00", "USD"),
        cost_snapshot=Money.create("12.00", "USD")
    )
    assert line.quantity == 5
    assert line.unit_price.amount == Decimal("20.00")
    assert line.discount.amount == Decimal("10.00")
    assert line.tax_rate == Decimal("0.18")
    assert line.calculate_subtotal().amount == Decimal("90.00")
    assert line.calculate_tax().amount == Decimal("16.20")
    assert line.calculate_total().amount == Decimal("106.20")


def test_ts_007_money_precision_and_currency_isolation():
    m1 = Money.create("10.555", "USD").round_to(2)
    assert m1.amount == Decimal("10.56")

    m2 = Money.create("5.00", "USD")
    assert (m1 + m2).amount == Decimal("15.56")
    assert (m1 - m2).amount == Decimal("5.56")
    assert (m2 * 3).amount == Decimal("15.00")
    assert (m2 / 2).amount == Decimal("2.50")

    m_eur = Money.create("10.00", "EUR")
    with pytest.raises(CurrencyMismatchException):
        _ = m1 + m_eur

    with pytest.raises(NegativeAmountException):
        Money.create("-1.00", "USD").ensure_non_negative()


def test_ts_008_datetime_timezone_and_commercial_calendar():
    t_utc = now_utc()
    assert t_utc.tzinfo is not None

    parsed = parse_iso_utc("2026-10-10T12:00:00Z")
    assert parsed.tzinfo == timezone.utc

    comm_date = to_commercial_date(parsed, "America/Lima")
    assert comm_date.year == 2026
    assert comm_date.month == 10
    assert comm_date.day == 10

    start = parse_iso_utc("2026-10-01T00:00:00Z")
    end = parse_iso_utc("2026-10-31T23:59:59Z")
    assert is_within_period(parsed, start, end) is True
    assert is_within_period(parse_iso_utc("2026-11-01T00:00:00Z"), start, end) is False


def test_ts_009_domain_errors_codes_and_safe_translation():
    err = InsufficientStockException("SKU-1", 10, 2)
    assert err.code == "INSUFFICIENT_STOCK"
    assert "SKU-1" in err.message
    assert not hasattr(err, "sql_statement")

    inv_err = InvariantViolationException("Regla rota")
    assert inv_err.code == "INVARIANT_VIOLATION"


def test_ts_010_dependencies_manifests_and_lock():
    backend_dir = Path(__file__).resolve().parent.parent
    pyproject = backend_dir / "pyproject.toml"
    assert pyproject.exists()
    content = pyproject.read_text(encoding="utf-8")
    assert "celery" in content
    assert "PyJWT" in content
    assert "mypy" in content
    assert "hypothesis" in content

    uv_lock = backend_dir / "uv.lock"
    assert uv_lock.exists()


def test_arq_001_domain_independent_without_web_server():
    company_id = uuid4()
    branch_id = uuid4()
    customer_id = uuid4()
    sale = Sale.create_draft(company_id=company_id, branch_id=branch_id, customer_id=customer_id)
    sale.add_line(
        product_id=uuid4(),
        sku="TEST-INDEP",
        product_name="Laptop",
        quantity=2,
        unit_price=Money.create("500.00", "USD"),
        tax_rate=Decimal("0.18")
    )
    total = sale.calculate_total()
    assert total.amount == Decimal("1180.00")
    sale.confirm()
    assert sale.status == SaleStatus.CONFIRMED


def test_arq_002_explicit_use_cases_instances():
    uow = InMemorySalesUnitOfWork(inventory_port=InMemoryInventoryService({"SKU-X": 10}))
    create_uc = CreateSaleDraftUseCase(uow=uow)
    confirm_uc = ConfirmSaleUseCase(uow=uow)
    payment_uc = ApplyPaymentUseCase(uow=uow)
    reserve_uc = ReserveStockUseCase(uow=uow)
    return_uc = AcceptReturnUseCase(uow=uow)

    assert callable(create_uc.execute)
    assert callable(confirm_uc.execute)
    assert callable(payment_uc.execute)
    assert callable(reserve_uc.execute)
    assert callable(return_uc.execute)


def test_arq_003_directed_dependencies():
    import salesia.modules.ventas.domain.entities as domain_mod
    for val in dir(domain_mod):
        assert "fastapi" not in str(getattr(domain_mod, val)).lower()
        assert "react" not in str(getattr(domain_mod, val)).lower()


def test_arq_004_unit_of_work_atomicity_and_rollback():
    uow = InMemorySalesUnitOfWork(inventory_port=InMemoryInventoryService({"SKU-ATOM": 1}))
    company_id = uuid4()
    sale = Sale.create_draft(company_id=company_id, branch_id=uuid4(), customer_id=uuid4())
    sale.add_line(
        product_id=uuid4(),
        sku="SKU-ATOM",
        product_name="Atomic Test",
        quantity=5,
        unit_price=Money.create("100.00", "USD")
    )
    uow.sales.save(sale)

    confirm_uc = ConfirmSaleUseCase(uow=uow)
    cmd = ConfirmSaleCommand(sale_id=sale.sale_id, company_id=company_id)

    with pytest.raises(InsufficientStockException):
        with uow:
            confirm_uc.execute(cmd)

    assert uow.rolled_back is True
    persisted = uow.sales.get_by_id(sale.sale_id)
    assert persisted.status == SaleStatus.DRAFT
    assert uow.inventory._stock["SKU-ATOM"] == 1


def test_arq_010_isolated_workers_and_queue_configuration():
    assert "cpu_intensive" in celery_app.conf.task_routes["salesia.modules.analitica.tasks.*"]["queue"]
    assert "io_bound" in celery_app.conf.task_routes["salesia.modules.operaciones.tasks.*"]["queue"]
    assert celery_app.conf.task_time_limit == 300
    assert celery_app.conf.worker_max_memory_per_child == 512000


def test_arq_011_bounded_retries_and_backoff():
    delay_0 = compute_jitter_backoff(0, base_delay_sec=1.0, max_delay_sec=30.0)
    delay_3 = compute_jitter_backoff(3, base_delay_sec=1.0, max_delay_sec=30.0)
    delay_10 = compute_jitter_backoff(10, base_delay_sec=1.0, max_delay_sec=30.0)

    assert 1.0 <= delay_0 <= 1.3
    assert 8.0 <= delay_3 <= 10.0
    assert delay_10 <= 36.0


def test_arq_014_and_arq_015_provider_resilience_and_circuit_breaker():
    notifier = ResilientEmailNotifier(primary_provider=None)
    sale_id = uuid4()

    success = notifier.notify_sale_confirmed("customer@example.com", sale_id, "500.00")
    assert success is False
    assert len(notifier.pending_notifications) == 1
    assert notifier.pending_notifications[0]["status"] == "queued_due_to_failure"
    assert notifier.pending_notifications[0]["sale_id"] == str(sale_id)


def test_arq_016_reproducible_architecture_adrs():
    repo_root = Path(__file__).resolve().parent.parent.parent
    adr_dir = repo_root / "docs" / "adr"
    assert adr_dir.exists()
    adrs = list(adr_dir.glob("*.md"))
    assert len(adrs) >= 18
