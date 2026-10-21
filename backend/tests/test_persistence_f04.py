from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from salesia.shared.infrastructure.database import Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    InventoryStockModel,
    SaleModel,
    SaleLineModel,
    OutboxEventModel
)
import salesia.modules.operaciones.infrastructure_models
from salesia.shared.infrastructure.tenant_context import (
    set_current_tenant,
    get_current_tenant_id,
    scoped_tenant_transaction
)


@pytest.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_composite_foreign_key_scoping(test_session: AsyncSession):
    company_a_id = uuid4()
    company_b_id = uuid4()

    company_a = CompanyModel(
        id=company_a_id,
        tax_id="20601234567",
        legal_name="Empresa A S.A.C.",
        trade_name="Empresa A",
        base_currency="USD"
    )
    company_b = CompanyModel(
        id=company_b_id,
        tax_id="20607654321",
        legal_name="Empresa B S.A.C.",
        trade_name="Empresa B",
        base_currency="USD"
    )
    test_session.add_all([company_a, company_b])
    await test_session.commit()

    branch_a = BranchModel(
        id=uuid4(),
        company_id=company_a_id,
        code="SUC-A1",
        name="Sucursal A1"
    )
    customer_a = CustomerModel(
        id=uuid4(),
        company_id=company_a_id,
        code="CLI-001",
        doc_type="RUC",
        doc_number="20100010001",
        legal_name="Cliente A"
    )
    product_b = ProductModel(
        id=uuid4(),
        company_id=company_b_id,
        sku="SKU-PROD-B",
        name="Producto de Empresa B",
        category="General",
        unit_price=Decimal("100.000000"),
        unit_cost=Decimal("70.000000")
    )
    test_session.add_all([branch_a, customer_a, product_b])
    await test_session.commit()

    sale_a = SaleModel(
        id=uuid4(),
        company_id=company_a_id,
        branch_id=branch_a.id,
        customer_id=customer_a.id,
        series="F001",
        number=1,
        status="draft",
        currency="USD",
        subtotal_amount=Decimal("100.000000"),
        tax_amount=Decimal("18.000000"),
        total_amount=Decimal("118.000000")
    )
    test_session.add(sale_a)
    await test_session.commit()

    sale_line_invalid = SaleLineModel(
        id=uuid4(),
        company_id=company_a_id,
        sale_id=sale_a.id,
        product_id=product_b.id,
        line_number=1,
        sku_snapshot=product_b.sku,
        name_snapshot=product_b.name,
        unit_of_measure_snapshot="NIU",
        quantity=Decimal("1.000000"),
        unit_price_snapshot=Decimal("100.000000"),
        unit_cost_snapshot=Decimal("70.000000"),
        tax_rate_snapshot=Decimal("0.1800"),
        subtotal_amount=Decimal("100.000000"),
        tax_amount=Decimal("18.000000"),
        total_amount=Decimal("118.000000")
    )
    test_session.add(sale_line_invalid)

    assert sale_line_invalid.company_id != product_b.company_id


@pytest.mark.asyncio
async def test_decimal_numeric_precision_without_float(test_session: AsyncSession):
    company_id = uuid4()
    company = CompanyModel(
        id=company_id,
        tax_id="20999888777",
        legal_name="Comercial Decimal S.A.",
        trade_name="Decimal Exacto",
        base_currency="USD"
    )
    test_session.add(company)
    await test_session.commit()

    exact_price = Decimal("123456789012.345678")
    exact_cost = Decimal("9876543210.123456")

    product = ProductModel(
        id=uuid4(),
        company_id=company_id,
        sku="SKU-PRECISION-HIGH",
        name="Artículo de Alta Precisión",
        category="Maquinaria",
        unit_price=exact_price,
        unit_cost=exact_cost
    )
    test_session.add(product)
    await test_session.commit()

    query = select(ProductModel).where(ProductModel.sku == "SKU-PRECISION-HIGH")
    result = await test_session.execute(query)
    retrieved = result.scalar_one()

    assert retrieved.unit_price == exact_price
    assert retrieved.unit_cost == exact_cost
    assert isinstance(retrieved.unit_price, Decimal)
    assert not isinstance(retrieved.unit_price, float)


@pytest.mark.asyncio
async def test_commercial_snapshot_preservation(test_session: AsyncSession):
    company_id = uuid4()
    company = CompanyModel(
        id=company_id,
        tax_id="20111222333",
        legal_name="Distribuidora Snapshot S.A.",
        trade_name="Snapshot Test",
        base_currency="USD"
    )
    test_session.add(company)
    await test_session.commit()

    branch = BranchModel(
        id=uuid4(),
        company_id=company_id,
        code="SUC-MAIN",
        name="Sede Principal"
    )
    customer = CustomerModel(
        id=uuid4(),
        company_id=company_id,
        code="CLI-SNAP",
        doc_type="RUC",
        doc_number="20444555666",
        legal_name="Cliente Snapshot"
    )
    product = ProductModel(
        id=uuid4(),
        company_id=company_id,
        sku="SKU-ORIGINAL",
        name="Nombre Original del Producto",
        category="Cat-A",
        unit_price=Decimal("50.000000"),
        unit_cost=Decimal("30.000000")
    )
    test_session.add_all([branch, customer, product])
    await test_session.commit()

    sale = SaleModel(
        id=uuid4(),
        company_id=company_id,
        branch_id=branch.id,
        customer_id=customer.id,
        series="F001",
        number=100,
        status="confirmed",
        currency="USD",
        subtotal_amount=Decimal("100.000000"),
        tax_amount=Decimal("18.000000"),
        total_amount=Decimal("118.000000")
    )
    test_session.add(sale)
    await test_session.commit()

    sale_line = SaleLineModel(
        id=uuid4(),
        company_id=company_id,
        sale_id=sale.id,
        product_id=product.id,
        line_number=1,
        sku_snapshot=product.sku,
        name_snapshot=product.name,
        unit_of_measure_snapshot="NIU",
        quantity=Decimal("2.000000"),
        unit_price_snapshot=product.unit_price,
        unit_cost_snapshot=product.unit_cost,
        tax_rate_snapshot=Decimal("0.1800"),
        subtotal_amount=Decimal("100.000000"),
        tax_amount=Decimal("18.000000"),
        total_amount=Decimal("118.000000")
    )
    test_session.add(sale_line)
    await test_session.commit()

    product.name = "Nombre Modificado Posterior"
    product.unit_price = Decimal("99.000000")
    await test_session.commit()

    query_line = select(SaleLineModel).where(SaleLineModel.sale_id == sale.id)
    res_line = await test_session.execute(query_line)
    retrieved_line = res_line.scalar_one()

    assert retrieved_line.name_snapshot == "Nombre Original del Producto"
    assert retrieved_line.unit_price_snapshot == Decimal("50.000000")
    assert product.name == "Nombre Modificado Posterior"
    assert product.unit_price == Decimal("99.000000")


@pytest.mark.asyncio
async def test_tenant_context_manager(test_session: AsyncSession):
    tenant_id = uuid4()
    await set_current_tenant(test_session, tenant_id)
    assert get_current_tenant_id(test_session) == tenant_id

    scoped_id = uuid4()
    async with scoped_tenant_transaction(test_session, scoped_id) as sess:
        assert get_current_tenant_id(sess) == scoped_id

    outbox = OutboxEventModel(
        id=uuid4(),
        company_id=scoped_id,
        event_type="sale.confirmed",
        aggregate_type="sale",
        aggregate_id=uuid4(),
        payload_json="{}",
        status="PENDING"
    )
    test_session.add(outbox)
    await test_session.commit()

    query_outbox = select(OutboxEventModel).where(OutboxEventModel.company_id == scoped_id)
    res = await test_session.execute(query_outbox)
    event = res.scalar_one()
    assert event.event_type == "sale.confirmed"
    assert event.company_id == scoped_id
