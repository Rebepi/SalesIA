from decimal import Decimal
import json
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.analitica.domain.probability import (
    validate_structured_condition,
    validate_temporal_leakage,
    validate_manual_bayes_inputs,
    calculate_empirical_probability,
    calculate_empirical_bayes_full,
    run_two_proportions_hypothesis_test
)
from salesia.shared.domain.exceptions import (
    EmptySampleException,
    InvariantViolationException,
    ZeroEvidenceException
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A_ID = UUID("00000000-0000-0000-0000-000000000001")
USER_A_ID = UUID("00000000-0000-0000-0000-000000000088")

COMPANY_B_ID = UUID("00000000-0000-0000-0000-000000000099")
USER_B_ID = UUID("00000000-0000-0000-0000-000000000089")


@pytest.fixture(autouse=True, scope="module")
def setup_probability_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp_a = session.execute(
            select(CompanyModel).where(CompanyModel.id == COMPANY_A_ID)
        ).scalar_one_or_none()
        if not comp_a:
            comp_a = CompanyModel(
                id=COMPANY_A_ID,
                tax_id="20100000001",
                legal_name="EMPRESA COMERCIAL A S.A.C.",
                trade_name="SALESIA ALPHA",
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
                tax_id="20900000002",
                legal_name="EMPRESA COMERCIAL B S.A.C.",
                trade_name="SALESIA BETA",
                base_currency="USD",
                is_active=True
            )
            session.add(comp_b)
        session.commit()
    yield


@pytest.fixture
def auth_headers_a():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            role="company_admin",
            email="admin_a_prob@salesia.enterprise"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_b():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_B_ID,
            user_id=USER_B_ID,
            role="company_admin",
            email="admin_b_prob@salesia.enterprise"
        )
        return identity["headers"]


@pytest.mark.asyncio
async def test_prob_001_universe_definition_and_same_universe(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "sample_space_size": 1000,
            "event_a_count": 200,
            "event_b_count": 120,
            "intersection_count": 60,
            "universe_definition": {
                "entity": "sales",
                "period": "30d",
                "eligibility_criteria": "ventas_confirmadas_periodo"
            }
        }
        res = await client.post("/api/v1/probability/events", json=payload, headers=auth_headers_a)
        assert res.status_code == 200
        data = res.json()
        assert data["is_defined"] is True
        assert data["sample_space_size"] == 1000
        assert data["event_a_count"] == 200
        assert data["event_b_count"] == 120
        assert data["intersection_count"] == 60
        assert data["contingency_table"]["grand_total"] == 1000


@pytest.mark.asyncio
async def test_prob_002_commercial_events_structured_and_sql_rejection(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        valid_payload = {
            "sample_space_size": 500,
            "event_a_count": 100,
            "event_b_count": 50,
            "intersection_count": 20,
            "event_a_definition": {
                "name": "Compra Recurrente",
                "description": "Clientes con compra en canal digital",
                "condition": {
                    "field": "channel",
                    "operator": "eq",
                    "value": "ecommerce"
                }
            },
            "event_b_definition": {
                "name": "Ticket Alto",
                "description": "Ventas mayores o iguales a 500",
                "condition": {
                    "field": "total_amount",
                    "operator": "gte",
                    "value": 500
                }
            }
        }
        res = await client.post("/api/v1/probability/events", json=valid_payload, headers=auth_headers_a)
        assert res.status_code == 200

        sql_injection_payload = {
            "sample_space_size": 500,
            "event_a_count": 100,
            "event_b_count": 50,
            "intersection_count": 20,
            "event_a_definition": {
                "name": "Ataque SQL",
                "description": "Intento de SQL arbitrario",
                "condition": {
                    "field": "category",
                    "operator": "eq",
                    "value": "electronica; DROP TABLE users; --"
                }
            }
        }
        bad_res = await client.post("/api/v1/probability/events", json=sql_injection_payload, headers=auth_headers_a)
        assert bad_res.status_code == 400
        assert "no permitidas" in bad_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_prob_003_unique_counts_customers_vs_sales(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_id = uuid4()
        cust_1 = str(uuid4())
        cust_2 = str(uuid4())
        rows = [
            {"id": str(uuid4()), "customer_id": cust_1, "total_amount": "100.00"},
            {"id": str(uuid4()), "customer_id": cust_1, "total_amount": "150.00"},
            {"id": str(uuid4()), "customer_id": cust_1, "total_amount": "200.00"},
            {"id": str(uuid4()), "customer_id": cust_2, "total_amount": "80.00"}
        ]
        with sync_session_factory() as session:
            session.add(AnalyticsArtifact(
                id=dataset_id,
                company_id=COMPANY_A_ID,
                kind="dataset",
                artifact_key=str(dataset_id),
                version=1,
                status="active",
                data_json=json.dumps({"rows": rows, "grain": "lines"}),
                created_by=USER_A_ID
            ))
            session.add(AnalyticsArtifact(
                id=uuid4(),
                company_id=COMPANY_A_ID,
                kind="dataset_version",
                artifact_key=str(dataset_id),
                version=1,
                status="active",
                data_json=json.dumps({"rows": rows, "storage_type": "inline"}),
                created_by=USER_A_ID
            ))
            session.commit()

        res_cust = await client.post(
            "/api/v1/probability/events",
            json={
                "dataset_id": str(dataset_id),
                "dataset_version": 1,
                "universe_definition": {"entity": "customers"}
            },
            headers=auth_headers_a
        )
        assert res_cust.status_code == 200
        data_cust = res_cust.json()
        assert data_cust["sample_space_size"] == 2

        res_sales = await client.post(
            "/api/v1/probability/events",
            json={
                "dataset_id": str(dataset_id),
                "dataset_version": 1,
                "universe_definition": {"entity": "sales"}
            },
            headers=auth_headers_a
        )
        assert res_sales.status_code == 200
        data_sales = res_sales.json()
        assert data_sales["sample_space_size"] == 4


@pytest.mark.asyncio
async def test_prob_004_simple_probability_and_empty_universe(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_res = await client.post(
            "/api/v1/probability/events",
            json={
                "sample_space_size": 0,
                "event_a_count": 0,
                "event_b_count": 0,
                "intersection_count": 0
            },
            headers=auth_headers_a
        )
        assert empty_res.status_code == 200
        data_empty = empty_res.json()
        assert data_empty["is_defined"] is False
        assert "vacio" in data_empty["reason"].lower()
        assert data_empty["probability_a"] is None
        assert data_empty["probability_b"] is None

        valid_res = await client.post(
            "/api/v1/probability/events",
            json={
                "sample_space_size": 100,
                "event_a_count": 40,
                "event_b_count": 30,
                "intersection_count": 10
            },
            headers=auth_headers_a
        )
        assert valid_res.status_code == 200
        data_valid = valid_res.json()
        assert data_valid["probability_a"] == "0.400000"
        assert data_valid["probability_b"] == "0.300000"
        assert data_valid["probability_intersection"] == "0.100000"
        assert data_valid["probability_union"] == "0.600000"
        assert data_valid["probability_complement_a"] == "0.600000"
        assert data_valid["probability_complement_b"] == "0.700000"


@pytest.mark.asyncio
async def test_prob_005_conditional_probability_direction_labels(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/events",
            json={
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 120,
                "intersection_count": 60
            },
            headers=auth_headers_a
        )
        assert res.status_code == 200
        data = res.json()
        assert data["conditional_probability_a_given_b"] == "0.500000"
        assert data["conditional_probability_b_given_a"] == "0.300000"
        assert "P(A|B)" in data["direction_labels"]["p_a_given_b"]
        assert "n(B)=120" in data["direction_labels"]["p_a_given_b"]
        assert "P(B|A)" in data["direction_labels"]["p_b_given_a"]
        assert "n(A)=200" in data["direction_labels"]["p_b_given_a"]


@pytest.mark.asyncio
async def test_prob_006_empirical_bayes_readme_case_equivalence(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/bayes",
            json={
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 120,
                "intersection_count": 60
            },
            headers=auth_headers_a
        )
        assert res.status_code == 200
        data = res.json()
        assert data["prior_a"] == "0.200000"
        assert data["evidence_b"] == "0.120000"
        assert data["likelihood_b_given_a"] == "0.300000"
        assert data["likelihood_b_given_not_a"] == "0.075000"
        assert data["direct_count_posterior"] == "0.500000"
        assert data["posterior_a_given_b"] == "0.500000"
        assert data["equivalence_verified"] is True
        assert len(data["formula_cards"]) >= 4


@pytest.mark.asyncio
async def test_prob_007_manual_bayes_mode_proportion_vs_percentage(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad_prop = await client.post(
            "/api/v1/probability/bayes",
            json={
                "mode": "proportion",
                "prior_a": "80",
                "likelihood_b_given_a": "0.50",
                "likelihood_b_given_not_a": "0.20"
            },
            headers=auth_headers_a
        )
        assert bad_prop.status_code in (400, 422), f"Expected 400 or 422, got {bad_prop.status_code}: {bad_prop.text}"
        _body = bad_prop.json()
        _detail = str(_body.get("detail", ""))
        _errors_msgs = " ".join(str(e.get("message", "")) for e in _body.get("errors", []))
        _all_text = (_detail + " " + _errors_msgs).lower()
        assert ("proporcion" in _all_text or "porcentaje" in _all_text or "modo" in _all_text
                or "contrato" in _all_text), f"Unexpected response body: {_body}"

        ok_perc = await client.post(
            "/api/v1/probability/bayes",
            json={
                "mode": "percentage",
                "prior_a": "80",
                "likelihood_b_given_a": "50",
                "likelihood_b_given_not_a": "20"
            },
            headers=auth_headers_a
        )
        assert ok_perc.status_code == 200
        data = ok_perc.json()
        assert data["prior_a"] == "0.8" or data["prior_a"] == "0.800000"


@pytest.mark.asyncio
async def test_prob_008_impossible_evidence_rejection(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        zero_ev = await client.post(
            "/api/v1/probability/bayes",
            json={
                "prior_a": "0.40",
                "likelihood_b_given_a": "0.00",
                "evidence_b": "0.00"
            },
            headers=auth_headers_a
        )
        assert zero_ev.status_code == 400
        assert "evidencia" in zero_ev.json()["detail"].lower()


@pytest.mark.asyncio
async def test_prob_009_incompatible_inputs_rejection(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/bayes",
            json={
                "prior_a": "0.50",
                "likelihood_b_given_a": "0.80",
                "evidence_b": "0.10"
            },
            headers=auth_headers_a
        )
        assert res.status_code == 400
        assert "inconsistencia" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_prob_010_low_frequencies_warning(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/events",
            json={
                "sample_space_size": 1,
                "event_a_count": 1,
                "event_b_count": 1,
                "intersection_count": 1,
                "min_support_threshold": 30
            },
            headers=auth_headers_a
        )
        assert res.status_code == 200
        data = res.json()
        assert data["low_sample_warning"] is True
        assert data["warning_message"] is not None
        assert "bajo" in data["warning_message"].lower() or "soporte" in data["warning_message"].lower()


@pytest.mark.asyncio
async def test_prob_011_smoothing_laplace_regularization(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_no_smooth = await client.post(
            "/api/v1/probability/bayes",
            json={
                "sample_space_size": 10,
                "event_a_count": 5,
                "event_b_count": 1,
                "intersection_count": 1,
                "smoothing_enabled": False
            },
            headers=auth_headers_a
        )
        assert res_no_smooth.status_code == 200
        assert res_no_smooth.json()["smoothing_enabled"] is False

        res_smooth = await client.post(
            "/api/v1/probability/bayes",
            json={
                "sample_space_size": 10,
                "event_a_count": 5,
                "event_b_count": 1,
                "intersection_count": 1,
                "smoothing_enabled": True,
                "alpha": "1.0"
            },
            headers=auth_headers_a
        )
        assert res_smooth.status_code == 200
        data = res_smooth.json()
        assert data["smoothing_enabled"] is True
        assert data["smoothing_details"] is not None
        assert Decimal(data["smoothing_details"]["alpha"]) == Decimal("1.0")


@pytest.mark.asyncio
async def test_prob_012_no_automatic_causality_disclaimer(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/bayes",
            json={
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 120,
                "intersection_count": 60
            },
            headers=auth_headers_a
        )
        assert res.status_code == 200
        data = res.json()
        assert "causality_disclaimer" in data
        assert "no implica" in data["causality_disclaimer"].lower() or "causa" in data["causality_disclaimer"].lower()


@pytest.mark.asyncio
async def test_prob_013_no_temporal_leakage_validation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad_field = await client.post(
            "/api/v1/probability/validate-temporal",
            json={
                "predictor_fields": ["category", "post_purchase_survey"],
                "predictor_window_end": "2026-09-01",
                "outcome_window_start": "2026-09-02"
            },
            headers=auth_headers_a
        )
        assert bad_field.status_code == 400
        assert "fuga temporal" in bad_field.json()["detail"].lower()

        bad_window = await client.post(
            "/api/v1/probability/validate-temporal",
            json={
                "predictor_fields": ["category", "channel"],
                "predictor_window_end": "2026-09-15",
                "outcome_window_start": "2026-09-01"
            },
            headers=auth_headers_a
        )
        assert bad_window.status_code == 400
        assert "fuga temporal" in bad_window.json()["detail"].lower()

        ok_temp = await client.post(
            "/api/v1/probability/validate-temporal",
            json={
                "predictor_fields": ["category", "channel"],
                "predictor_window_end": "2026-08-31",
                "outcome_window_start": "2026-09-01"
            },
            headers=auth_headers_a
        )
        assert ok_temp.status_code == 200
        assert ok_temp.json()["valid"] is True


@pytest.mark.asyncio
async def test_prob_014_explainable_interface_contingency_table(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/probability/events",
            json={
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 120,
                "intersection_count": 60
            },
            headers=auth_headers_a
        )
        assert res.status_code == 200
        table = res.json()["contingency_table"]
        assert table["a_and_b"] == 60
        assert table["a_and_not_b"] == 140
        assert table["not_a_and_b"] == 60
        assert table["not_a_and_not_b"] == 740
        assert table["total_a"] == 200
        assert table["total_not_a"] == 800
        assert table["total_b"] == 120
        assert table["total_not_b"] == 880
        assert table["grand_total"] == 1000


@pytest.mark.asyncio
async def test_prob_015_persistence_exact_reopen(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        save_payload = {
            "name": f"Analisis Bayes Fidelizacion {uuid4().hex[:6]}",
            "mode": "proportion",
            "counts": {"sample_space_size": 1000, "event_a": 200, "event_b": 120, "intersection": 60},
            "probabilities": {
                "prior_a": "0.200000",
                "evidence_b": "0.120000",
                "likelihood_b_given_a": "0.300000",
                "posterior_a_given_b": "0.500000"
            },
            "smoothing_enabled": False,
            "alpha": "1.0",
            "is_simulation": False,
            "scenario_type": "observed"
        }
        create_res = await client.post("/api/v1/probability/analyses", json=save_payload, headers=auth_headers_a)
        assert create_res.status_code == 200
        created = create_res.json()
        analysis_id = created["id"]

        get_res = await client.get(f"/api/v1/probability/analyses/{analysis_id}", headers=auth_headers_a)
        assert get_res.status_code == 200
        fetched = get_res.json()
        assert fetched["name"] == save_payload["name"]
        assert fetched["probabilities"]["posterior_a_given_b"] == "0.500000"
        assert fetched["counts"]["intersection"] == 60


@pytest.mark.asyncio
async def test_prob_016_scenario_comparison_and_simulation_tag(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        base_payload = {
            "name": f"Base Observada {uuid4().hex[:6]}",
            "probabilities": {"prior_a": "0.200000", "posterior_a_given_b": "0.500000"},
            "is_simulation": False,
            "scenario_type": "observed"
        }
        c1 = await client.post("/api/v1/probability/analyses", json=base_payload, headers=auth_headers_a)
        id_1 = c1.json()["id"]

        dup_payload = {
            "scenario_name": "Simulacion Escenario Optimista",
            "modified_prior_a": "0.350000",
            "modified_likelihood_b_given_a": "0.450000"
        }
        dup_res = await client.post(f"/api/v1/probability/analyses/{id_1}/duplicate-scenario", json=dup_payload, headers=auth_headers_a)
        assert dup_res.status_code == 200
        dup_data = dup_res.json()
        assert dup_data["is_simulation"] is True
        assert dup_data["scenario_type"] == "simulation"
        assert dup_data["simulation_label"] == "Simulacion hipotetica"
        id_2 = dup_data["id"]

        comp_res = await client.post(
            "/api/v1/probability/scenarios/compare",
            json={"analysis_id_1": id_1, "analysis_id_2": id_2},
            headers=auth_headers_a
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["comparison"]["scenario_1_is_simulation"] is False
        assert comp_data["comparison"]["scenario_2_is_simulation"] is True


@pytest.mark.asyncio
async def test_api_075_and_076_auth_validation_cross_company(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth_events = await client.post(
            "/api/v1/probability/events",
            json={"sample_space_size": 100, "event_a_count": 10, "event_b_count": 10, "intersection_count": 5}
        )
        assert unauth_events.status_code == 401

        unauth_bayes = await client.post(
            "/api/v1/probability/bayes",
            json={"prior_a": "0.20", "likelihood_b_given_a": "0.50", "likelihood_b_given_not_a": "0.10"}
        )
        assert unauth_bayes.status_code == 401

        dataset_id_a = uuid4()
        with sync_session_factory() as session:
            session.add(AnalyticsArtifact(
                id=dataset_id_a,
                company_id=COMPANY_A_ID,
                kind="dataset",
                artifact_key=str(dataset_id_a),
                version=1,
                status="active",
                data_json=json.dumps({"rows": [], "grain": "lines"}),
                created_by=USER_A_ID
            ))
            session.commit()

        cross_events = await client.post(
            "/api/v1/probability/events",
            json={"dataset_id": str(dataset_id_a), "sample_space_size": 10, "event_a_count": 1, "event_b_count": 1, "intersection_count": 1},
            headers=auth_headers_b
        )
        assert cross_events.status_code == 404

        cross_bayes = await client.post(
            "/api/v1/probability/bayes",
            json={"dataset_id": str(dataset_id_a), "prior_a": "0.2", "likelihood_b_given_a": "0.4", "likelihood_b_given_not_a": "0.1"},
            headers=auth_headers_b
        )
        assert cross_bayes.status_code == 404


@pytest.mark.asyncio
async def test_fal_026_semana_08_hypothesis_testing(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "count_1": 65,
            "total_1": 100,
            "count_2": 45,
            "total_2": 100,
            "confidence_level": "0.95"
        }
        res = await client.post("/api/v1/probability/hypothesis-test", json=payload, headers=auth_headers_a)
        assert res.status_code == 200
        data = res.json()
        assert data["test_type"] == "two_proportions_z_test"
        assert Decimal(data["p_value"]) < Decimal("0.05")
        assert "p-valor" in data["didactic_explanation"].lower()
        assert "no representa la probabilidad de que la hipotesis" in data["didactic_explanation"].lower()
        assert data["assumptions_met"] is True
        assert data["expected_value_group_1"] == "65"
        assert data["expected_value_group_2"] == "45"
