from decimal import Decimal
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
    SaleModel
)
import json
from salesia.modules.seguridad.infrastructure.security import create_access_token
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000003")
TEST_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000004")


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp = session.execute(
            select(CompanyModel).where(CompanyModel.id == TEST_COMPANY_ID)
        ).scalar_one_or_none()
        if not comp:
            comp = CompanyModel(
                id=TEST_COMPANY_ID,
                tax_id="20999999999",
                legal_name="EMPRESA COMERCIAL MATRIZ S.A.C.",
                trade_name="SALESIA CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp)

        branch = session.execute(
            select(BranchModel).where(BranchModel.id == TEST_BRANCH_ID)
        ).scalar_one_or_none()
        if not branch:
            branch = BranchModel(
                id=TEST_BRANCH_ID,
                company_id=TEST_COMPANY_ID,
                code="SUC-01",
                name="Sucursal Principal Lima",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch)

        cust = session.execute(
            select(CustomerModel).where(CustomerModel.id == TEST_CUSTOMER_ID)
        ).scalar_one_or_none()
        if not cust:
            cust = CustomerModel(
                id=TEST_CUSTOMER_ID,
                company_id=TEST_COMPANY_ID,
                code="CLI-9999",
                doc_type="RUC",
                doc_number="20555555555",
                legal_name="CLIENTE CORPORATIVO S.A.C.",
                credit_limit=Decimal("50000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

        sale_num = int(uuid4().int % 900000 + 100000)
        sale = SaleModel(
            id=uuid4(),
            company_id=TEST_COMPANY_ID,
            branch_id=TEST_BRANCH_ID,
            customer_id=TEST_CUSTOMER_ID,
            series="F001",
            number=sale_num,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            total_amount=Decimal("118.00"),
            paid_amount=Decimal("118.00")
        )
        session.add(sale)
        session.commit()
    yield


@pytest.fixture
def auth_headers():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="company_admin",
        email="admin@salesia.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_reports_catalog(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/reports", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 6
        codes = [item["code"] for item in data["items"]]
        assert "REP_SALES_DETAIL" in codes
        assert "REP_STATISTICAL_DISTRIBUTION" in codes
        assert "REP_CRM_CATALOG" in codes
        assert "REP_SALES_REPS_COMMISSIONS" in codes
        assert "REP_KARDEX_VALUATION" in codes
        assert "REP_CASH_CLOSURE_RECEIVABLES" in codes


@pytest.mark.asyncio
async def test_reports_preview(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/reports/preview?report_type=REP_SALES_DETAIL&limit=10",
            headers=auth_headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["report_type"] == "REP_SALES_DETAIL"
        assert "columns" in data
        assert "sale_id" in data["columns"]
        assert "total_amount" in data["columns"]
        assert isinstance(data["preview_sample"], list)


@pytest.mark.asyncio
async def test_report_runs_lifecycle_and_download(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        trigger_res = await client.post(
            "/api/v1/report-runs",
            json={"report_type": "REP_SALES_DETAIL", "format": "csv"},
            headers=auth_headers
        )
        assert trigger_res.status_code == 202
        run_data = trigger_res.json()
        run_id = run_data["run_id"]
        assert run_data["status"] == "completed"
        assert run_data["data_hash"].startswith("sha256-")

        status_res = await client.get(f"/api/v1/report-runs/{run_id}", headers=auth_headers)
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "completed"

        download_res = await client.get(f"/api/v1/report-runs/{run_id}/download", headers=auth_headers)
        assert download_res.status_code == 200
        assert download_res.text.startswith("\ufeff")
        assert "sale_id" in download_res.text

        with sync_session_factory() as session:
            artifact = session.execute(
                select(AnalyticsArtifact).where(AnalyticsArtifact.id == UUID(run_id))
            ).scalar_one()
            data_dict = json.loads(artifact.data_json)
            assert data_dict["downloads_count"] == 1
            data_dict["status"] = "failed"
            artifact.status = "failed"
            artifact.data_json = json.dumps(data_dict)
            session.commit()

        retry_res = await client.post(f"/api/v1/report-runs/{run_id}/retry", headers=auth_headers)
        assert retry_res.status_code == 200
        assert retry_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_report_comparison_and_scheduling(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/api/v1/report-runs",
            json={"report_type": "REP_STATISTICAL_DISTRIBUTION"},
            headers=auth_headers
        )
        r2 = await client.post(
            "/api/v1/report-runs",
            json={"report_type": "REP_STATISTICAL_DISTRIBUTION"},
            headers=auth_headers
        )
        run_1_id = r1.json()["run_id"]
        run_2_id = r2.json()["run_id"]

        comp_res = await client.post(
            "/api/v1/reports/compare",
            json={"run_id_1": run_1_id, "run_id_2": run_2_id},
            headers=auth_headers
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert "row_count_delta" in comp_data
        assert "is_identical" in comp_data

        sched_res = await client.post(
            "/api/v1/report-schedules",
            json={
                "report_type": "REP_SALES_DETAIL",
                "cron_expression": "0 8 * * 1-5",
                "format": "csv",
                "recipients": ["director@salesia.enterprise"]
            },
            headers=auth_headers
        )
        assert sched_res.status_code == 201
        sched_id = sched_res.json()["schedule_id"]

        list_sched = await client.get("/api/v1/report-schedules", headers=auth_headers)
        assert list_sched.status_code == 200
        assert any(s["schedule_id"] == sched_id for s in list_sched.json()["items"])

        del_sched = await client.delete(f"/api/v1/report-schedules/{sched_id}", headers=auth_headers)
        assert del_sched.status_code == 200


@pytest.mark.asyncio
async def test_report_safety_limits_and_branding(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        overlimit_res = await client.post(
            "/api/v1/report-runs",
            json={"report_type": "REP_SALES_DETAIL", "limit": 60000},
            headers=auth_headers
        )
        assert overlimit_res.status_code == 422 or overlimit_res.status_code == 400

        branding_res = await client.get("/api/v1/reports/branding", headers=auth_headers)
        assert branding_res.status_code == 200
        branding = branding_res.json()
        assert branding["tax_id"] in ("20999999999", "20100000001")
        assert branding["safe_logo_url"] == "/assets/brand_logo.svg"
        assert "<script>" not in branding["legal_name"]
