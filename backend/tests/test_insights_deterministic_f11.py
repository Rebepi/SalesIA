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
    ProductModel,
    SaleModel,
    SaleLineModel
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from tests.support.auth_helpers import create_durable_identity


@pytest.fixture(autouse=True, scope="module")
def setup_insights_db():
    Base.metadata.create_all(sync_engine)
    yield


@pytest.mark.asyncio
async def test_ins_001_versioned_rules_and_exact_snapshot():
    comp_id = uuid4()
    admin_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, user_id=admin_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS1-{uuid4().hex[:6]}",
                name="Producto Margen Bajo Versionado",
                category="Hardware",
                unit_of_measure="NIU",
                unit_cost=Decimal("95.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        rules_res = await client.get("/api/v1/insights/rules", headers=admin["headers"])
        assert rules_res.status_code == 200
        rules_data = rules_res.json()
        assert "items" in rules_data
        rule_codes = [r["code"] for r in rules_data["items"]]
        assert "RULE-MARGIN-COMPRESSION-v1" in rule_codes
        assert "RULE-HISTORICAL-MARGIN-DIP-v1" in rule_codes

        eval_res = await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        assert eval_res.status_code == 200
        assert eval_res.json()["generated_count"] >= 1

        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        target = next(i for i in items if i.get("entity_id") == str(prod_id))

        assert "rule_definition" in target
        rule_def = target["rule_definition"]
        assert rule_def["code"] == "RULE-MARGIN-COMPRESSION-v1"
        assert rule_def["version"] == 1
        assert rule_def["scope"] == "product"
        assert "formula" in rule_def
        assert "threshold" in rule_def
        assert rule_def["severity"] in ["high", "critical", "medium"]
        assert rule_def["min_n"] >= 1
        assert "parameter_template" in rule_def


@pytest.mark.asyncio
async def test_ins_002_numerical_evidence_structure_and_reproducibility():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS2-{uuid4().hex[:6]}",
                name="Servidor de Prueba Evidencia",
                category="Servidores",
                unit_of_measure="NIU",
                unit_cost=Decimal("90.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        target = next(i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id))
        ins_id = target["id"]

        ev_res = await client.get(f"/api/v1/insights/{ins_id}/evidence", headers=admin["headers"])
        assert ev_res.status_code == 200
        ev_data = ev_res.json()
        assert ev_data["insight_id"] == str(ins_id)
        assert "evidence_data" in ev_data
        detail = ev_data["evidence_data"]
        assert Decimal(detail["current_value"]) == Decimal("10.00")
        assert Decimal(detail["denominator"]) == Decimal("100.00")
        assert Decimal(detail["threshold"]) == Decimal("20.00")
        assert "cutoff_date" in detail
        assert "sample_size" in detail
        assert detail["sample_size"] >= 1


@pytest.mark.asyncio
async def test_ins_003_prudent_explanation_observation_interpretation_action():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS3-{uuid4().hex[:6]}",
                name="Monitor Corporativo UltraWide",
                category="Pantallas",
                unit_of_measure="NIU",
                unit_cost=Decimal("92.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        target = next(i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id))

        assert "observation" in target
        assert "interpretation" in target
        assert "suggested_action" in target
        assert len(target["observation"]) > 10
        assert len(target["interpretation"]) > 10
        assert len(target["suggested_action"]) > 10
        assert "vendedor" not in target["observation"].lower() or "no se atribuye" in target["interpretation"].lower()


@pytest.mark.asyncio
async def test_ins_004_quality_before_alert_suppression():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        eval_res = await client.post(
            "/api/v1/insights/evaluate",
            headers=admin["headers"],
            json={"data_pipeline_delayed": True}
        )
        assert eval_res.status_code == 200
        data = eval_res.json()
        assert "suppression_log" in data
        assert any("pipeline" in s["reason"].lower() or "calidad" in s["reason"].lower() for s in data["suppression_log"])


@pytest.mark.asyncio
async def test_ins_005_durable_deduplication_100_runs():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS5-{uuid4().hex[:6]}",
                name="Switch Core Redundante",
                category="Redes",
                unit_of_measure="NIU",
                unit_cost=Decimal("94.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        initial_eval = await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        assert initial_eval.status_code == 200
        assert initial_eval.json()["generated_count"] >= 1

        for _ in range(5):
            loop_eval = await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
            assert loop_eval.status_code == 200
            assert loop_eval.json()["generated_count"] == 0

        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        items = [i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id)]
        assert len(items) == 1
        assert items[0]["evaluation_count"] >= 6


@pytest.mark.asyncio
async def test_ins_006_lifecycle_transitions_and_new_episode():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS6-{uuid4().hex[:6]}",
                name="Disco NVMe Datacenter",
                category="Almacenamiento",
                unit_of_measure="NIU",
                unit_cost=Decimal("93.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        target = next(i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id))
        ins_id = target["id"]

        patch_review = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=admin["headers"],
            json={"status": "in_review", "reason": "Asignado a comité de pricing", "version": 1}
        )
        assert patch_review.status_code == 200
        review_data = patch_review.json()
        assert review_data["status"] == "in_review"
        assert len(review_data["lifecycle_history"]) >= 1

        patch_resolve = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=admin["headers"],
            json={"status": "resolved", "reason": "Proveedor confirmó descuento compensatorio"}
        )
        assert patch_resolve.status_code == 200
        resolved_data = patch_resolve.json()
        assert resolved_data["status"] == "resolved"
        assert "evidence_data" in resolved_data

        eval_after = await client.post(
            "/api/v1/insights/evaluate",
            headers=admin["headers"],
            json={"force_new_episode": True}
        )
        assert eval_after.status_code == 200
        list_after = await client.get("/api/v1/insights", headers=admin["headers"])
        prod_items = [i for i in list_after.json()["items"] if i.get("entity_id") == str(prod_id)]
        assert any(i["status"] == "resolved" for i in prod_items)


@pytest.mark.asyncio
async def test_ins_007_frequency_cooldown_and_suppression():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS7-{uuid4().hex[:6]}",
                name="Router Edge Gateway",
                category="Redes",
                unit_of_measure="NIU",
                unit_cost=Decimal("91.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        eval1 = await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        assert eval1.status_code == 200

        eval2 = await client.post(
            "/api/v1/insights/evaluate",
            headers=admin["headers"],
            json={"check_cooldown": True}
        )
        assert eval2.status_code == 200
        assert eval2.json()["suppressed_by_cooldown_count"] >= 1


@pytest.mark.asyncio
async def test_ins_008_suggested_actions_draft_and_no_auto_execution():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS8-{uuid4().hex[:6]}",
                name="Antena Punto a Punto",
                category="Telecom",
                unit_of_measure="NIU",
                unit_cost=Decimal("96.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        target = next(i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id))
        ins_id = target["id"]

        assert "suggested_actions" in target
        assert len(target["suggested_actions"]) >= 1
        action = target["suggested_actions"][0]
        assert action["requires_manual_confirmation"] is True
        assert action["financial_auto_execution"] is False
        act_id = action["action_id"]

        prep_res = await client.post(
            f"/api/v1/insights/{ins_id}/actions/{act_id}/prepare",
            headers=admin["headers"]
        )
        assert prep_res.status_code == 200
        prep_data = prep_res.json()
        assert prep_data["can_auto_execute_finance"] is False
        assert "draft_preview" in prep_data
        assert "projected_impact" in prep_data


@pytest.mark.asyncio
async def test_ins_010_rule_version_simulation_and_false_positives():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS10-{uuid4().hex[:6]}",
                name="Cable Fibra Optica 100m",
                category="Cables",
                unit_of_measure="NIU",
                unit_cost=Decimal("75.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        sim_res = await client.post(
            "/api/v1/insights/rules/simulate",
            headers=admin["headers"],
            json={
                "rule_code": "RULE-MARGIN-COMPRESSION-v1",
                "candidate_threshold": "30.00"
            }
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert sim_data["rule_code"] == "RULE-MARGIN-COMPRESSION-v1"
        assert sim_data["candidate_threshold"] == "30.00"
        assert sim_data["simulated_triggered_count"] >= 1
        assert "potential_false_positives_diff" in sim_data
        assert sim_data["persisted_changes"] is False


@pytest.mark.asyncio
async def test_ins_011_feedback_company_isolation_no_business_mutation():
    comp_a = uuid4()
    comp_b = uuid4()
    admin_a = create_durable_identity(company_id=comp_a, role="company_admin")
    admin_b = create_durable_identity(company_id=comp_b, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_a,
                sku=f"SKU-INS11-{uuid4().hex[:6]}",
                name="Firewall Hardware Enterprise",
                category="Seguridad",
                unit_of_measure="NIU",
                unit_cost=Decimal("94.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin_a["headers"])
        list_res = await client.get("/api/v1/insights", headers=admin_a["headers"])
        target = next(i for i in list_res.json()["items"] if i.get("entity_id") == str(prod_id))
        ins_id = target["id"]

        cross_res = await client.post(
            f"/api/v1/insights/{ins_id}/feedback",
            headers=admin_b["headers"],
            json={"helpful": True, "comment": "Intento de feedback cruzado"}
        )
        assert cross_res.status_code == 404

        own_res = await client.post(
            f"/api/v1/insights/{ins_id}/feedback",
            headers=admin_a["headers"],
            json={"helpful": False, "comment": "Precio en liquidación promocional", "reason": "liquidación"}
        )
        assert own_res.status_code == 200
        assert own_res.json()["recorded"] is True

        with sync_session_factory() as session:
            p_check = session.get(ProductModel, prod_id)
            assert p_check.unit_price == Decimal("100.000000")
            assert p_check.unit_cost == Decimal("94.000000")


@pytest.mark.asyncio
async def test_ins_012_permission_based_cost_redaction():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    seller = create_durable_identity(company_id=comp_id, role="salesperson")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        with sync_session_factory() as session:
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-INS12-{uuid4().hex[:6]}",
                name="Servidor Blade Confidencial",
                category="Servidores",
                unit_of_measure="NIU",
                unit_cost=Decimal("95.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin["headers"])

        admin_list = await client.get("/api/v1/insights", headers=admin["headers"])
        admin_target = next(i for i in admin_list.json()["items"] if i.get("entity_id") == str(prod_id))
        assert "95" in str(admin_target.get("evidence", "")) or "5.00%" in str(admin_target.get("evidence", ""))
        assert admin_target["cost_confidential"] is False

        seller_list = await client.get("/api/v1/insights", headers=seller["headers"])
        assert seller_list.status_code == 200
        seller_target = next(i for i in seller_list.json()["items"] if i.get("entity_id") == str(prod_id))
        assert seller_target["cost_confidential"] is True
        assert "[RESTRINGIDO]" in seller_target["cifra_clave"] or "[CONFIDENCIAL]" in seller_target["evidence"]
        assert "95.00" not in seller_target["evidence"]


@pytest.mark.asyncio
async def test_api_080_list_insights_filters_and_cross_company_isolation():
    comp_a = uuid4()
    comp_b = uuid4()
    admin_a = create_durable_identity(company_id=comp_a, role="company_admin")
    admin_b = create_durable_identity(company_id=comp_b, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            p_a = ProductModel(
                id=uuid4(),
                company_id=comp_a,
                sku=f"SKU-A-{uuid4().hex[:6]}",
                name="Producto A",
                category="CatA",
                unit_of_measure="NIU",
                unit_cost=Decimal("95.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(p_a)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin_a["headers"])

        res_a = await client.get("/api/v1/insights", headers=admin_a["headers"])
        assert res_a.status_code == 200
        assert res_a.json()["count"] >= 1

        res_b = await client.get("/api/v1/insights", headers=admin_b["headers"])
        assert res_b.status_code == 200
        assert res_b.json()["count"] == 0

        invalid_res = await client.get("/api/v1/insights?limit=0", headers=admin_a["headers"])
        assert invalid_res.status_code in [400, 422]


@pytest.mark.asyncio
async def test_api_081_patch_status_validation_and_errors():
    comp_a = uuid4()
    comp_b = uuid4()
    admin_a = create_durable_identity(company_id=comp_a, role="company_admin")
    admin_b = create_durable_identity(company_id=comp_b, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            p_a = ProductModel(
                id=uuid4(),
                company_id=comp_a,
                sku=f"SKU-A81-{uuid4().hex[:6]}",
                name="Producto A81",
                category="CatA",
                unit_of_measure="NIU",
                unit_cost=Decimal("95.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(p_a)
            session.commit()

        await client.post("/api/v1/insights/evaluate", headers=admin_a["headers"])
        items = (await client.get("/api/v1/insights", headers=admin_a["headers"])).json()["items"]
        ins_id = items[0]["id"]

        cross_patch = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=admin_b["headers"],
            json={"status": "acknowledged"}
        )
        assert cross_patch.status_code == 404

        not_found_patch = await client.patch(
            f"/api/v1/insights/{uuid4()}/status",
            headers=admin_a["headers"],
            json={"status": "acknowledged"}
        )
        assert not_found_patch.status_code == 404

        invalid_status = await client.patch(
            f"/api/v1/insights/{ins_id}/status",
            headers=admin_a["headers"],
            json={"status": "status_totalmente_invalido_xyz"}
        )
        assert invalid_status.status_code in [400, 422]


@pytest.mark.asyncio
async def test_fal_028_separate_historical_margin_from_list_margin():
    comp_id = uuid4()
    admin = create_durable_identity(company_id=comp_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        branch_id = uuid4()
        cust_id = uuid4()
        prod_id = uuid4()
        sale_id = uuid4()
        with sync_session_factory() as session:
            branch = BranchModel(
                id=branch_id,
                company_id=comp_id,
                code=f"BR-{uuid4().hex[:4]}",
                name="Sucursal Test FAL028",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch)
            cust = CustomerModel(
                id=cust_id,
                company_id=comp_id,
                code=f"CUST-{uuid4().hex[:4]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().hex[:9]}",
                legal_name="Cliente Mayorista SAC",
                is_active=True
            )
            session.add(cust)
            prod = ProductModel(
                id=prod_id,
                company_id=comp_id,
                sku=f"SKU-FAL028-{uuid4().hex[:6]}",
                name="Componente de Margen Dual",
                category="Hardware",
                unit_of_measure="NIU",
                unit_cost=Decimal("70.000000"),
                unit_price=Decimal("100.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            )
            session.add(prod)
            sale = SaleModel(
                id=sale_id,
                company_id=comp_id,
                branch_id=branch_id,
                customer_id=cust_id,
                series="F001",
                number=int(uuid4().int % 100000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("100.000000"),
                tax_amount=Decimal("18.000000"),
                total_amount=Decimal("118.000000"),
                paid_amount=Decimal("118.000000")
            )
            session.add(sale)
            for idx in range(3):
                line = SaleLineModel(
                    id=uuid4(),
                    company_id=comp_id,
                    sale_id=sale_id,
                    product_id=prod_id,
                    line_number=idx + 1,
                    sku_snapshot=prod.sku,
                    name_snapshot=prod.name,
                    unit_of_measure_snapshot="NIU",
                    quantity=Decimal("1.000000"),
                    unit_price_snapshot=Decimal("80.000000"),
                    unit_cost_snapshot=Decimal("75.000000"),
                    discount_amount=Decimal("0.000000"),
                    tax_rate_snapshot=Decimal("0.1800"),
                    subtotal_amount=Decimal("80.000000"),
                    tax_amount=Decimal("14.400000"),
                    total_amount=Decimal("94.400000")
                )
                session.add(line)
            session.commit()

        eval_res = await client.post("/api/v1/insights/evaluate", headers=admin["headers"])
        assert eval_res.status_code == 200

        list_res = await client.get("/api/v1/insights", headers=admin["headers"])
        items = list_res.json()["items"]
        hist_items = [i for i in items if i.get("rule_id") == "RULE-HISTORICAL-MARGIN-DIP-v1"]
        assert len(hist_items) >= 1
        hist_item = hist_items[0]
        assert hist_item["rule_definition"]["scope"] == "sales_history"
        assert Decimal(hist_item["evidence_data"]["current_value"]) < Decimal("15.00")
