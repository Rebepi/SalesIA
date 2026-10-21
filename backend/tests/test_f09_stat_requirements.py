from decimal import Decimal
import json
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from hypothesis import given, strategies as st, settings, HealthCheck
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    CustomerModel,
    SaleModel
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.analitica.domain.statistics import (
    calculate_mean,
    calculate_median,
    calculate_median_exact,
    compute_statistical_summary,
    classify_variable,
    validate_variable_scale_for_mean,
    compare_mean_median,
    analyze_extreme_values,
    calculate_frequencies,
    calculate_distribution,
    compute_descriptive_summary,
    calculate_weighted_mean,
    analyze_discrete_random_variable,
    analyze_continuous_random_variable,
    validate_universe_consistency,
    sanitize_numeric_values,
    VariableScale,
    CommercialUniverse,
    ALGORITHM_VERSION,
    DEFAULT_DECIMAL_PRECISION
)
from salesia.shared.domain.exceptions import (
    EmptySampleException,
    InvariantViolationException,
    IncompatibleVariableScaleException
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A_ID = UUID("00000000-0000-0000-0000-000000000001")
BRANCH_A_ID = UUID("00000000-0000-0000-0000-000000000002")
USER_A_ID = UUID("00000000-0000-0000-0000-000000000003")

COMPANY_B_ID = UUID("00000000-0000-0000-0000-000000000099")
BRANCH_B_ID = UUID("00000000-0000-0000-0000-000000000098")
USER_B_ID = UUID("00000000-0000-0000-0000-000000000097")


@pytest.fixture(autouse=True, scope="module")
def setup_stat_test_db():
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

        branch_a = session.execute(
            select(BranchModel).where(BranchModel.id == BRANCH_A_ID)
        ).scalar_one_or_none()
        if not branch_a:
            branch_a = BranchModel(
                id=BRANCH_A_ID,
                company_id=COMPANY_A_ID,
                code="SUC-A1",
                name="Sucursal Principal Alpha",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch_a)

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

        branch_b = session.execute(
            select(BranchModel).where(BranchModel.id == BRANCH_B_ID)
        ).scalar_one_or_none()
        if not branch_b:
            branch_b = BranchModel(
                id=BRANCH_B_ID,
                company_id=COMPANY_B_ID,
                code="SUC-B1",
                name="Sucursal Principal Beta",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch_b)

        session.commit()
    yield


@pytest.fixture
def auth_headers_company_a():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            role="company_admin",
            email="admin_a@salesia.enterprise"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_company_b():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_B_ID,
            user_id=USER_B_ID,
            role="company_admin",
            email="admin_b@salesia.enterprise"
        )
        return identity["headers"]


def test_stat_001_deterministic_python_library():
    values = [Decimal("100.50"), Decimal("200.75"), Decimal("300.25")]
    res1 = calculate_mean(values)
    res2 = calculate_mean(values)
    assert res1 == res2
    assert res1 == Decimal("200.500000")

    summary = compute_statistical_summary(values)
    assert summary.algorithm_version == ALGORITHM_VERSION
    assert summary.tolerance == str(DEFAULT_DECIMAL_PRECISION)


def test_stat_002_mean_monetary_accumulator_and_null_policies():
    monetary_values = [
        Decimal("10.500000"),
        Decimal("20.250000"),
        Decimal("30.750000"),
        Decimal("40.000000")
    ]
    mean_res = calculate_mean(monetary_values)
    assert mean_res == Decimal("25.375000")

    values_with_nulls = [Decimal("10.00"), None, Decimal("20.00"), "null", Decimal("30.00")]
    mean_skip = calculate_mean(values_with_nulls, null_policy="skip")
    assert mean_skip == Decimal("20.000000")

    mean_zero = calculate_mean(values_with_nulls, null_policy="zero")
    assert mean_zero == Decimal("12.000000")

    with pytest.raises(ValueError):
        calculate_mean(values_with_nulls, null_policy="error")


def test_stat_003_median_non_mutating_parity_and_ordering():
    original = [Decimal("40.00"), Decimal("10.00"), Decimal("30.00"), Decimal("20.00")]
    original_copy = list(original)
    med_even = calculate_median(original)
    assert original == original_copy
    assert med_even == Decimal("25.000000")

    odd_list = [Decimal("50.00"), Decimal("10.00"), Decimal("30.00")]
    assert calculate_median(odd_list) == Decimal("30.000000")

    reversed_odd = [Decimal("10.00"), Decimal("30.00"), Decimal("50.00")]
    assert calculate_median(reversed_odd) == Decimal("30.000000")

    with_repeats = [Decimal("10.00"), Decimal("20.00"), Decimal("20.00"), Decimal("30.00")]
    assert calculate_median(with_repeats) == Decimal("20.000000")


def test_stat_004_median_exact_high_precision_decimal():
    high_precision = [
        Decimal("100.000000000001"),
        Decimal("200.000000000005")
    ]
    med_exact = calculate_median_exact(high_precision)
    assert med_exact == Decimal("150.000000000003")


def test_stat_005_variable_classification_and_rejection():
    cls_channel = classify_variable("canal")
    assert cls_channel["scale"] == VariableScale.QUALITATIVE_NOMINAL.value
    assert cls_channel["is_numeric_computable"] is False

    cls_doc = classify_variable("numero_documento")
    assert cls_doc["scale"] == VariableScale.QUALITATIVE_NOMINAL.value
    assert cls_doc["is_numeric_computable"] is False

    with pytest.raises(IncompatibleVariableScaleException):
        validate_variable_scale_for_mean("canal", VariableScale.QUALITATIVE_NOMINAL)

    with pytest.raises(IncompatibleVariableScaleException):
        validate_variable_scale_for_mean("numero_documento")

    cls_total = classify_variable("total_amount")
    assert cls_total["scale"] == VariableScale.QUANTITATIVE_CONTINUOUS.value
    assert cls_total["is_numeric_computable"] is True


def test_stat_006_mean_vs_median_neutral_didactics():
    skewed_sample = [Decimal("10.00"), Decimal("10.00"), Decimal("10.00"), Decimal("90.00")]
    comp = compare_mean_median(skewed_sample)
    assert Decimal(comp["mean"]) == Decimal("30.000000")
    assert Decimal(comp["median"]) == Decimal("10.000000")
    assert Decimal(comp["absolute_difference"]) == Decimal("20.000000")
    assert Decimal(comp["relative_difference"]) == Decimal("2.000000")
    assert "no permite concluir" in comp["explanation"].lower()
    assert "causalidad" in comp["explanation"].lower()
    assert "fraude" in comp["explanation"].lower()


def test_stat_007_extreme_values_tukey_fences_comparison():
    data = [Decimal("10.00"), Decimal("11.00"), Decimal("12.00"), Decimal("10.50"), Decimal("11.50"), Decimal("150.00")]
    ext = analyze_extreme_values(data)
    assert ext["rule"] == "tukey_iqr_1.5"
    assert ext["outliers_count"] == 1
    assert "150.00" in ext["outliers"][0]
    assert ext["retains_original_dataset"] is True
    assert Decimal(ext["original_summary"]["mean"]) > Decimal("30.00")
    assert Decimal(ext["trimmed_summary"]["mean"]) < Decimal("15.00")


def test_stat_008_frequencies_sum_and_percentages():
    categories = ["tienda_fisica", "online", "online", "tienda_fisica", "tienda_fisica", "telefonico"]
    freqs = calculate_frequencies(categories)
    assert freqs["valid_count"] == 6
    assert freqs["frequencies_sum_check"] is True
    assert len(freqs["items"]) == 3

    sum_freqs = sum(item["absolute_frequency"] for item in freqs["items"])
    assert sum_freqs == 6


def test_stat_009_distributions_bins_and_accounting():
    values = [Decimal("10.00"), Decimal("20.00"), Decimal("30.00"), Decimal("40.00"), Decimal("50.00"), Decimal("60.00")]
    dist = calculate_distribution(values, num_bins=3)
    assert dist["bins_count"] == 3
    assert dist["all_observations_accounted"] is True
    assert dist["total_binned"] == 6


def test_stat_010_descriptive_summary_empty_and_categorical():
    with pytest.raises(EmptySampleException):
        compute_descriptive_summary([])

    cat_values = ["A", "B", "A", "C"]
    cat_summary = compute_descriptive_summary(cat_values, scale=VariableScale.QUALITATIVE_NOMINAL)
    assert cat_summary["sum_total"] is None
    assert cat_summary["mean"] is None
    assert cat_summary["median"] is None
    assert cat_summary["distinct_categories"] == 3


def test_stat_011_weighted_mean_methods_and_validation():
    prices = [Decimal("10.00"), Decimal("20.00")]
    units = [Decimal("5"), Decimal("15")]
    w_res = calculate_weighted_mean(prices, units, method="weighted_by_units")
    assert Decimal(w_res["weighted_mean_by_units"]) == Decimal("17.500000")
    assert Decimal(w_res["simple_average_per_sale"]) == Decimal("15.000000")

    with pytest.raises(InvariantViolationException):
        calculate_weighted_mean([Decimal("10.00")], [Decimal("-1.00")])

    with pytest.raises(InvariantViolationException):
        calculate_weighted_mean([Decimal("10.00")], [Decimal("0.00")])


def test_stat_012_discrete_random_variable_support_and_mass():
    observations = [0, 0, 1, 2, 2, 2, 3]
    var_res = analyze_discrete_random_variable(observations)
    assert "0" in var_res["support"]
    assert var_res["mass_is_unitary"] is True
    total_mass = Decimal(var_res["total_probability_mass"])
    assert abs(total_mass - Decimal("1.000000")) <= Decimal("0.000010")


def test_stat_013_continuous_random_variable_density():
    observations = [Decimal("10.5"), Decimal("11.2"), Decimal("12.8"), Decimal("14.0"), Decimal("15.5")]
    cont_res = analyze_continuous_random_variable(observations, num_bins=2)
    assert cont_res["estimation_method"] == "histogram_density_estimator"
    assert "probabilidad puntual en cualquier valor exacto es cero" in cont_res["didactic_concept"].lower()


def test_stat_014_universe_consistency():
    same_univ = validate_universe_consistency(
        CommercialUniverse.VENTA_ELEGIBLE.value,
        CommercialUniverse.VENTA_ELEGIBLE.value
    )
    assert same_univ["is_consistent"] is True
    assert same_univ["warning"] is None

    diff_univ = validate_universe_consistency(
        CommercialUniverse.VENTA_ELEGIBLE.value,
        CommercialUniverse.CLIENTE_ACTIVO.value
    )
    assert diff_univ["is_consistent"] is False
    assert diff_univ["warning"] is not None


def test_stat_015_invalid_data_sanitization_no_nan():
    raw_mixed = ["12.50", None, "nan", "inf", "25.00"]
    cleaned, null_cnt = sanitize_numeric_values(raw_mixed, null_policy="skip")
    assert len(cleaned) == 2
    assert null_cnt == 3
    assert cleaned[0] == Decimal("12.50")
    assert cleaned[1] == Decimal("25.00")

    with pytest.raises(ValueError):
        sanitize_numeric_values(["texto_invalido"])


def test_stat_017_tolerances_and_exactness():
    values = [Decimal("10.000000"), Decimal("20.000000")]
    summary = compute_statistical_summary(values)
    assert summary.tolerance == "0.000001"
    assert summary.mean == Decimal("15.000000")


def test_stat_018_didactic_explanation_reconstruction():
    values = [Decimal("10.00"), Decimal("20.00"), Decimal("30.00")]
    mean_val = calculate_mean(values)
    sum_val = sum(values)
    n = len(values)
    assert mean_val == (sum_val / Decimal(str(n))).quantize(Decimal("0.000001"))


@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(st.decimals(min_value=Decimal("1.00"), max_value=Decimal("1000.00"), places=2), min_size=2, max_size=20))
def test_fal_025_hypothesis_properties(sample):
    mean_res = calculate_mean(sample)
    min_val = min(sample)
    max_val = max(sample)
    assert min_val <= mean_res <= max_val

    median_res = calculate_median(sample)
    assert min_val <= median_res <= max_val


@pytest.mark.asyncio
async def test_api_071_post_mean_comprehensive(auth_headers_company_a, auth_headers_company_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth_res = await client.post("/api/v1/statistics/mean", json={"values": ["10", "20"]})
        assert unauth_res.status_code == 401

        empty_res = await client.post("/api/v1/statistics/mean", json={"values": []}, headers=auth_headers_company_a)
        assert empty_res.status_code in (400, 422), f"Expected 400/422 got {empty_res.status_code}: {empty_res.text}"

        nominal_res = await client.post(
            "/api/v1/statistics/mean",
            json={"values": ["100", "200"], "variable_name": "canal"},
            headers=auth_headers_company_a
        )
        assert nominal_res.status_code == 400
        assert "canal y número de documento" in nominal_res.json()["detail"].lower()

        succ_res = await client.post(
            "/api/v1/statistics/mean",
            json={"values": ["10.00", "20.00", "30.00"], "record_run": True},
            headers=auth_headers_company_a
        )
        assert succ_res.status_code == 200
        data = succ_res.json()
        assert data["count"] == 3
        assert Decimal(data["mean"]) == Decimal("20.000000")
        assert "execution_id" in data

        dset_create = await client.post(
            "/api/v1/datasets",
            headers=auth_headers_company_a,
            json={"name": "Dataset Para Media", "grain": "ticket"}
        )
        assert dset_create.status_code == 201
        dset_id = dset_create.json()["id"]

        ver_create = await client.post(
            f"/api/v1/datasets/{dset_id}/versions",
            headers=auth_headers_company_a,
            json={
                "row_count": 2,
                "data_hash": "sha256-test12345678",
                "schema_snapshot": {"columns": ["total_amount"]}
            }
        )
        assert ver_create.status_code == 201

        with sync_session_factory() as session:
            ver_art = session.scalar(select(AnalyticsArtifact).where(
                AnalyticsArtifact.kind == "dataset_version",
                AnalyticsArtifact.artifact_key == str(dset_id),
                AnalyticsArtifact.version == 1
            ))
            v_data = json.loads(ver_art.data_json)
            v_data["rows"] = [{"total_amount": "50.00"}, {"total_amount": "150.00"}]
            ver_art.data_json = json.dumps(v_data)
            session.commit()

        dset_mean = await client.post(
            "/api/v1/statistics/mean",
            json={"dataset_id": dset_id, "dataset_version": 1, "variable_name": "total_amount"},
            headers=auth_headers_company_a
        )
        assert dset_mean.status_code == 200
        assert Decimal(dset_mean.json()["mean"]) == Decimal("100.000000")

        cross_res = await client.post(
            "/api/v1/statistics/mean",
            json={"dataset_id": dset_id, "dataset_version": 1, "variable_name": "total_amount"},
            headers=auth_headers_company_b
        )
        assert cross_res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_072_post_median_comprehensive(auth_headers_company_a, auth_headers_company_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth_res = await client.post("/api/v1/statistics/median", json={"values": ["10", "20"]})
        assert unauth_res.status_code == 401

        succ_res = await client.post(
            "/api/v1/statistics/median",
            json={"values": ["100.0000000001", "200.0000000005"]},
            headers=auth_headers_company_a
        )
        assert succ_res.status_code == 200
        assert succ_res.json()["median"] == "150.000000"


@pytest.mark.asyncio
async def test_api_073_post_compare_comprehensive(auth_headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth_res = await client.post("/api/v1/statistics/compare", json={"values_a": ["10"], "values_b": ["20"]})
        assert unauth_res.status_code == 401

        comp_res = await client.post(
            "/api/v1/statistics/compare",
            json={
                "label_a": "Lima",
                "values_a": ["10.00", "20.00", "30.00"],
                "label_b": "Arequipa",
                "values_b": ["20.00", "40.00", "60.00"]
            },
            headers=auth_headers_company_a
        )
        assert comp_res.status_code == 200
        data = comp_res.json()
        assert data["differences"]["delta_mean"] == "20.000000"
        assert "no permite concluir" in data["explanation"].lower()


@pytest.mark.asyncio
async def test_api_074_post_random_variables_analyze_comprehensive(auth_headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth_res = await client.post(
            "/api/v1/random-variables/analyze",
            json={"name": "test", "scale": "quantitative_discrete", "observations": ["1"]}
        )
        assert unauth_res.status_code == 401

        nom_res = await client.post(
            "/api/v1/random-variables/analyze",
            json={
                "name": "canal",
                "scale": "qualitative_nominal",
                "observations": ["1", "2", "1"]
            },
            headers=auth_headers_company_a
        )
        assert nom_res.status_code == 200
        nom_data = nom_res.json()
        assert nom_data["mean"] is None
        assert nom_data["median"] is None
        assert "canal y número de documento" in nom_data["explanation"].lower()

        succ_res = await client.post(
            "/api/v1/random-variables/analyze",
            json={
                "name": "ticket_monto",
                "scale": "quantitative_continuous",
                "observations": ["50.00", "60.00", "70.00"]
            },
            headers=auth_headers_company_a
        )
        assert succ_res.status_code == 200
        assert succ_res.json()["mean"] == "60.000000"
        assert "intervalos y probabilidades puntuales" in succ_res.json()["didactic_concept"].lower()


@pytest.mark.asyncio
async def test_stat_020_cancel_analysis_leaves_no_partial_artifact(auth_headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dset_create = await client.post(
            "/api/v1/datasets",
            headers=auth_headers_company_a,
            json={"name": "Dataset Cancelacion", "grain": "ticket"}
        )
        assert dset_create.status_code == 201
        dset_id = dset_create.json()["id"]

        ver_create = await client.post(
            f"/api/v1/datasets/{dset_id}/versions",
            headers=auth_headers_company_a
        )
        assert ver_create.status_code == 201

        an_create = await client.post(
            "/api/v1/analyses",
            headers=auth_headers_company_a,
            json={"name": "Analisis A Cancelar", "dataset_id": dset_id}
        )
        assert an_create.status_code == 201
        an_id = an_create.json()["id"]

        cancel_res = await client.post(
            f"/api/v1/analyses/{an_id}/cancel",
            headers=auth_headers_company_a
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"

        get_res = await client.get(f"/api/v1/analyses/{an_id}", headers=auth_headers_company_a)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "cancelled"
        assert get_res.json()["result"] is None
