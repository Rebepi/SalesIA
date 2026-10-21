from datetime import datetime, timezone, timedelta
from decimal import Decimal
from time import perf_counter
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    CustomerModel,
    SaleModel,
    WarehouseModel,
    ProductModel,
    InventoryStockModel
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A_ID = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B_ID = UUID("00000000-0000-0000-0000-000000000099")
BRANCH_A_ID = UUID("00000000-0000-0000-0000-000000000002")
USER_A_ID = UUID("00000000-0000-0000-0000-000000000002")
USER_B_ID = UUID("00000000-0000-0000-0000-000000000088")
SHARED_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000005")


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp_a = session.execute(
            select(CompanyModel).where(CompanyModel.id == COMPANY_A_ID)
        ).scalar_one_or_none()
        if not comp_a:
            comp_a = CompanyModel(
                id=COMPANY_A_ID,
                tax_id="20999999991",
                legal_name="EMPRESA QA MATRIZ S.A.C.",
                trade_name="SALESIA CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp_a)

        comp_b = session.execute(
            select(CompanyModel).where(CompanyModel.id == COMPANY_B_ID)
        ).scalar_one_or_none()
        if not comp_b:
            comp_b = CompanyModel(
                id=COMPANY_B_ID,
                tax_id="20999999992",
                legal_name="EMPRESA QA COMPETENCIA S.A.C.",
                trade_name="RIVAL CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp_b)
        session.flush()

        branch_a = session.execute(
            select(BranchModel).where(BranchModel.id == BRANCH_A_ID)
        ).scalar_one_or_none()
        if not branch_a:
            branch_a = BranchModel(
                id=BRANCH_A_ID,
                company_id=COMPANY_A_ID,
                code="SUC-QA-01",
                name="Sucursal QA Principal",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch_a)

        cust = session.execute(
            select(CustomerModel).where(CustomerModel.id == SHARED_CUSTOMER_ID)
        ).scalar_one_or_none()
        if not cust:
            cust = CustomerModel(
                id=SHARED_CUSTOMER_ID,
                company_id=COMPANY_A_ID,
                code="CLI-QA-SHARED",
                doc_type="RUC",
                doc_number="20444555666",
                legal_name="CLIENTE COMPARTIDO QA S.A.C.",
                credit_limit=Decimal("50000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

        session.commit()
    yield


@pytest.fixture
def auth_headers_a():
    identity = create_durable_identity(
        company_id=COMPANY_A_ID,
        user_id=USER_A_ID,
        role="company_admin",
        email="admin_qa_a@salesia.enterprise",
        password="valid_password"
    )
    return identity["headers"]


@pytest.fixture
def auth_headers_b():
    identity = create_durable_identity(
        company_id=COMPANY_B_ID,
        user_id=USER_B_ID,
        role="company_admin",
        email="admin_qa_b@rival.enterprise",
        password="valid_password"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_bug_014_cent_accuracy_and_split_rounding(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        warehouse_id = uuid4()
        prod_id = uuid4()
        sku_rnd = f"SKU-RND-{uuid4().hex[:6]}"
        with sync_session_factory() as session:
            cust = CustomerModel(
                id=customer_id,
                company_id=COMPANY_A_ID,
                code=f"CLI-RND-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 900000000 + 100000000}",
                legal_name="CLIENTE EXACTITUD CENTIMOS S.A.C.",
                credit_limit=Decimal("50000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

            wh = WarehouseModel(
                id=warehouse_id,
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                code=f"WH-RND-{uuid4().hex[:4]}",
                name="Almacen Redondeo",
                is_active=True
            )
            session.add(wh)

            prod = ProductModel(
                id=prod_id,
                company_id=COMPANY_A_ID,
                sku=sku_rnd,
                name="Licencia Software Mensual",
                category="LICENCIAS",
                unit_of_measure="NIU",
                unit_price=Decimal("10.33"),
                unit_cost=Decimal("5.00"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        draft_res = await client.post(
            "/api/v1/sales/draft",
            json={
                "customer_id": str(customer_id),
                "branch_id": str(BRANCH_A_ID),
                "warehouse_id": str(warehouse_id),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_rnd,
                        "product_name": "Licencia Software Mensual",
                        "quantity": 3,
                        "unit_price": "10.33",
                        "tax_rate": "0.18"
                    }
                ]
            },
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex}
        )
        assert draft_res.status_code == 201
        sale = draft_res.json()
        assert Decimal(sale["total_amount"]).quantize(Decimal("0.01")) == Decimal("36.57")


@pytest.mark.asyncio
async def test_bug_023_tenant_isolation_idor(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_a_id = uuid4()
        with sync_session_factory() as session:
            sale_a = SaleModel(
                id=sale_a_id,
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                customer_id=SHARED_CUSTOMER_ID,
                series="F001",
                number=int(uuid4().int % 900000 + 100000),
                status="draft",
                currency="USD",
                subtotal_amount=Decimal("50.00"),
                tax_amount=Decimal("9.00"),
                total_amount=Decimal("59.00"),
                paid_amount=Decimal("0.00")
            )
            session.add(sale_a)
            session.commit()

        cross_access = await client.get(f"/api/v1/sales/{sale_a_id}", headers=auth_headers_b)
        assert cross_access.status_code in (403, 404)


@pytest.mark.asyncio
async def test_bug_030_and_035_statistical_edge_cases(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_stat = await client.post(
            "/api/v1/statistics/mean",
            json={"values": []},
            headers=auth_headers_a
        )
        assert empty_stat.status_code in (400, 422)

        zero_bayes = await client.post(
            "/api/v1/probability/bayes",
            json={
                "prior_a": "0.50",
                "likelihood_b_given_a": "0.00",
                "likelihood_b_given_not_a": "0.00"
            },
            headers=auth_headers_a
        )
        assert zero_bayes.status_code == 400
        assert "evidencia" in zero_bayes.json()["detail"].lower()


@pytest.mark.asyncio
async def test_qa_002_and_003_conservation_and_idempotency(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        warehouse_id = uuid4()
        prod_id = uuid4()
        sku_idem = f"SKU-IDEM-{uuid4().hex[:6]}"
        with sync_session_factory() as session:
            cust = CustomerModel(
                id=customer_id,
                company_id=COMPANY_A_ID,
                code=f"CLI-IDEM-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 900000000 + 100000000}",
                legal_name="CLIENTE CONSERVACION S.A.C.",
                credit_limit=Decimal("10000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

            wh = WarehouseModel(
                id=warehouse_id,
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                code=f"WH-IDEM-{uuid4().hex[:4]}",
                name="Almacen Idempotencia",
                is_active=True
            )
            session.add(wh)

            prod = ProductModel(
                id=prod_id,
                company_id=COMPANY_A_ID,
                sku=sku_idem,
                name="Producto Prueba",
                category="GENERAL",
                unit_of_measure="NIU",
                unit_price=Decimal("50.00"),
                unit_cost=Decimal("30.00"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(prod)

            stock = InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A_ID,
                warehouse_id=warehouse_id,
                product_id=prod_id,
                physical_quantity=Decimal("20.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)
            session.commit()

        sale_res = await client.post(
            "/api/v1/sales/draft",
            json={
                "customer_id": str(customer_id),
                "branch_id": str(BRANCH_A_ID),
                "warehouse_id": str(warehouse_id),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_idem,
                        "product_name": "Producto Prueba",
                        "quantity": 2,
                        "unit_price": "50.00",
                        "tax_rate": "0.18"
                    }
                ]
            },
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex}
        )
        assert sale_res.status_code == 201
        sale_id = sale_res.json()["sale_id"]

        confirm_key = uuid4().hex
        confirm_1 = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_a, "Idempotency-Key": confirm_key}
        )
        assert confirm_1.status_code == 200

        confirm_2 = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_a, "Idempotency-Key": confirm_key}
        )
        assert confirm_2.status_code == 200
        assert confirm_1.json()["sale_id"] == confirm_2.json()["sale_id"]
        assert confirm_1.json()["total_amount"] == confirm_2.json()["total_amount"]


@pytest.mark.asyncio
async def test_uat_flow_end_to_end(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        warehouse_id = uuid4()
        prod_id = uuid4()
        sku_uat = f"PROD-UAT-{uuid4().hex[:6]}"
        with sync_session_factory() as session:
            cust = CustomerModel(
                id=customer_id,
                company_id=COMPANY_A_ID,
                code=f"CLI-UAT-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 900000000 + 100000000}",
                legal_name="CLIENTE UAT S.A.C.",
                credit_limit=Decimal("50000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

            wh = WarehouseModel(
                id=warehouse_id,
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                code=f"WH-UAT-{uuid4().hex[:4]}",
                name="Almacen UAT",
                is_active=True
            )
            session.add(wh)

            prod = ProductModel(
                id=prod_id,
                company_id=COMPANY_A_ID,
                sku=sku_uat,
                name="Servidor Cloud Enterprise",
                category="EQUIPOS",
                unit_of_measure="NIU",
                unit_price=Decimal("250.00"),
                unit_cost=Decimal("150.00"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(prod)

            stock = InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A_ID,
                warehouse_id=warehouse_id,
                product_id=prod_id,
                physical_quantity=Decimal("10.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)
            session.commit()

        valid_future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        quote_res = await client.post(
            "/api/v1/quotations",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(customer_id),
                "branch_id": str(BRANCH_A_ID),
                "valid_until": valid_future,
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_uat,
                        "name": "Servidor Cloud Enterprise",
                        "quantity": "1.00",
                        "unit_price": "250.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert quote_res.status_code == 201
        quote_id = quote_res.json()["quotation_id"]

        accept_res = await client.post(
            f"/api/v1/quotations/{quote_id}/accept",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex}
        )
        assert accept_res.status_code == 200

        convert_res = await client.post(
            f"/api/v1/quotations/{quote_id}/convert?warehouse_id={warehouse_id}",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex}
        )
        assert convert_res.status_code == 201
        order_data = convert_res.json()
        assert "order_id" in order_data

        sale_res = await client.post(
            "/api/v1/sales",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A_ID),
                "customer_id": str(customer_id),
                "warehouse_id": str(warehouse_id),
                "currency": "USD",
                "lines": [{
                    "product_id": str(prod_id),
                    "sku": sku_uat,
                    "product_name": "Servidor Cloud Enterprise",
                    "quantity": 1,
                    "unit_price": "250.00",
                    "cost_snapshot": "150.00",
                    "tax_rate": "0.18"
                }]
            }
        )
        assert sale_res.status_code == 201
        sale_id = sale_res.json()["sale_id"]
        confirm_sale = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex},
            json={"is_credit_sale": False}
        )
        assert confirm_sale.status_code == 200

        payment_res = await client.post(
            "/api/v1/payments",
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex},
            json={"sale_id": sale_id, "payment_method": "CASH", "amount": "295.00", "currency": "USD"}
        )
        assert payment_res.status_code == 201
        with sync_session_factory() as session:
            stock_after_sale = session.scalar(select(InventoryStockModel).where(
                InventoryStockModel.company_id == COMPANY_A_ID,
                InventoryStockModel.warehouse_id == warehouse_id,
                InventoryStockModel.product_id == prod_id
            ))
            assert stock_after_sale.physical_quantity == Decimal("9.000000")

        dataset_res = await client.post(
            "/api/v1/datasets",
            headers=auth_headers_a,
            json={"name": f"Dataset UAT {uuid4().hex[:6]}", "grain": "ticket", "source_entity": "sales"}
        )
        assert dataset_res.status_code == 201
        dataset_id = dataset_res.json()["id"]
        version_res = await client.post(
            f"/api/v1/datasets/{dataset_id}/versions",
            headers=auth_headers_a,
            json={}
        )
        assert version_res.status_code == 201
        assert version_res.json()["row_count"] >= 1

        mean_res = await client.post(
            "/api/v1/statistics/mean",
            headers=auth_headers_a,
            json={"dataset_id": dataset_id, "dataset_version": version_res.json()["version"], "variable_name": "total_amount"}
        )
        assert mean_res.status_code == 200
        assert Decimal(mean_res.json()["mean"]) > 0

        reports_res = await client.get("/api/v1/reports", headers=auth_headers_a)
        assert reports_res.status_code == 200
        assert reports_res.json()["count"] >= 1

        run_res = await client.post(
            "/api/v1/report-runs",
            json={"report_type": "REP_SALES_DETAIL", "format": "csv"},
            headers={**auth_headers_a, "Idempotency-Key": uuid4().hex}
        )
        assert run_res.status_code == 202
        run_id = run_res.json()["run_id"]

        download_res = await client.get(f"/api/v1/report-runs/{run_id}/download", headers=auth_headers_a)
        assert download_res.status_code == 200
        assert download_res.text.startswith("\ufeff")

        audit_res = await client.get("/api/v1/audit/logs/verify", headers=auth_headers_a)
        assert audit_res.status_code == 200
        assert audit_res.json()["is_valid"] is True
        assert audit_res.json()["verified_count"] >= 1


@pytest.mark.asyncio
async def test_analytics_performance_with_large_sales_volume(auth_headers_a):
    created = datetime.now(timezone.utc)
    with sync_session_factory() as session:
        session.add_all([
            SaleModel(
                id=uuid4(),
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                customer_id=SHARED_CUSTOMER_ID,
                series="PERF",
                number=index + 1,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("100.00"),
                tax_amount=Decimal("18.00"),
                total_amount=Decimal("118.00"),
                paid_amount=Decimal("118.00"),
                confirmed_at=created,
                created_at=created,
            )
            for index in range(2000)
        ])
        session.commit()

    timings = {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        started = perf_counter()
        dashboard = await client.get("/api/v1/dashboard/summary?period=30d", headers=auth_headers_a)
        timings["dashboard"] = perf_counter() - started
        assert dashboard.status_code == 200

        started = perf_counter()
        dataset = await client.post(
            "/api/v1/datasets",
            headers=auth_headers_a,
            json={"name": f"Dataset rendimiento {uuid4().hex[:6]}", "grain": "ticket", "source_entity": "sales"}
        )
        assert dataset.status_code == 201
        version = await client.post(
            f"/api/v1/datasets/{dataset.json()['id']}/versions",
            headers=auth_headers_a,
            json={}
        )
        timings["dataset"] = perf_counter() - started
        assert version.status_code == 201
        assert version.json()["row_count"] >= 2000

        started = perf_counter()
        statistics = await client.post(
            "/api/v1/statistics/mean",
            headers=auth_headers_a,
            json={
                "dataset_id": dataset.json()["id"],
                "dataset_version": version.json()["version"],
                "variable_name": "total_amount",
            }
        )
        timings["statistics"] = perf_counter() - started
        assert statistics.status_code == 200

        started = perf_counter()
        report = await client.get(
            "/api/v1/reports/preview?report_type=REP_SALES_DETAIL&limit=20",
            headers=auth_headers_a
        )
        timings["report"] = perf_counter() - started
        assert report.status_code == 200

    assert set(timings) == {"dashboard", "dataset", "statistics", "report"}
    assert all(duration < 10 for duration in timings.values()), timings
