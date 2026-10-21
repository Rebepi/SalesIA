import secrets
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, Base, sync_engine
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    InventoryStockModel,
    WarehouseModel,
    PaymentModel
)
from salesia.shared.infrastructure.transactions import RefundModel
from salesia.modules.finanzas.infrastructure_models import ReturnModel, ReturnLineModel
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from tests.support.auth_helpers import create_durable_identity


@pytest.fixture(autouse=True, scope="module")
def setup_module_tables():
    Base.metadata.create_all(sync_engine)
    yield


@pytest.fixture
def analytics_fixture():
    company_a_id = uuid4()
    company_b_id = uuid4()
    branch_a1_id = uuid4()
    branch_a2_id = uuid4()
    branch_b_id = uuid4()
    warehouse_a_id = uuid4()
    user_a_id = uuid4()
    user_b_id = uuid4()
    rep_a_id = uuid4()

    with sync_session_factory() as db:
        comp_a = CompanyModel(
            id=company_a_id,
            tax_id=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Comercial Alfa S.A.C.",
            trade_name="Alfa Enterprise",
            base_currency="USD",
            is_active=True
        )
        comp_b = CompanyModel(
            id=company_b_id,
            tax_id=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Comercial Beta S.A.C.",
            trade_name="Beta Corp",
            base_currency="USD",
            is_active=True
        )
        db.add_all([comp_a, comp_b])
        db.flush()

        br_a1 = BranchModel(
            id=branch_a1_id,
            company_id=company_a_id,
            code="SUC-CENTRAL",
            name="Sede Principal Centro",
            timezone="America/Lima",
            is_active=True
        )
        br_a2 = BranchModel(
            id=branch_a2_id,
            company_id=company_a_id,
            code="SUC-NORTE",
            name="Sede Norte",
            timezone="America/Lima",
            is_active=True
        )
        br_b = BranchModel(
            id=branch_b_id,
            company_id=company_b_id,
            code="SUC-BETA",
            name="Sede Beta",
            timezone="America/Lima",
            is_active=True
        )
        db.add_all([br_a1, br_a2, br_b])
        db.flush()

        wh_a = WarehouseModel(
            id=warehouse_a_id,
            company_id=company_a_id,
            branch_id=branch_a1_id,
            code="ALM-01",
            name="Almacen Central",
            is_active=True
        )
        db.add(wh_a)
        db.flush()

        rep_a = SalesRepresentative(
            id=rep_a_id,
            company_id=company_a_id,
            full_name="Carlos Vendedor",
            territory="Lima Centro",
            monthly_quota=Decimal("10000.00"),
            is_active=True
        )
        db.add(rep_a)

        c_historical = CustomerModel(
            id=uuid4(),
            company_id=company_a_id,
            code="CLI-HIST",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Cliente Historico Recurrente S.A.C.",
            credit_limit=Decimal("50000.00"),
            current_balance=Decimal("0.00"),
            is_active=True
        )
        c_new = CustomerModel(
            id=uuid4(),
            company_id=company_a_id,
            code="CLI-NEW",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Cliente Nuevo Primerizo S.A.C.",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("0.00"),
            is_active=True
        )
        c_beta = CustomerModel(
            id=uuid4(),
            company_id=company_b_id,
            code="CLI-BETA",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Cliente Beta S.A.C.",
            credit_limit=Decimal("10000.00"),
            current_balance=Decimal("0.00"),
            is_active=True
        )
        db.add_all([c_historical, c_new, c_beta])
        db.flush()

        p1 = ProductModel(
            id=uuid4(),
            company_id=company_a_id,
            sku="SKU-LAPTOP",
            name="Laptop Corporativa",
            category="Computo",
            unit_of_measure="NIU",
            unit_cost=Decimal("600.00"),
            unit_price=Decimal("1000.00"),
            tax_rate=Decimal("0.18"),
            is_active=True
        )
        p2 = ProductModel(
            id=uuid4(),
            company_id=company_a_id,
            sku="SKU-MOUSE",
            name="Mouse Ergonomico",
            category="Accesorios",
            unit_of_measure="NIU",
            unit_cost=Decimal("20.00"),
            unit_price=Decimal("50.00"),
            tax_rate=Decimal("0.18"),
            is_active=True
        )
        p_beta = ProductModel(
            id=uuid4(),
            company_id=company_b_id,
            sku="SKU-BETA",
            name="Producto Beta",
            category="General",
            unit_of_measure="NIU",
            unit_cost=Decimal("10.00"),
            unit_price=Decimal("20.00"),
            tax_rate=Decimal("0.18"),
            is_active=True
        )
        db.add_all([p1, p2, p_beta])
        db.flush()

        stock_p1 = InventoryStockModel(
            id=uuid4(),
            company_id=company_a_id,
            warehouse_id=warehouse_a_id,
            product_id=p1.id,
            physical_quantity=Decimal("50"),
            reserved_quantity=Decimal("5"),
            average_cost=Decimal("600.00")
        )
        db.add(stock_p1)

        now = datetime.now(timezone.utc)
        sale_hist = SaleModel(
            id=uuid4(),
            company_id=company_a_id,
            branch_id=branch_a1_id,
            customer_id=c_historical.id,
            sales_rep_id=rep_a_id,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("1000.00"),
            tax_amount=Decimal("180.00"),
            total_amount=Decimal("1180.00"),
            paid_amount=Decimal("1180.00"),
            confirmed_at=now - timedelta(days=60),
            created_at=now - timedelta(days=60)
        )
        db.add(sale_hist)
        db.flush()
        db.add(SaleLineModel(
            id=uuid4(),
            company_id=company_a_id,
            sale_id=sale_hist.id,
            product_id=p1.id,
            line_number=1,
            sku_snapshot=p1.sku,
            name_snapshot=p1.name,
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("1"),
            unit_price_snapshot=Decimal("1000.00"),
            unit_cost_snapshot=Decimal("600.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_snapshot=Decimal("0.18"),
            subtotal_amount=Decimal("1000.00"),
            tax_amount=Decimal("180.00"),
            total_amount=Decimal("1180.00")
        ))

        sale_a_curr1 = SaleModel(
            id=uuid4(),
            company_id=company_a_id,
            branch_id=branch_a1_id,
            customer_id=c_historical.id,
            sales_rep_id=rep_a_id,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("2000.00"),
            tax_amount=Decimal("360.00"),
            total_amount=Decimal("2360.00"),
            paid_amount=Decimal("2360.00"),
            confirmed_at=now - timedelta(days=5),
            created_at=now - timedelta(days=5)
        )
        db.add(sale_a_curr1)
        db.flush()
        db.add(SaleLineModel(
            id=uuid4(),
            company_id=company_a_id,
            sale_id=sale_a_curr1.id,
            product_id=p1.id,
            line_number=1,
            sku_snapshot=p1.sku,
            name_snapshot=p1.name,
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("2"),
            unit_price_snapshot=Decimal("1000.00"),
            unit_cost_snapshot=Decimal("600.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_snapshot=Decimal("0.18"),
            subtotal_amount=Decimal("2000.00"),
            tax_amount=Decimal("360.00"),
            total_amount=Decimal("2360.00")
        ))

        sale_a_curr2 = SaleModel(
            id=uuid4(),
            company_id=company_a_id,
            branch_id=branch_a2_id,
            customer_id=c_new.id,
            sales_rep_id=None,
            series="F002",
            number=int(uuid4().int % 900000 + 100000),
            status="paid",
            currency="USD",
            subtotal_amount=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            total_amount=Decimal("118.00"),
            paid_amount=Decimal("118.00"),
            confirmed_at=now - timedelta(days=2),
            created_at=now - timedelta(days=2)
        )
        db.add(sale_a_curr2)
        db.flush()
        db.add(SaleLineModel(
            id=uuid4(),
            company_id=company_a_id,
            sale_id=sale_a_curr2.id,
            product_id=p2.id,
            line_number=1,
            sku_snapshot=p2.sku,
            name_snapshot=p2.name,
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("2"),
            unit_price_snapshot=Decimal("50.00"),
            unit_cost_snapshot=Decimal("20.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_snapshot=Decimal("0.18"),
            subtotal_amount=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            total_amount=Decimal("118.00")
        ))

        sale_draft = SaleModel(
            id=uuid4(),
            company_id=company_a_id,
            branch_id=branch_a1_id,
            customer_id=c_new.id,
            sales_rep_id=rep_a_id,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="draft",
            currency="USD",
            subtotal_amount=Decimal("5000.00"),
            tax_amount=Decimal("900.00"),
            total_amount=Decimal("5900.00"),
            paid_amount=Decimal("0.00"),
            confirmed_at=None,
            created_at=now - timedelta(days=1)
        )
        sale_cancelled = SaleModel(
            id=uuid4(),
            company_id=company_a_id,
            branch_id=branch_a1_id,
            customer_id=c_new.id,
            sales_rep_id=rep_a_id,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="cancelled",
            currency="USD",
            subtotal_amount=Decimal("3000.00"),
            tax_amount=Decimal("540.00"),
            total_amount=Decimal("3540.00"),
            paid_amount=Decimal("0.00"),
            confirmed_at=now - timedelta(days=3),
            created_at=now - timedelta(days=3)
        )
        db.add_all([sale_draft, sale_cancelled])

        sale_b = SaleModel(
            id=uuid4(),
            company_id=company_b_id,
            branch_id=branch_b_id,
            customer_id=c_beta.id,
            sales_rep_id=None,
            series="B001",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("9999.00"),
            tax_amount=Decimal("1799.82"),
            total_amount=Decimal("11798.82"),
            paid_amount=Decimal("11798.82"),
            confirmed_at=now - timedelta(days=1),
            created_at=now - timedelta(days=1)
        )
        db.add(sale_b)
        db.flush()
        db.add(SaleLineModel(
            id=uuid4(),
            company_id=company_b_id,
            sale_id=sale_b.id,
            product_id=p_beta.id,
            line_number=1,
            sku_snapshot=p_beta.sku,
            name_snapshot=p_beta.name,
            unit_of_measure_snapshot="NIU",
            quantity=Decimal("10"),
            unit_price_snapshot=Decimal("20.00"),
            unit_cost_snapshot=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_snapshot=Decimal("0.18"),
            subtotal_amount=Decimal("9999.00"),
            tax_amount=Decimal("1799.82"),
            total_amount=Decimal("11798.82")
        ))
        db.commit()

    id_a = create_durable_identity(
        company_id=company_a_id,
        user_id=user_a_id,
        role="company_admin",
        email=f"admin.a.{uuid4().hex[:6]}@empresa-a.pe"
    )
    id_b = create_durable_identity(
        company_id=company_b_id,
        user_id=user_b_id,
        role="company_admin",
        email=f"admin.b.{uuid4().hex[:6]}@empresa-b.pe"
    )

    return {
        "company_a_id": company_a_id,
        "company_b_id": company_b_id,
        "branch_a1_id": branch_a1_id,
        "branch_a2_id": branch_a2_id,
        "headers_a": id_a["headers"],
        "headers_b": id_b["headers"],
        "customer_hist_id": c_historical.id,
        "customer_new_id": c_new.id,
        "rep_a_id": rep_a_id
    }


@pytest.mark.asyncio
async def test_reg17_and_fal027_drafts_excluded_and_exact_kpis(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/dashboard/summary?period=30d", headers=headers_a)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["orders_count"] == 2
        expected_rev = Decimal("2360.00") + Decimal("118.00")
        assert Decimal(data["total_revenue"]) == expected_rev
        expected_avg = (expected_rev / Decimal("2")).quantize(Decimal("0.01"))
        assert Decimal(data["average_ticket"]) == expected_avg
        assert data["distribution"]["min"] == "118.000000"
        assert data["distribution"]["max"] == "2360.000000"
        assert data["period"] == "30d"


@pytest.mark.asyncio
async def test_empty_company_shows_zero_not_mock(analytics_fixture):
    empty_company_id = uuid4()
    user_id = uuid4()
    with sync_session_factory() as db:
        c = CompanyModel(
            id=empty_company_id,
            tax_id=f"20{uuid4().int % 900000000 + 100000000}",
            legal_name="Comercial Vacia S.A.C.",
            trade_name="Vacia",
            base_currency="PEN",
            is_active=True
        )
        db.add(c)
        db.commit()
    id_empty = create_durable_identity(
        company_id=empty_company_id,
        user_id=user_id,
        role="company_admin",
        email=f"empty.{uuid4().hex[:6]}@vacia.pe"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/dashboard/summary?period=30d", headers=id_empty["headers"])
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["orders_count"] == 0
        assert Decimal(data["total_revenue"]) == Decimal("0")
        assert data["average_ticket"] is None
        assert data["median_ticket"] is None
        assert len(data["trend"]) == 0
        assert len(data["top_products"]) == 0
        assert data["currency"] == "PEN"


@pytest.mark.asyncio
async def test_api063_dashboard_summary_contract_and_isolation(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    headers_b = analytics_fixture["headers_b"]
    branch_a1 = analytics_fixture["branch_a1_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_inv = await client.get("/api/v1/dashboard/summary?period=yearly_invalid", headers=headers_a)
        assert res_inv.status_code == 422

        res_unauth = await client.get("/api/v1/dashboard/summary?period=30d")
        assert res_unauth.status_code == 401

        res_branch = await client.get(f"/api/v1/dashboard/summary?period=30d&branch_id={branch_a1}", headers=headers_a)
        assert res_branch.status_code == 200
        data_branch = res_branch.json()
        assert data_branch["orders_count"] == 1
        assert Decimal(data_branch["total_revenue"]) == Decimal("2360.00")

        res_b = await client.get("/api/v1/dashboard/summary?period=30d", headers=headers_b)
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["orders_count"] == 1
        assert Decimal(data_b["total_revenue"]) == Decimal("11798.82")
        assert Decimal(data_b["total_revenue"]) != Decimal(data_branch["total_revenue"])

        assert "comparative_period" in data_branch
        assert "inventory_summary" in data_branch
        assert "kpi_definitions" in data_branch
        assert "generated_at" in data_branch


@pytest.mark.asyncio
async def test_api064_analytics_sales_granularity_and_zero_distinction(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    headers_b = analytics_fixture["headers_b"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/sales?period=7d&granularity=day", headers=headers_a)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["count"] == 2
        assert Decimal(data["total_volume"]) == Decimal("2478.00")
        assert len(data["series"]) == 7
        zero_days = [b for b in data["series"] if b["status"] == "zero_sales"]
        recorded_days = [b for b in data["series"] if b["status"] == "recorded"]
        assert len(zero_days) >= 1
        assert len(recorded_days) >= 1
        for z in zero_days:
            assert Decimal(z["revenue"]) == Decimal("0")
            assert z["orders_count"] == 0
            assert z["has_data"] is True

        res_inv_p = await client.get("/api/v1/analytics/sales?period=15d", headers=headers_a)
        assert res_inv_p.status_code == 422
        res_inv_g = await client.get("/api/v1/analytics/sales?granularity=decade", headers=headers_a)
        assert res_inv_g.status_code == 422

        res_b = await client.get("/api/v1/analytics/sales?period=7d", headers=headers_b)
        assert res_b.status_code == 200
        assert res_b.json()["count"] == 1
        assert Decimal(res_b.json()["total_volume"]) == Decimal("11798.82")


@pytest.mark.asyncio
async def test_api065_analytics_products_ranking_and_margins(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/products?period=30d", headers=headers_a)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["count"] >= 2
        items = data["items"]
        laptop = next((it for it in items if it["sku"] == "SKU-LAPTOP"), None)
        assert laptop is not None
        assert Decimal(laptop["units"]) == Decimal("2")
        assert Decimal(laptop["base_commercial"]) == Decimal("2000.00")
        assert Decimal(laptop["revenue"]) == Decimal("2360.00")
        assert Decimal(laptop["margin_amount"]) == Decimal("800.00")
        assert Decimal(laptop["margin_pct"]) == Decimal("40.00")
        assert Decimal(laptop["share_pct"]) > Decimal("90.00")
        assert "returns_units" in laptop

        res_cat = await client.get("/api/v1/analytics/products?period=30d&category=Computo", headers=headers_a)
        assert res_cat.status_code == 200
        assert all(it["category"] == "Computo" for it in res_cat.json()["items"])

        res_inv = await client.get("/api/v1/analytics/products?period=bad_period", headers=headers_a)
        assert res_inv.status_code == 422


@pytest.mark.asyncio
async def test_api066_analytics_customers_history_window(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    c_hist_id = str(analytics_fixture["customer_hist_id"])
    c_new_id = str(analytics_fixture["customer_new_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/customers?period=30d", headers=headers_a)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["count"] >= 2
        items = data["items"]

        hist_cust = next((it for it in items if it["customer_id"] == c_hist_id), None)
        new_cust = next((it for it in items if it["customer_id"] == c_new_id), None)
        assert hist_cust is not None
        assert new_cust is not None

        assert hist_cust["customer_type"] == "recurring"
        assert new_cust["customer_type"] == "new"
        assert hist_cust["orders_count"] == 1
        assert Decimal(hist_cust["total_revenue"]) == Decimal("2360.00")
        assert new_cust["orders_count"] == 1
        assert Decimal(new_cust["total_revenue"]) == Decimal("118.00")

        summary = data["summary"]
        assert summary["recurring_customers_count"] >= 1
        assert summary["new_customers_count"] >= 1


@pytest.mark.asyncio
async def test_api067_analytics_sellers_reconciliation(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    rep_a_id = str(analytics_fixture["rep_a_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/sellers?period=30d", headers=headers_a)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["reconciliation_checked"] is True
        total_period_rev = Decimal(data["total_revenue"])
        items = data["items"]
        unassigned = data["unassigned"]

        seller_rep = next((it for it in items if it["seller_id"] == rep_a_id), None)
        assert seller_rep is not None
        assert seller_rep["sales_count"] == 1
        assert Decimal(seller_rep["total_revenue"]) == Decimal("2360.00")
        assert Decimal(seller_rep["quota_target"]) == Decimal("10000.00")
        assert Decimal(seller_rep["quota_completion_pct"]) == Decimal("23.60")

        assert unassigned["sales_count"] == 1
        assert Decimal(unassigned["total_revenue"]) == Decimal("118.00")

        sum_sellers = sum(Decimal(it["total_revenue"]) for it in items)
        assert sum_sellers + Decimal(unassigned["total_revenue"]) == total_period_rev


@pytest.mark.asyncio
async def test_ana001_to_ana020_filters_and_statistics_invariance(analytics_fixture):
    headers_a = analytics_fixture["headers_a"]
    branch_a1 = analytics_fixture["branch_a1_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dash_all = await client.get("/api/v1/dashboard/summary?period=30d", headers=headers_a)
        dash_br = await client.get(f"/api/v1/dashboard/summary?period=30d&branch_id={branch_a1}", headers=headers_a)
        assert dash_all.status_code == 200
        assert dash_br.status_code == 200
        assert dash_all.json()["orders_count"] == 2
        assert dash_br.json()["orders_count"] == 1

        dist5 = await client.post(
            "/api/v1/statistics/distribution",
            headers=headers_a,
            json={"values": [100, 200, 300, 400, 500, 600, 700, 800], "num_bins": 4, "bin_policy": "manual"}
        )
        dist8 = await client.post(
            "/api/v1/statistics/distribution",
            headers=headers_a,
            json={"values": [100, 200, 300, 400, 500, 600, 700, 800], "num_bins": 8, "bin_policy": "manual"}
        )
        assert dist5.status_code == 200
        assert dist8.status_code == 200
        assert dist5.json()["total_observations"] == 8
        assert dist8.json()["total_observations"] == 8
        assert dist5.json()["total_binned"] == 8
        assert dist8.json()["total_binned"] == 8

        adv = await client.post(
            "/api/v1/statistics/advanced",
            headers=headers_a,
            json={"values": [10, 11, 12, 13, 14, 15, 100], "is_sample": True}
        )
        assert adv.status_code == 200
        data_adv = adv.json()
        assert "q1" in data_adv
        assert "q3" in data_adv
        assert "lower_fence" in data_adv
        assert "upper_fence" in data_adv
        assert "outliers" in data_adv
        assert "100" in data_adv["outliers"]

        cmp = await client.post(
            "/api/v1/statistics/compare",
            headers=headers_a,
            json={"values_a": [100, 105, 110], "values_b": [100, 100, 300]}
        )
        assert cmp.status_code == 200
        assert "asimetría" in cmp.json()["explanation"].lower()
        assert "no permite concluir" in cmp.json()["explanation"].lower()
