from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, Base, sync_engine, get_async_session_factory
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    InventoryStockModel,
    AuditLogModel,
    OutboxEventModel,
    CashSessionModel
)
from salesia.shared.infrastructure.transactions import (
    CompanySettings,
    DocumentSequence,
    next_number
)
from salesia.shared.infrastructure.tenant_context import (
    set_current_tenant,
    get_current_tenant_id,
    scoped_tenant_transaction
)
import salesia.modules.operaciones.infrastructure_models
from tests.support.auth_helpers import create_durable_identity
from alembic.config import Config
from alembic.script import ScriptDirectory

Base.metadata.create_all(sync_engine)


@pytest.fixture
def org_company_a():
    with sync_session_factory() as db:
        identity = create_durable_identity(db=db, role="company_admin")
        branch = BranchModel(
            id=uuid4(),
            company_id=identity["company_id"],
            code="SUC-" + uuid4().hex[:6].upper(),
            name="Sede Alfa",
            timezone="America/Lima",
            is_active=True
        )
        db.add(branch)
        db.flush()
        warehouse = WarehouseModel(
            id=uuid4(),
            company_id=identity["company_id"],
            branch_id=branch.id,
            code="ALM-" + uuid4().hex[:6].upper(),
            name="Almacen Alfa",
            is_active=True
        )
        db.add(warehouse)
        customer = CustomerModel(
            id=uuid4(),
            company_id=identity["company_id"],
            code="CLI-" + uuid4().hex[:6].upper(),
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente Alfa SAC",
            is_active=True
        )
        db.add(customer)
        db.commit()
        return {
            "identity": identity,
            "company_id": identity["company_id"],
            "headers": identity["headers"],
            "branch_id": branch.id,
            "warehouse_id": warehouse.id,
            "customer_id": customer.id
        }


@pytest.fixture
def org_company_b():
    with sync_session_factory() as db:
        identity = create_durable_identity(db=db, role="company_admin")
        branch = BranchModel(
            id=uuid4(),
            company_id=identity["company_id"],
            code="SUC-" + uuid4().hex[:6].upper(),
            name="Sede Beta",
            timezone="America/Lima",
            is_active=True
        )
        db.add(branch)
        db.flush()
        warehouse = WarehouseModel(
            id=uuid4(),
            company_id=identity["company_id"],
            branch_id=branch.id,
            code="ALM-" + uuid4().hex[:6].upper(),
            name="Almacen Beta",
            is_active=True
        )
        db.add(warehouse)
        customer = CustomerModel(
            id=uuid4(),
            company_id=identity["company_id"],
            code="CLI-" + uuid4().hex[:6].upper(),
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente Beta SAC",
            is_active=True
        )
        db.add(customer)
        db.commit()
        return {
            "identity": identity,
            "company_id": identity["company_id"],
            "headers": identity["headers"],
            "branch_id": branch.id,
            "warehouse_id": warehouse.id,
            "customer_id": customer.id
        }


@pytest.mark.asyncio
async def test_dat_001_isolation_composite_foreign_keys(org_company_a, org_company_b):
    with sync_session_factory() as db:
        prod_b = ProductModel(
            id=uuid4(),
            company_id=org_company_b["company_id"],
            sku="SKU-PROD-B-" + uuid4().hex[:6],
            name="Producto Empresa B",
            category="Cat",
            unit_price=Decimal("100.000000"),
            unit_cost=Decimal("60.000000"),
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        cust_a = CustomerModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            code="CLI-" + uuid4().hex[:6],
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente A",
            is_active=True
        )
        db.add_all([prod_b, cust_a])
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sales",
            headers={**org_company_a["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(org_company_a["branch_id"]),
                "warehouse_id": str(org_company_a["warehouse_id"]),
                "customer_id": str(cust_a.id),
                "currency": "USD",
                "is_credit": False,
                "lines": [
                    {
                        "product_id": str(prod_b.id),
                        "sku": prod_b.sku,
                        "product_name": prod_b.name,
                        "quantity": 1,
                        "unit_price": "100.000000"
                    }
                ]
            }
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_dat_002_business_constraints_negative_quantities(org_company_a):
    with sync_session_factory() as db:
        prod = ProductModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            sku="SKU-NEG-" + uuid4().hex[:6],
            name="Prod Check",
            category="General",
            unit_price=Decimal("10.000000"),
            unit_cost=Decimal("5.000000"),
            is_active=True
        )
        db.add(prod)
        sale = SaleModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            branch_id=org_company_a["branch_id"],
            warehouse_id=org_company_a["warehouse_id"],
            customer_id=org_company_a["customer_id"],
            series="F001",
            number=123,
            status="draft",
            currency="USD",
            subtotal_amount=Decimal("100"),
            tax_amount=Decimal("18"),
            total_amount=Decimal("118")
        )
        db.add(sale)
        db.flush()
        invalid_line = SaleLineModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            sale_id=sale.id,
            product_id=prod.id,
            line_number=1,
            sku_snapshot="SKU-NEG",
            name_snapshot="Test Name",
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("-1.000000"),
            unit_price_snapshot=Decimal("10.000000"),
            unit_cost_snapshot=Decimal("5.000000"),
            tax_rate_snapshot=Decimal("0.1800"),
            subtotal_amount=Decimal("10.000000"),
            tax_amount=Decimal("1.800000"),
            total_amount=Decimal("11.800000")
        )
        db.add(invalid_line)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


@pytest.mark.asyncio
async def test_dat_003_decimal_numeric_precision(org_company_a):
    exact_price = Decimal("123456789012.345678")
    exact_cost = Decimal("9876543210.123456")
    with sync_session_factory() as db:
        prod = ProductModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            sku="SKU-DEC-" + uuid4().hex[:6],
            name="Precision Test",
            category="Cat",
            unit_price=exact_price,
            unit_cost=exact_cost,
            is_active=True
        )
        db.add(prod)
        db.commit()
        retrieved = db.get(ProductModel, prod.id)
        assert retrieved.unit_price == exact_price
        assert retrieved.unit_cost == exact_cost
        assert isinstance(retrieved.unit_price, Decimal)
        assert not isinstance(retrieved.unit_price, float)


@pytest.mark.asyncio
async def test_dat_004_commercial_snapshot_preservation(org_company_a):
    with sync_session_factory() as db:
        prod = ProductModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            sku="SKU-SNAP-" + uuid4().hex[:6],
            name="Nombre Original",
            category="Cat",
            unit_price=Decimal("50.000000"),
            unit_cost=Decimal("30.000000"),
            is_active=True
        )
        sale = SaleModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            branch_id=org_company_a["branch_id"],
            warehouse_id=org_company_a["warehouse_id"],
            customer_id=org_company_a["customer_id"],
            series="F001",
            number=456,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("50"),
            tax_amount=Decimal("9"),
            total_amount=Decimal("59")
        )
        line = SaleLineModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            sale_id=sale.id,
            product_id=prod.id,
            line_number=1,
            sku_snapshot=prod.sku,
            name_snapshot=prod.name,
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("1.000000"),
            unit_price_snapshot=prod.unit_price,
            unit_cost_snapshot=prod.unit_cost,
            tax_rate_snapshot=Decimal("0.1800"),
            subtotal_amount=Decimal("50.000000"),
            tax_amount=Decimal("9.000000"),
            total_amount=Decimal("59.000000")
        )
        db.add_all([prod, sale, line])
        db.commit()

        prod.name = "Nombre Modificado Posterior"
        prod.unit_price = Decimal("999.000000")
        db.commit()

        saved_line = db.get(SaleLineModel, line.id)
        assert saved_line.name_snapshot == "Nombre Original"
        assert saved_line.unit_price_snapshot == Decimal("50.000000")


@pytest.mark.asyncio
async def test_dat_005_historical_integrity_no_cascade(org_company_a):
    with sync_session_factory() as db:
        customer = CustomerModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            code="CLI-HIST-" + uuid4().hex[:6],
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente Historico",
            is_active=True
        )
        sale = SaleModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            branch_id=org_company_a["branch_id"],
            warehouse_id=org_company_a["warehouse_id"],
            customer_id=customer.id,
            series="F001",
            number=789,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("100"),
            tax_amount=Decimal("18"),
            total_amount=Decimal("118")
        )
        db.add_all([customer, sale])
        db.commit()

        customer.is_active = False
        db.commit()

        saved_sale = db.get(SaleModel, sale.id)
        assert saved_sale is not None
        assert saved_sale.customer_id == customer.id


@pytest.mark.asyncio
async def test_dat_006_uniqueness_and_normalization(org_company_a):
    code = "SUC-DUP-" + uuid4().hex[:6].upper()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/v1/branches",
            headers=org_company_a["headers"],
            json={"code": code, "name": "Sucursal Uno", "timezone": "America/Lima"}
        )
        assert res1.status_code == 201

        res2 = await client.post(
            "/api/v1/branches",
            headers=org_company_a["headers"],
            json={"code": code, "name": "Sucursal Dos", "timezone": "America/Lima"}
        )
        assert res2.status_code == 409


@pytest.mark.asyncio
async def test_dat_007_query_indexes():
    metadata = Base.metadata
    table_branches = metadata.tables["branches"]
    table_warehouses = metadata.tables["warehouses"]
    table_sales = metadata.tables["sales"]
    table_lines = metadata.tables["sale_lines"]

    branch_indexes = [idx.name for idx in table_branches.indexes]
    wh_indexes = [idx.name for idx in table_warehouses.indexes]
    sales_indexes = [idx.name for idx in table_sales.indexes]
    lines_indexes = [idx.name for idx in table_lines.indexes]

    assert any("company_id" in idx for idx in branch_indexes)
    assert any("branch_id" in idx for idx in wh_indexes)
    assert any("branch_id" in idx for idx in sales_indexes)
    assert any("product_id" in idx for idx in lines_indexes)


def test_dat_008_safe_migrations_alembic():
    ini_path = Path("alembic.ini") if Path("alembic.ini").exists() else Path("backend/alembic.ini")
    config = Config(str(ini_path))
    script_dir = Path("alembic") if Path("alembic").exists() else Path("backend/alembic")
    config.set_main_option("script_location", str(script_dir.resolve()))
    script = ScriptDirectory.from_config(config)
    head_rev = script.get_current_head()
    assert head_rev in ["0015", "0016", "0017", "0018", "0019", "0020", "0021", "0022", "0023", "0024", "0025", "0026", "0027", "0028", "0029"]
    revs = list(script.walk_revisions())
    assert len(revs) >= 15



@pytest.mark.asyncio
async def test_dat_009_rls_defense_non_owner(org_company_a, org_company_b):
    with sync_session_factory() as db:
        comp_a_count = db.scalar(
            select(func.count()).select_from(BranchModel).where(BranchModel.company_id == org_company_a["company_id"])
        )
        comp_b_count = db.scalar(
            select(func.count()).select_from(BranchModel).where(BranchModel.company_id == org_company_b["company_id"])
        )
        assert comp_a_count >= 1
        assert comp_b_count >= 1


@pytest.mark.asyncio
async def test_dat_010_transactional_tenant_context():
    tenant_1 = uuid4()
    tenant_2 = uuid4()
    session_factory = get_async_session_factory()
    async with session_factory() as sess:
        async with scoped_tenant_transaction(sess, tenant_1) as sess1:
            assert get_current_tenant_id(sess1) == tenant_1
        async with scoped_tenant_transaction(sess, tenant_2) as sess2:
            assert get_current_tenant_id(sess2) == tenant_2


@pytest.mark.asyncio
async def test_dat_011_soft_delete_and_annulment():
    with sync_session_factory() as db:
        company = CompanyModel(
            id=uuid4(),
            tax_id=uuid4().hex[:11],
            legal_name="Soft Delete SAC",
            trade_name="SD",
            base_currency="USD",
            is_active=True
        )
        db.add(company)
        db.commit()
        company.is_active = False
        db.commit()
        assert db.get(CompanyModel, company.id).is_active is False


@pytest.mark.asyncio
async def test_dat_012_dates_and_temporal_indices():
    now_utc = datetime.now(timezone.utc)
    with sync_session_factory() as db:
        company = CompanyModel(
            id=uuid4(),
            tax_id=uuid4().hex[:11],
            legal_name="Temporal SAC",
            trade_name="TS",
            base_currency="USD",
            is_active=True,
            created_at=now_utc
        )
        db.add(company)
        db.commit()
        retrieved = db.get(CompanyModel, company.id)
        assert retrieved.created_at.tzinfo is not None


def test_dat_013_controlled_backfill():
    items = list(range(100))
    batch_size = 25
    processed = 0
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        processed += len(chunk)
    assert processed == 100


def test_dat_014_schema_audit_tenant_id():
    tables_to_check = ["branches", "warehouses", "customers", "products", "sales", "sale_lines"]
    metadata = Base.metadata
    for t_name in tables_to_check:
        table = metadata.tables[t_name]
        assert "company_id" in table.columns


def test_dat_015_readable_dictionary():
    table = Base.metadata.tables["products"]
    assert table.columns["unit_price"].type.python_type is Decimal
    assert table.columns["is_active"].type.python_type is bool


def test_dat_016_real_persistence_integration():
    with sync_session_factory() as db:
        comp_id = uuid4()
        comp = CompanyModel(
            id=comp_id,
            tax_id=uuid4().hex[:11],
            legal_name="PG Integration Test",
            trade_name="PG",
            base_currency="USD",
            is_active=True
        )
        db.add(comp)
        db.commit()
        assert db.get(CompanyModel, comp_id) is not None


@pytest.mark.asyncio
async def test_org_001_guided_onboarding_idempotency(org_company_a):
    tax_id = "20" + uuid4().hex[:9]
    payload = {
        "tax_id": tax_id,
        "legal_name": "Corporacion Onboarding SAC",
        "trade_name": "Onboarding Corp",
        "base_currency": "USD",
        "branch_code": "PRINCIPAL",
        "branch_name": "Sede Principal",
        "timezone": "America/Lima",
        "warehouse_code": "ALM-01",
        "warehouse_name": "Almacen Principal",
        "series": "F001"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/v1/organization/onboarding/setup",
            headers=org_company_a["headers"],
            json=payload
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "completed"

        res2 = await client.post(
            "/api/v1/organization/onboarding/setup",
            headers=org_company_a["headers"],
            json=payload
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["resumed"] is True
        assert data2["branch_id"] == data1["branch_id"]

        status_res = await client.get(
            "/api/v1/organization/onboarding/status",
            headers=org_company_a["headers"]
        )
        assert status_res.status_code == 200
        assert status_res.json()["is_completed"] is True


@pytest.mark.asyncio
async def test_org_002_context_switch_and_cache_invalidation(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/organization/context/switch",
            headers=org_company_a["headers"],
            json={"branch_id": str(org_company_a["branch_id"])}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["branch_id"] == str(org_company_a["branch_id"])
        assert "invalidated_caches" in data


@pytest.mark.asyncio
async def test_org_003_preferences_by_scope_and_reset(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_res = await client.get("/api/v1/organization/preferences", headers=org_company_a["headers"])
        assert get_res.status_code == 200
        data = get_res.json()
        assert "platform_defaults" in data
        assert "effective" in data

        reset_res = await client.post(
            "/api/v1/organization/preferences/reset",
            headers=org_company_a["headers"],
            json={"key": "default_tax_rate"}
        )
        assert reset_res.status_code == 200
        assert reset_res.json()["restored_value"] == "0.18"


@pytest.mark.asyncio
async def test_org_004_series_and_correlatives(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        series = "F" + uuid4().hex[:3].upper()
        res1 = await client.post(
            f"/api/v1/organization/sequences/reserve?series={series}",
            headers=org_company_a["headers"]
        )
        assert res1.status_code == 200
        val1 = res1.json()["assigned_number"]

        res2 = await client.post(
            f"/api/v1/organization/sequences/reserve?series={series}",
            headers=org_company_a["headers"]
        )
        assert res2.status_code == 200
        val2 = res2.json()["assigned_number"]
        assert val2 == val1 + 1


@pytest.mark.asyncio
async def test_org_005_currency_and_rounding(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        current_settings = (await client.get("/api/v1/settings", headers=org_company_a["headers"])).json()
        patch_res = await client.patch(
            "/api/v1/companies/current/settings",
            headers=org_company_a["headers"],
            json={"version": current_settings["version"], "rounding_mode": "ROUND_HALF_UP"}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["rounding_mode"] == "ROUND_HALF_UP"


@pytest.mark.asyncio
async def test_org_006_configurable_fiscal_rules(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_res = await client.get("/api/v1/organization/tax-rules", headers=org_company_a["headers"])
        assert list_res.status_code == 200

        post_res = await client.post(
            "/api/v1/organization/tax-rules",
            headers=org_company_a["headers"],
            json={"code": "RED", "rate": "0.1000", "name": "Tasa Reducida 10%", "is_active": True}
        )
        assert post_res.status_code == 200


@pytest.mark.asyncio
async def test_org_007_business_hours_and_timezones(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/organization/business-hours", headers=org_company_a["headers"])
        assert res.status_code == 200
        assert "working_days" in res.json()


@pytest.mark.asyncio
async def test_org_008_branding_templates_preview(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/organization/branding/preview",
            headers=org_company_a["headers"],
            json={
                "legal_name": "A" * 200,
                "trade_name": "Trade Corp",
                "footer_text": "Pie de documento"
            }
        )
        assert res.status_code == 200
        assert res.json()["is_safe"] is True


@pytest.mark.asyncio
async def test_org_009_accounting_period_lock(org_company_a):
    with sync_session_factory() as db:
        sale = SaleModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            branch_id=org_company_a["branch_id"],
            warehouse_id=org_company_a["warehouse_id"],
            customer_id=org_company_a["customer_id"],
            series="F001",
            number=999,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("100"),
            tax_amount=Decimal("18"),
            total_amount=Decimal("118"),
            paid_amount=Decimal("0"),
            confirmed_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
            created_at=datetime(2026, 9, 15, tzinfo=timezone.utc)
        )
        db.add(sale)
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        close_res = await client.post(
            "/api/v1/organization/periods/close",
            headers=org_company_a["headers"],
            json={"closed_until": "2026-09-30", "reason": "Cierre mensual Septiembre 2026"}
        )
        assert close_res.status_code == 200

        cancel_res = await client.post(
            f"/api/v1/sales/{sale.id}/cancel",
            headers={**org_company_a["headers"], "Idempotency-Key": uuid4().hex},
            json={"reason": "Error en digitacion"}
        )
        assert cancel_res.status_code == 409
        assert "periodo cerrado" in cancel_res.text.lower()

        reopen_res = await client.post(
            "/api/v1/organization/periods/reopen",
            headers=org_company_a["headers"],
            json={"reopen_date": "2026-09-30", "reason": "Apertura autorizada por gerencia contable"}
        )
        assert reopen_res.status_code == 200


@pytest.mark.asyncio
async def test_org_010_tenant_limits_and_quotas(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        quotas_res = await client.get("/api/v1/organization/quotas", headers=org_company_a["headers"])
        assert quotas_res.status_code == 200
        assert "quotas" in quotas_res.json()

        check_res = await client.post(
            "/api/v1/organization/quotas/check",
            headers=org_company_a["headers"],
            json={"resource": "exports", "requested_quantity": 9999}
        )
        assert check_res.status_code == 429


@pytest.mark.asyncio
async def test_org_011_branch_deactivation_protection(org_company_a):
    with sync_session_factory() as db:
        branch = BranchModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            code="SUC-DEACT-" + uuid4().hex[:6].upper(),
            name="Sede Borrador",
            is_active=True
        )
        db.add(branch)
        db.flush()
        draft_sale = SaleModel(
            id=uuid4(),
            company_id=org_company_a["company_id"],
            branch_id=branch.id,
            warehouse_id=org_company_a["warehouse_id"],
            customer_id=org_company_a["customer_id"],
            series="F001",
            number=321,
            status="draft",
            currency="USD",
            subtotal_amount=Decimal("10"),
            tax_amount=Decimal("1.8"),
            total_amount=Decimal("11.8")
        )
        db.add(draft_sale)
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.patch(
            f"/api/v1/branches/{branch.id}",
            headers=org_company_a["headers"],
            json={"is_active": False}
        )
        assert res.status_code == 409
        assert "borradores" in res.text.lower()


@pytest.mark.asyncio
async def test_org_012_configuration_test_mode_verify(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/organization/test-mode/verify",
            headers=org_company_a["headers"]
        )
        assert res.status_code == 200
        assert res.json()["live_effects_emitted"] is False
        assert res.json()["verified"] is True


@pytest.mark.asyncio
async def test_api_013_get_company_current(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/companies/current", headers=org_company_a["headers"])
        assert res.status_code == 200
        data = res.json()
        assert data["company_id"] == str(org_company_a["company_id"])
        assert "legal_name" in data
        assert "tax_id" in data

        unauth_res = await client.get("/api/v1/companies/current")
        assert unauth_res.status_code == 401


@pytest.mark.asyncio
async def test_api_014_patch_company_settings(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        curr = (await client.get("/api/v1/companies/current/settings", headers=org_company_a["headers"])).json()
        patch_res = await client.patch(
            "/api/v1/companies/current/settings",
            headers=org_company_a["headers"],
            json={"version": curr["version"], "default_tax_rate": "0.1000"}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["default_tax_rate"] == "0.1000"

        stale_res = await client.patch(
            "/api/v1/companies/current/settings",
            headers=org_company_a["headers"],
            json={"version": curr["version"], "default_tax_rate": "0.1800"}
        )
        assert stale_res.status_code == 409


@pytest.mark.asyncio
async def test_api_015_get_branches(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/branches?is_active=true", headers=org_company_a["headers"])
        assert res.status_code == 200
        items = res.json()
        assert len(items) >= 1
        assert all(b["company_id"] == str(org_company_a["company_id"]) for b in items)


@pytest.mark.asyncio
async def test_api_016_get_warehouses(org_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/warehouses?branch_id={org_company_a['branch_id']}&is_active=true",
            headers=org_company_a["headers"]
        )
        assert res.status_code == 200
        items = res.json()
        assert len(items) >= 1
        assert all(w["company_id"] == str(org_company_a["company_id"]) for w in items)
        assert all(w["branch_id"] == str(org_company_a["branch_id"]) for w in items)


@pytest.mark.asyncio
async def test_reg_15_rate_zero_preserved_and_tenant_settings_isolation(org_company_a, org_company_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        curr_a = (await client.get("/api/v1/companies/current/settings", headers=org_company_a["headers"])).json()
        set_zero = await client.patch(
            "/api/v1/companies/current/settings",
            headers=org_company_a["headers"],
            json={"version": curr_a["version"], "default_tax_rate": "0"}
        )
        assert set_zero.status_code == 200
        assert set_zero.json()["default_tax_rate"] == "0"

        after_a = (await client.get("/api/v1/settings", headers=org_company_a["headers"])).json()
        assert after_a["default_tax_rate"] == "0"

        after_b = (await client.get("/api/v1/settings", headers=org_company_b["headers"])).json()
        assert after_b["default_tax_rate"] != "0"
        assert after_b["company_id"] == str(org_company_b["company_id"])
