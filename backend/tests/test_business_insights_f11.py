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
    ProductModel
)
from salesia.modules.seguridad.infrastructure.security import create_access_token
from tests.support.auth_helpers import create_durable_identity

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
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="company_admin",
        email="admin@salesia.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_insights_evaluation_and_deduplication(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            low_margin_prod = ProductModel(
                id=prod_id,
                company_id=TEST_COMPANY_ID,
                sku=f"SKU-LOWMARGIN-{uuid4().hex[:6]}",
                name="Memoria RAM Servidor Low Margin",
                category="Hardware",
                unit_of_measure="NIU",
                unit_cost=Decimal("95.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(low_margin_prod)
            session.commit()

        eval1_res = await client.post("/api/v1/insights/evaluate", headers=auth_headers)
        assert eval1_res.status_code == 200
        eval1_data = eval1_res.json()
        assert eval1_data["status"] == "evaluated"
        assert eval1_data["generated_count"] >= 1

        eval2_res = await client.post("/api/v1/insights/evaluate", headers=auth_headers)
        assert eval2_res.status_code == 200

        list_res = await client.get("/api/v1/insights", headers=auth_headers)
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert len(items) >= 1
        found = [i for i in items if i.get("rule_id") == "RULE-MARGIN-COMPRESSION-v1"]
        assert len(found) >= 1


@pytest.mark.asyncio
async def test_insight_lifecycle_and_feedback(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_res = await client.get("/api/v1/insights", headers=auth_headers)
        assert list_res.status_code == 200
        first_insight = list_res.json()["items"][0]
        ins_id = first_insight["id"]

        patch_res = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=auth_headers,
            json={"status": "acknowledged"}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "acknowledged"

        patch2_res = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=auth_headers,
            json={"status": "actioned"}
        )
        assert patch2_res.status_code == 200
        assert patch2_res.json()["status"] == "actioned"

        fb_res = await client.post(
            f"/api/v1/insights/{ins_id}/feedback",
            headers=auth_headers,
            json={"helpful": True, "comment": "Alerta pertinente para renegociación con proveedor"}
        )
        assert fb_res.status_code == 200
        assert fb_res.json()["recorded"] is True


@pytest.mark.asyncio
async def test_ai_query_grounded_response(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ai_res = await client.post(
            "/api/v1/ai/query",
            headers=auth_headers,
            json={"query": "¿Cuál es el resumen de operaciones y tendencias de venta?"}
        )
        assert ai_res.status_code == 200
        data = ai_res.json()
        assert len(data["facts_cited"]) >= 2
        assert Decimal(data["confidence_score"]) >= Decimal("0.90")
        assert len(data["suggested_next_steps"]) >= 1


@pytest.mark.asyncio
async def test_ai_simulation_dry_run_and_emergency_pause(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sim_res = await client.post(
            "/api/v1/ai/simulate-action",
            headers=auth_headers,
            json={
                "action_type": "adjust_safety_stock",
                "parameters": {"product_sku": "SKU-SWITCH-48P", "target_increase_pct": 15}
            }
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert sim_data["simulation_mode"] is True
        assert sim_data["state_mutated"] is False
        assert "projected_impact" in sim_data

        pause_res = await client.post(
            "/api/v1/ai/emergency-pause",
            headers=auth_headers,
            json={"reason": "Mantenimiento programado de reglas de inventario"}
        )
        assert pause_res.status_code == 200
        assert pause_res.json()["automation_paused"] is True

        resume_res = await client.post(
            "/api/v1/ai/resume",
            headers=auth_headers
        )
        assert resume_res.status_code == 200
        assert resume_res.json()["automation_paused"] is False
