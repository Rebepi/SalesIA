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
from tests.support.auth_helpers import create_durable_identity, ensure_business_records

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000003")


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
        session.commit()
    yield


@pytest.fixture
def auth_headers():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=TEST_COMPANY_ID,
            user_id=TEST_USER_ID,
            role="company_admin",
            email="admin@salesia.enterprise"
        )
        return identity["headers"]


@pytest.mark.asyncio
async def test_advanced_statistics_variance_stdev_iqr_outliers(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "values": ["10.00", "11.00", "12.00", "10.50", "11.50", "10.80", "120.00"],
            "is_sample": True
        }
        res = await client.post("/api/v1/statistics/advanced", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 7
        assert Decimal(data["variance"]) > Decimal("1000.00")
        assert Decimal(data["standard_deviation"]) > Decimal("30.00")
        assert data["outliers_count"] == 1
        assert "120.00" in data["outliers"][0]
        assert data["skewness"] == "sesgo_positivo_derecha"


@pytest.mark.asyncio
async def test_smoothed_bayes_and_laplace_regularization(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "count_a_and_b": 1,
            "count_not_a_and_b": 0,
            "total_a": 5,
            "total_not_a": 5,
            "prior_a": "0.40",
            "alpha": "1.0"
        }
        res = await client.post("/api/v1/probability/smoothed-bayes", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert Decimal(data["smoothed_likelihood_b_given_a"]) == Decimal("0.285714")
        assert Decimal(data["smoothed_likelihood_b_given_not_a"]) == Decimal("0.142857")
        assert Decimal(data["posterior_a_given_b"]) > Decimal("0.40")


@pytest.mark.asyncio
async def test_operational_dataset_extraction_reproducibility(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            records = ensure_business_records(session, TEST_COMPANY_ID, branch_id=TEST_BRANCH_ID)
            sale = SaleModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                branch_id=TEST_BRANCH_ID,
                customer_id=records["customer_id"],
                series="B005",
                number=int(uuid4().int % 1000000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("500.000000"),
                tax_amount=Decimal("90.000000"),
                total_amount=Decimal("590.000000"),
                paid_amount=Decimal("590.000000")
            )
            session.add(sale)
            session.commit()

        extract_res = await client.post(
            "/api/v1/datasets/extract-operational",
            headers=auth_headers,
            json={"grain": "ticket", "limit": 50}
        )
        assert extract_res.status_code == 200
        d_data = extract_res.json()
        assert d_data["grain"] == "ticket"
        assert d_data["row_count"] >= 1
        assert d_data["null_count"] == 0
        assert d_data["duplicate_count"] == 0
        assert d_data["data_hash"].startswith("sha256-")
        assert len(d_data["preview_sample"]) >= 1


@pytest.mark.asyncio
async def test_statistical_distribution_properties(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        even_sample = ["10.00", "20.00", "30.00", "40.00"]
        med_res = await client.post("/api/v1/statistics/median", json={"values": even_sample}, headers=auth_headers)
        assert med_res.status_code == 200
        assert Decimal(med_res.json()["median"]) == Decimal("25.000000")

        var_res = await client.post(
            "/api/v1/random-variables/analyze",
            json={
                "name": "tiempo_despacho_minutos",
                "scale": "quantitative_continuous",
                "observations": ["15.0", "15.0", "15.0", "15.0"]
            },
            headers=auth_headers
        )
        assert var_res.status_code == 200
        var_data = var_res.json()
        assert var_data["distinct_values_count"] == 1
        assert var_data["skewness_direction"] == "simetrica"
