import math
import statistics as py_stats
from decimal import Decimal
from datetime import datetime, timezone, timedelta
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
    SaleLineModel,
    ProductModel
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.shared.domain.exceptions import (
    EmptySampleException,
    InvariantViolationException,
    ZeroEvidenceException
)
from salesia.modules.analitica.domain.statistics import (
    calculate_mean,
    calculate_variance,
    calculate_stdev
)
from salesia.modules.analitica.domain.advanced import (
    calculate_variance_detailed,
    calculate_stdev_detailed,
    verify_numerical_stability,
    calculate_mathematical_expectation,
    evaluate_distribution_fit,
    calculate_confidence_interval_detailed,
    preregister_hypothesis,
    run_two_groups_test_detailed,
    calculate_effect_size_detailed,
    adjust_multiple_comparisons_detailed,
    execute_reproducible_sampling,
    evaluate_ab_experiment,
    analyze_time_series_split,
    forecast_demand_censored_detailed,
    detect_anomalies_detailed,
    register_statistical_model,
    get_model_history,
    verify_model_reproducibility,
    monitor_model_drift_and_health
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A_ID = UUID("00000000-0000-0000-0000-000000000301")
BRANCH_A_ID = UUID("00000000-0000-0000-0000-000000000302")
USER_A_ID = UUID("00000000-0000-0000-0000-000000000303")

COMPANY_B_ID = UUID("00000000-0000-0000-0000-000000000309")
BRANCH_B_ID = UUID("00000000-0000-0000-0000-000000000392")
USER_B_ID = UUID("00000000-0000-0000-0000-000000000308")


@pytest.fixture(autouse=True, scope="module")
def setup_adv_part22_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [
            (COMPANY_A_ID, "20999000301", "Empresa Alpha ADV"),
            (COMPANY_B_ID, "20999000309", "Empresa Beta ADV")
        ]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(
                    id=cid,
                    tax_id=tax,
                    legal_name=name,
                    trade_name=name,
                    base_currency="USD",
                    is_active=True
                ))
        session.flush()
        for bid, cid, code in [
            (BRANCH_A_ID, COMPANY_A_ID, "SUC-A-ADV"),
            (BRANCH_B_ID, COMPANY_B_ID, "SUC-B-ADV")
        ]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(
                    id=bid,
                    company_id=cid,
                    code=code,
                    name=f"Sucursal {code}",
                    timezone="America/Lima",
                    is_active=True
                ))
        session.commit()
    yield


@pytest.fixture
def auth_adv_headers_a():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            role="company_admin",
            email="admin_a_adv@salesia.enterprise"
        )
        return identity["headers"]


@pytest.fixture
def auth_adv_headers_b():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_B_ID,
            user_id=USER_B_ID,
            role="company_admin",
            email="admin_b_adv@salesia.enterprise"
        )
        return identity["headers"]


def test_adv_001_variance_population_and_sample():
    with pytest.raises(EmptySampleException):
        calculate_variance([], is_sample=True)

    with pytest.raises(EmptySampleException):
        calculate_variance([], is_sample=False)

    with pytest.raises(InvariantViolationException):
        calculate_variance([Decimal("100.00")], is_sample=True)

    pop_one = calculate_variance([Decimal("100.00")], is_sample=False)
    assert pop_one == Decimal("0.000000")

    vals = [Decimal("10.00"), Decimal("20.00"), Decimal("30.00")]
    sample_det = calculate_variance_detailed(vals, is_sample=True, variable_unit="USD")
    assert sample_det["estimator"] == "sample"
    assert sample_det["denominator"] == 2
    assert sample_det["formula"] == "sum((x_i - mean)^2) / (n - 1)"
    assert sample_det["units"] == "USD al cuadrado"
    assert sample_det["variance"] == Decimal("100.000000")

    pop_det = calculate_variance_detailed(vals, is_sample=False, variable_unit="USD")
    assert pop_det["estimator"] == "population"
    assert pop_det["denominator"] == 3
    assert pop_det["formula"] == "sum((x_i - mean)^2) / n"
    assert pop_det["units"] == "USD al cuadrado"
    assert pop_det["variance"] == Decimal("66.666667")


def test_adv_002_standard_deviation():
    fixture_vals = [
        Decimal("2"), Decimal("4"), Decimal("4"), Decimal("4"),
        Decimal("5"), Decimal("5"), Decimal("7"), Decimal("9")
    ]
    stdev_pop = calculate_stdev(fixture_vals, is_sample=False)
    assert stdev_pop == Decimal("2.000000")

    pop_det = calculate_stdev_detailed(fixture_vals, is_sample=False, variable_unit="unidades")
    assert pop_det["standard_deviation"] == Decimal("2.000000")
    assert pop_det["units"] == "unidades"
    assert pop_det["estimator"] == "population"

    sample_det = calculate_stdev_detailed(fixture_vals, is_sample=True, variable_unit="unidades")
    assert sample_det["estimator"] == "sample"
    assert sample_det["standard_deviation"] > Decimal("2.000000")


def test_adv_003_numerical_stability():
    large_vals = [
        Decimal("1000000000.1"),
        Decimal("1000000000.2"),
        Decimal("1000000000.3")
    ]
    var_res = calculate_variance(large_vals, is_sample=True)
    assert var_res == Decimal("0.010000")
    assert var_res > Decimal("0")

    oracle_var = py_stats.variance([float(x) for x in large_vals])
    assert abs(float(var_res) - oracle_var) < 1e-6

    stab_report = verify_numerical_stability(large_vals)
    assert stab_report["is_stable"] is True
    assert stab_report["catastrophic_cancellation_prevented"] is True
    assert Decimal(str(stab_report["variance"])) == Decimal("0.010000")


def test_adv_004_mathematical_expectation():
    vals = [Decimal("0"), Decimal("1"), Decimal("2")]
    probs = [Decimal("0.25"), Decimal("0.50"), Decimal("0.25")]
    exp_res = calculate_mathematical_expectation(vals, probs)
    assert exp_res["expected_value"] == Decimal("1.000000")
    assert exp_res["valid_probabilities"] is True
    assert exp_res["probabilities_sum"] == Decimal("1.000000")

    with pytest.raises(InvariantViolationException):
        calculate_mathematical_expectation(vals, [Decimal("0.20"), Decimal("0.50"), Decimal("0.20")])

    with pytest.raises(InvariantViolationException):
        calculate_mathematical_expectation(vals, [Decimal("-0.10"), Decimal("0.60"), Decimal("0.50")])

    with pytest.raises(InvariantViolationException):
        calculate_mathematical_expectation([Decimal("1")], [Decimal("0.5"), Decimal("0.5")])


def test_adv_005_theoretical_distributions():
    skewed_data = [Decimal("1")] * 80 + [Decimal("100")] * 5 + [Decimal("500")] * 1
    fit_res = evaluate_distribution_fit(skewed_data, candidate_family="normal")
    assert fit_res["has_mean"] is True
    assert fit_res["assumed_normal_by_default"] is False
    assert fit_res["normality_rejected"] is True
    assert "no se asume normalidad solo porque exista una media" in fit_res["didactic_warning"].lower()
    assert fit_res["distribution_family"] in ("asymmetric_empirical", "lognormal_or_pareto", "empirical_non_normal")


def test_adv_006_confidence_intervals():
    vals = [Decimal(str(x)) for x in [10, 12, 14, 15, 16, 18, 20, 22, 24, 25]]
    ci = calculate_confidence_interval_detailed(vals, confidence_level=Decimal("0.95"), method="student_t")
    assert ci["confidence_level"] == Decimal("0.95")
    assert ci["point_estimate"] == Decimal("17.600000")
    assert ci["lower_bound"] < ci["point_estimate"] < ci["upper_bound"]
    assert "no interpretar como probabilidad posterior" in ci["didactic_disclaimer"].lower()
    assert ci["method"] == "student_t"


def test_adv_007_hypothesis_definition_preregistration():
    hypo = preregister_hypothesis(
        hypothesis_id="HYP-001",
        h0="La promocion no incrementa el ticket promedio",
        h1="La promocion incrementa el ticket promedio",
        variable="ticket_total",
        group_a="sin_promocion",
        group_b="con_promocion",
        direction="greater",
        alpha=Decimal("0.05"),
        test_type="welch_t"
    )
    assert hypo["preregistered"] is True
    assert hypo["direction"] == "greater"
    assert hypo["is_confirmatory"] is True
    assert "post_hoc" not in hypo["status"]

    with pytest.raises(InvariantViolationException):
        preregister_hypothesis(
            hypothesis_id="HYP-BAD",
            h0="H0",
            h1="H1",
            variable="x",
            group_a="A",
            group_b="B",
            direction="invalid_direction"
        )


def test_adv_008_group_testing_welch_paired():
    group_a = [Decimal(str(x)) for x in [10, 11, 12, 13, 14]]
    group_b = [Decimal(str(x)) for x in [20, 22, 24, 26, 28]]
    welch_res = run_two_groups_test_detailed(group_a, group_b, paired=False)
    assert welch_res["test_name"] in ("welch_t_test", "student_t_test")
    assert welch_res["degrees_of_freedom"] is not None
    assert welch_res["p_value"] < Decimal("0.05")

    with pytest.raises(InvariantViolationException):
        run_two_groups_test_detailed(group_a, group_b[:3], paired=True)

    paired_res = run_two_groups_test_detailed(group_a, group_b, paired=True)
    assert paired_res["is_paired"] is True
    assert paired_res["test_name"] == "paired_t_test"


def test_adv_009_p_value_and_degrees_of_freedom():
    group_a = [Decimal(str(x)) for x in [100, 102, 104, 106, 108]]
    group_b = [Decimal(str(x)) for x in [110, 112, 114, 116, 118]]
    res = run_two_groups_test_detailed(group_a, group_b, paired=False)
    assert "statistic" in res
    assert "degrees_of_freedom" in res
    assert "validity_conditions" in res
    assert "no es la probabilidad de que h0 sea verdadera" in res["didactic_p_value_explanation"].lower()


def test_adv_010_effect_size_and_cohens_d():
    g1_big = [Decimal("100.00")] * 5000
    g2_big = [Decimal("100.02")] * 5000
    eff = calculate_effect_size_detailed(g1_big, g2_big)
    assert eff["cohens_d"] < Decimal("0.20")
    assert eff["magnitude"] == "negligible"
    assert eff["is_commercially_meaningful"] is False
    assert "efecto minúsculo" in eff["interpretation"].lower() or "magnitud despreciable" in eff["interpretation"].lower()


def test_adv_011_multiple_comparisons_adjustment():
    raw_tests = [
        {"segment": "cat_a", "p_value": Decimal("0.01")},
        {"segment": "cat_b", "p_value": Decimal("0.04")},
        {"segment": "cat_c", "p_value": Decimal("0.045")},
        {"segment": "cat_d", "p_value": Decimal("0.15")},
        {"segment": "cat_e", "p_value": Decimal("0.30")}
    ]
    adj = adjust_multiple_comparisons_detailed(raw_tests, method="bonferroni", alpha=Decimal("0.05"))
    assert adj["total_comparisons"] == 5
    assert adj["adjusted_alpha"] == Decimal("0.010000")
    assert adj["fwer_unadjusted"] > Decimal("0.20")
    results = adj["results"]
    assert results[0]["significant_after_adjustment"] is True
    assert results[1]["significant_after_adjustment"] is False


def test_adv_012_sampling_reproducibility():
    rows = [{"id": i, "val": i * 10} for i in range(100)]
    s1 = execute_reproducible_sampling(rows, size=15, seed=777)
    s2 = execute_reproducible_sampling(rows, size=15, seed=777)
    assert s1["sample_indices"] == s2["sample_indices"]
    assert s1["sample_rows"] == s2["sample_rows"]
    assert s1["seed"] == 777
    assert s1["universe_size"] == 100
    assert len(s1["sample_rows"]) == 15

    s3 = execute_reproducible_sampling(rows, size=15, seed=999)
    assert s1["sample_indices"] != s3["sample_indices"]


def test_adv_013_ab_testing_framework():
    events = [
        {"user_id": "u1", "variant": "A", "exposed": True, "converted": 1},
        {"user_id": "u1", "variant": "A", "exposed": True, "converted": 0},
        {"user_id": "u2", "variant": "A", "exposed": True, "converted": 0},
        {"user_id": "u3", "variant": "B", "exposed": True, "converted": 1},
        {"user_id": "u4", "variant": "B", "exposed": True, "converted": 1},
        {"user_id": "u5", "variant": "B", "exposed": False, "converted": 0}
    ]
    ab_res = evaluate_ab_experiment(events, is_randomized=True)
    assert ab_res["is_randomized_experiment"] is True
    assert ab_res["deduplicated_users_count"] == 4
    assert ab_res["unexposed_excluded_count"] == 1
    assert "srm_test" in ab_res

    obs_res = evaluate_ab_experiment(events, is_randomized=False)
    assert obs_res["is_randomized_experiment"] is False
    assert "observacional" in obs_res["method_type"].lower()
    assert "confusion" in obs_res["causality_disclaimer"].lower() or "asociacion" in obs_res["causality_disclaimer"].lower()


def test_adv_014_time_series_temporal_split():
    base_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ts_data = []
    for i in range(30):
        ts_data.append({
            "timestamp": (base_dt + timedelta(days=i)).isoformat(),
            "value": 100 + i * 2 + (i % 7) * 5
        })
    ts_res = analyze_time_series_split(ts_data, date_column="timestamp", value_column="value", train_ratio=0.8)
    assert ts_res["future_data_leakage_prevented"] is True
    assert ts_res["train_max_date"] < ts_res["test_min_date"]
    assert "naive_baseline_mae" in ts_res
    assert "trend_slope" in ts_res
    assert "seasonality" in ts_res


def test_adv_015_demand_forecast_stockout_censoring():
    records = [
        {"date": "2026-01-01", "sales": 10, "stock": 50},
        {"date": "2026-01-02", "sales": 12, "stock": 38},
        {"date": "2026-01-03", "sales": 0, "stock": 0},
        {"date": "2026-01-04", "sales": 0, "stock": 0},
        {"date": "2026-01-05", "sales": 15, "stock": 40}
    ]
    fc = forecast_demand_censored_detailed(records, horizon=3)
    assert fc["censored_days_count"] == 2
    assert fc["censored_zero_sales_treated_as_censored"] is True
    assert len(fc["forecast_intervals"]) == 3
    assert "naive_baseline_comparison" in fc
    assert fc["forecast_intervals"][0]["lower"] <= fc["forecast_intervals"][0]["point"] <= fc["forecast_intervals"][0]["upper"]


def test_adv_016_anomaly_detection_signals():
    recs = [
        {"ticket_id": f"T-{i}", "amount": 50.0 + i, "items": 2} for i in range(50)
    ]
    recs.append({"ticket_id": "T-ANOMALY", "amount": 9500.0, "items": 50})
    anom = detect_anomalies_detailed(recs, feature_columns=["amount", "items"])
    assert anom["anomalies_count"] >= 1
    found = [a for a in anom["anomalies"] if a["ticket_id"] == "T-ANOMALY"]
    assert len(found) == 1
    assert found[0]["classification"] == "señal_a_revisar"
    assert "fraude probado" not in found[0]["classification"].lower()
    assert "influential_features" in found[0]


def test_adv_017_model_registry_versioning(auth_adv_headers_a):
    m_name = f"forecast_demand_{uuid4().hex[:6]}"
    with sync_session_factory() as session:
        m1 = register_statistical_model(
            db=session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            name=m_name,
            algorithm="holt_winters_exponential_smoothing",
            hyperparameters={"alpha": 0.2, "beta": 0.1, "gamma": 0.3},
            feature_names=["sales_lag1", "day_of_week"],
            dataset_id=uuid4(),
            dataset_version=1,
            dataset_hash="hash_dataset_abc123",
            seed=42,
            evaluation_metrics={"mae": 12.5, "rmse": 15.2}
        )
        assert m1["version"] == 1
        assert m1["reproducibility_declared"] is True

        m2 = register_statistical_model(
            db=session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            name=m_name,
            algorithm="arima_with_seasonality",
            hyperparameters={"p": 1, "d": 1, "q": 1},
            feature_names=["sales_lag1", "sales_lag7"],
            dataset_id=uuid4(),
            dataset_version=2,
            dataset_hash="hash_dataset_def456",
            seed=42,
            evaluation_metrics={"mae": 9.8, "rmse": 12.1},
            previous_version_id=UUID(m1["id"])
        )
        assert m2["version"] == 2
        assert m2["previous_version_id"] == m1["id"]

        history = get_model_history(session, COMPANY_A_ID, m_name)
        assert len(history) == 2
        assert history[0]["version"] == 2
        assert history[1]["version"] == 1

        rep = verify_model_reproducibility(session, COMPANY_A_ID, UUID(m1["id"]))
        assert rep["reproducible"] is True
        assert rep["dataset_hash"] == "hash_dataset_abc123"


def test_adv_018_model_monitoring_and_drift_fallback():
    train_dist = [10.0 + i for i in range(100)]
    inference_normal = [10.5 + i for i in range(100)]
    healthy_res = monitor_model_drift_and_health(
        training_distribution=train_dist,
        current_distribution=inference_normal,
        error_metric_baseline=10.0,
        current_error_metric=10.5
    )
    assert healthy_res["status"] == "healthy"
    assert healthy_res["fallback_triggered"] is False

    inference_drifted = [80.0 + i * 3 for i in range(100)]
    degraded_res = monitor_model_drift_and_health(
        training_distribution=train_dist,
        current_distribution=inference_drifted,
        error_metric_baseline=10.0,
        current_error_metric=35.0
    )
    assert degraded_res["status"] in ("degraded", "retired")
    assert degraded_res["fallback_triggered"] is True
    assert "baseline_fallback" in degraded_res["active_policy"]
    assert "no sigue recomendando decisiones" in degraded_res["governance_action"].lower()


@pytest.mark.asyncio
async def test_adv_api_endpoints_complete(auth_adv_headers_a, auth_adv_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_v = await client.post(
            "/api/v1/statistics/variance",
            headers=auth_adv_headers_a,
            json={"values": ["10.00", "20.00", "30.00"], "is_sample": True}
        )
        assert res_v.status_code == 200
        assert res_v.json()["variance"] == "100.000000"

        res_v_one = await client.post(
            "/api/v1/statistics/variance",
            headers=auth_adv_headers_a,
            json={"values": ["10.00"], "is_sample": True}
        )
        assert res_v_one.status_code in (400, 422)

        res_sd = await client.post(
            "/api/v1/statistics/stdev",
            headers=auth_adv_headers_a,
            json={"values": ["2", "4", "4", "4", "5", "5", "7", "9"], "is_sample": False}
        )
        assert res_sd.status_code == 200
        assert res_sd.json()["standard_deviation"] == "2.000000"

        res_stab = await client.post(
            "/api/v1/statistics/numerical-stability",
            headers=auth_adv_headers_a,
            json={"values": ["1000000000.1", "1000000000.2", "1000000000.3"]}
        )
        assert res_stab.status_code == 200
        assert res_stab.json()["is_stable"] is True

        res_exp = await client.post(
            "/api/v1/statistics/mathematical-expectation",
            headers=auth_adv_headers_a,
            json={
                "values": ["0", "1", "2"],
                "probabilities": ["0.25", "0.50", "0.25"]
            }
        )
        assert res_exp.status_code == 200
        assert res_exp.json()["expected_value"] == "1.000000"

        res_hypo = await client.post(
            "/api/v1/probability/preregister-hypothesis",
            headers=auth_adv_headers_a,
            json={
                "hypothesis_id": "API-HYP-1",
                "h0": "Sin cambio",
                "h1": "Mayor ticket",
                "variable": "ticket",
                "group_a": "A",
                "group_b": "B",
                "direction": "greater"
            }
        )
        assert res_hypo.status_code == 200
        assert res_hypo.json()["preregistered"] is True

        res_grp = await client.post(
            "/api/v1/statistics/groups-test",
            headers=auth_adv_headers_a,
            json={
                "group_a": ["10", "11", "12", "13", "14"],
                "group_b": ["20", "22", "24", "26", "28"],
                "paired": False
            }
        )
        assert res_grp.status_code == 200
        assert res_grp.json()["degrees_of_freedom"] is not None

        res_eff = await client.post(
            "/api/v1/statistics/effect-size",
            headers=auth_adv_headers_a,
            json={
                "group_a": ["10", "12", "14"],
                "group_b": ["20", "22", "24"]
            }
        )
        assert res_eff.status_code == 200
        assert res_eff.json()["magnitude"] in ("large", "medium", "small", "negligible")

        res_mc = await client.post(
            "/api/v1/statistics/multiple-comparisons",
            headers=auth_adv_headers_a,
            json={
                "p_values": [
                    {"segment": "s1", "p_value": "0.01"},
                    {"segment": "s2", "p_value": "0.04"}
                ],
                "method": "bonferroni"
            }
        )
        assert res_mc.status_code == 200
        assert res_mc.json()["adjusted_alpha"] == "0.025000"

        res_sample = await client.post(
            "/api/v1/datasets/sample",
            headers=auth_adv_headers_a,
            json={
                "rows": [{"id": 1, "val": 10}, {"id": 2, "val": 20}, {"id": 3, "val": 30}],
                "size": 2,
                "seed": 123
            }
        )
        assert res_sample.status_code == 200
        assert len(res_sample.json()["sample_rows"]) == 2

        res_ab = await client.post(
            "/api/v1/experiments/ab-test",
            headers=auth_adv_headers_a,
            json={
                "events": [
                    {"user_id": "1", "variant": "A", "exposed": True, "converted": 1},
                    {"user_id": "2", "variant": "B", "exposed": True, "converted": 0}
                ]
            }
        )
        assert res_ab.status_code == 200
        assert res_ab.json()["is_randomized_experiment"] is True

        res_ts = await client.post(
            "/api/v1/analytics/time-series",
            headers=auth_adv_headers_a,
            json={
                "records": [
                    {"date": "2026-01-01", "value": 100},
                    {"date": "2026-01-02", "value": 110},
                    {"date": "2026-01-03", "value": 105},
                    {"date": "2026-01-04", "value": 120}
                ],
                "date_column": "date",
                "value_column": "value",
                "train_ratio": 0.75
            }
        )
        assert res_ts.status_code == 200
        assert res_ts.json()["future_data_leakage_prevented"] is True

        res_df = await client.post(
            "/api/v1/analytics/demand-forecast",
            headers=auth_adv_headers_a,
            json={
                "records": [
                    {"date": "2026-01-01", "sales": 10, "stock": 20},
                    {"date": "2026-01-02", "sales": 0, "stock": 0},
                    {"date": "2026-01-03", "sales": 12, "stock": 15}
                ],
                "horizon": 2
            }
        )
        assert res_df.status_code == 200
        assert res_df.json()["censored_zero_sales_treated_as_censored"] is True

        anomaly_recs = [{"id": i, "monto": 10.0 + i} for i in range(15)]
        anomaly_recs.append({"id": 99, "monto": 999.0})
        res_anom = await client.post(
            "/api/v1/analytics/anomaly-detection",
            headers=auth_adv_headers_a,
            json={
                "records": anomaly_recs,
                "feature_columns": ["monto"]
            }
        )
        assert res_anom.status_code == 200
        assert res_anom.json()["anomalies_count"] >= 1

        res_m_post = await client.post(
            "/api/v1/analytics/models",
            headers=auth_adv_headers_a,
            json={
                "name": "modelo_tickets_q4",
                "algorithm": "linear_regression",
                "hyperparameters": {"fit_intercept": True},
                "feature_names": ["items_count"],
                "dataset_id": str(uuid4()),
                "dataset_version": 1,
                "dataset_hash": "hash_xyz789",
                "seed": 42,
                "evaluation_metrics": {"r2": 0.88}
            }
        )
        assert res_m_post.status_code == 201
        model_id = res_m_post.json()["id"]

        res_m_b = await client.get(
            f"/api/v1/analytics/models/{model_id}",
            headers=auth_adv_headers_b
        )
        assert res_m_b.status_code in (404, 403)

        res_m_mon = await client.post(
            f"/api/v1/analytics/models/{model_id}/monitor",
            headers=auth_adv_headers_a,
            json={
                "training_distribution": [1.0, 2.0, 3.0, 4.0, 5.0],
                "current_distribution": [50.0, 60.0, 70.0, 80.0, 90.0],
                "error_metric_baseline": 2.0,
                "current_error_metric": 12.0
            }
        )
        assert res_m_mon.status_code == 200
        assert res_m_mon.json()["fallback_triggered"] is True


@pytest.mark.asyncio
async def test_fal_026_empirical_scenarios_and_week08_academic(auth_adv_headers_a, auth_adv_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        save_res = await client.post(
            "/api/v1/probability/analyses",
            headers=auth_adv_headers_a,
            json={
                "name": "Analisis Bayes Base FAL026",
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 120,
                "intersection_count": 60,
                "prior_a": "0.20",
                "likelihood_b_given_a": "0.30",
                "evidence_b": "0.12",
                "is_simulation": False
            }
        )
        assert save_res.status_code in (200, 201)
        analysis_1_id = save_res.json()["id"]

        cross_res = await client.get(
            f"/api/v1/probability/analyses/{analysis_1_id}",
            headers=auth_adv_headers_b
        )
        assert cross_res.status_code in (404, 403)

        dup_res = await client.post(
            f"/api/v1/probability/analyses/{analysis_1_id}/duplicate-scenario",
            headers=auth_adv_headers_a,
            json={
                "scenario_name": "Escenario Simulado Suavizado",
                "modified_prior_a": "0.25",
                "modified_alpha": "2.0",
                "smoothing_enabled": True
            }
        )
        assert dup_res.status_code in (200, 201)
        analysis_2_id = dup_res.json()["id"]

        comp_res = await client.post(
            "/api/v1/probability/scenarios/compare",
            headers=auth_adv_headers_a,
            json={
                "analysis_id_1": analysis_1_id,
                "analysis_id_2": analysis_2_id
            }
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["scenario_1"]["is_simulation"] is False
        assert comp_data["scenario_2"]["is_simulation"] is True

        zero_ev_res = await client.post(
            "/api/v1/probability/bayes",
            headers=auth_adv_headers_a,
            json={
                "sample_space_size": 1000,
                "event_a_count": 200,
                "event_b_count": 0,
                "intersection_count": 0
            }
        )
        assert zero_ev_res.status_code in (400, 422)

        hypo_res = await client.post(
            "/api/v1/probability/hypothesis-test",
            headers=auth_adv_headers_a,
            json={
                "count_1": 45,
                "total_1": 100,
                "count_2": 25,
                "total_2": 100,
                "confidence_level": "0.95"
            }
        )
        assert hypo_res.status_code == 200
        hypo_data = hypo_res.json()
        assert "no representa la probabilidad de que la hipotesis nula o alternativa sea cierta" in hypo_data["didactic_explanation"].lower()


@pytest.mark.asyncio
async def test_fal_024_dataset_persistence_and_frozen_repeat(auth_adv_headers_a, auth_adv_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        non_existent_id = str(uuid4())
        bad_ver = await client.get(
            f"/api/v1/datasets/{non_existent_id}/versions/1",
            headers=auth_adv_headers_a
        )
        assert bad_ver.status_code in (404, 403)

        ds_create = await client.post(
            "/api/v1/datasets",
            headers=auth_adv_headers_a,
            json={
                "name": "Dataset Congelado FAL024",
                "grain": "ticket",
                "source_entity": "sales"
            }
        )
        assert ds_create.status_code == 201
        ds_id = ds_create.json()["id"]

        ver_create = await client.post(
            f"/api/v1/datasets/{ds_id}/versions",
            headers=auth_adv_headers_a,
            json={}
        )
        assert ver_create.status_code == 201
        ver_info = ver_create.json()
        initial_hash = ver_info["data_hash"]
        initial_rows = ver_info["row_count"]
        version_num = ver_info["version"]

        analysis_create = await client.post(
            "/api/v1/analyses",
            headers=auth_adv_headers_a,
            json={
                "name": "Analisis Congelado FAL024",
                "dataset_id": ds_id,
                "dataset_version": version_num,
                "variable_name": "total_amount",
                "analysis_type": "summary"
            }
        )
        assert analysis_create.status_code == 201
        analysis_id = analysis_create.json()["id"]
        initial_mean = analysis_create.json()["result"]["mean"]

        repeat_res = await client.post(
            f"/api/v1/analyses/{analysis_id}/repeat",
            headers=auth_adv_headers_a,
            json={}
        )
        assert repeat_res.status_code == 200
        repeated = repeat_res.json()
        assert repeated["original_analysis_id"] == str(analysis_id)
        assert repeated["result"]["mean"] == initial_mean
        assert repeated["result"]["count"] == initial_rows

        expire_res = await client.post(
            f"/api/v1/datasets/{ds_id}/versions/{version_num}/expire",
            headers=auth_adv_headers_a,
            json={"retention_reason": "ciclo_auditoria_cerrado"}
        )
        assert expire_res.status_code == 200
        assert expire_res.json()["status"] == "expired"

