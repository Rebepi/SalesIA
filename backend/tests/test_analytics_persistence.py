import secrets
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, ProductModel, UserModel


@pytest.fixture
def analytics_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "private_storage_path", str(tmp_path))
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Analítica", trade_name="Analítica")
        db.add(company)
        db.flush()
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        product = ProductModel(company_id=company.id, sku=uuid4().hex[:10], name="Margen Bajo", category="General", unit_of_measure="NIU", unit_price=Decimal("100"), unit_cost=Decimal("90"), tax_rate=Decimal("0.18"))
        db.add_all([user, product])
        db.commit()
        return {"email": user.email, "password": password}


async def analytics_client(identity):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    login = await client.post("/api/v1/auth/login", json={"email": identity["email"], "password": identity["password"]})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


@pytest.mark.asyncio
async def test_dataset_versions_and_unknown_analysis_are_real(analytics_identity):
    client = await analytics_client(analytics_identity)
    try:
        created = await client.post("/api/v1/datasets", json={"name": "Ventas", "variable_scale": "quantitative_continuous"})
        assert created.status_code == 201, created.text
        dataset_id = created.json()["id"]
        version = await client.post(f"/api/v1/datasets/{dataset_id}/versions", json={"row_count": 0, "data_hash": "sha256-empty", "schema_snapshot": {"columns": []}})
        assert version.status_code == 201, version.text
        loaded = await client.get(f"/api/v1/datasets/{dataset_id}/versions/2")
        assert loaded.json()["row_count"] == 0
        assert (await client.get(f"/api/v1/datasets/{uuid4()}/versions/1")).status_code == 404
        assert (await client.get(f"/api/v1/analyses/{uuid4()}")).status_code == 404
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_insights_deduplicate_and_unknown_updates_fail(analytics_identity):
    client = await analytics_client(analytics_identity)
    try:
        first = await client.post("/api/v1/insights/evaluate")
        second = await client.post("/api/v1/insights/evaluate")
        assert first.json()["generated_count"] == 1
        assert second.json()["generated_count"] == 0
        items = (await client.get("/api/v1/insights")).json()["items"]
        insight_id = items[0]["id"]
        changed = await client.patch(f"/api/v1/insights/{insight_id}/status", json={"status": "acknowledged"})
        assert changed.json()["status"] == "acknowledged"
        assert (await client.patch(f"/api/v1/insights/{uuid4()}/status", json={"status": "dismissed"})).status_code == 404
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_report_artifact_is_durable_and_downloadable(analytics_identity):
    client = await analytics_client(analytics_identity)
    try:
        run = await client.post("/api/v1/report-runs", json={"report_type": "REP_CRM_CATALOG", "format": "csv", "limit": 100})
        assert run.status_code == 202, run.text
        run_id = run.json()["run_id"]
        status = await client.get(f"/api/v1/report-runs/{run_id}")
        assert status.json()["status"] == "completed"
        download = await client.get(f"/api/v1/report-runs/{run_id}/download")
        assert download.status_code == 200, download.text
        assert download.content.startswith(b"\xef\xbb\xbf")
        assert (await client.get(f"/api/v1/report-runs/{uuid4()}")).status_code == 404
    finally:
        await client.aclose()
