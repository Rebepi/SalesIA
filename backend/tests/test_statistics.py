from decimal import Decimal
import pytest
from salesia.modules.analitica.domain.statistics import (
    calculate_mean,
    calculate_median,
    compute_statistical_summary,
    calculate_bayes,
    calculate_bayes_full
)
from salesia.shared.domain.exceptions import (
    EmptySampleException,
    ZeroEvidenceException,
    InvariantViolationException
)


def test_calculate_mean_basic():
    values = [Decimal("10"), Decimal("20"), Decimal("30")]
    result = calculate_mean(values)
    assert result == Decimal("20.000000")


def test_calculate_mean_empty():
    with pytest.raises(EmptySampleException):
        calculate_mean([])


def test_calculate_median_odd_count():
    values = [Decimal("5"), Decimal("1"), Decimal("9")]
    result = calculate_median(values)
    assert result == Decimal("5.000000")


def test_calculate_median_even_count():
    values = [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40")]
    result = calculate_median(values)
    assert result == Decimal("25.000000")


def test_calculate_median_empty():
    with pytest.raises(EmptySampleException):
        calculate_median([])


def test_compute_statistical_summary_skewness():
    values = [Decimal("10"), Decimal("10"), Decimal("10"), Decimal("90")]
    summary = compute_statistical_summary(values)
    assert summary.count == 4
    assert summary.mean == Decimal("30.000000")
    assert summary.median == Decimal("10.000000")
    assert summary.skewness_direction == "sesgo_positivo_derecha"
    assert summary.sum_total == Decimal("120")


def test_bayes_formula_valid():
    prior = Decimal("0.3")
    likelihood = Decimal("0.8")
    evidence = Decimal("0.4")
    res = calculate_bayes(prior, likelihood, evidence)
    assert res == Decimal("0.600000")


def test_bayes_zero_evidence():
    prior = Decimal("0.3")
    likelihood = Decimal("0.8")
    evidence = Decimal("0")
    with pytest.raises(ZeroEvidenceException):
        calculate_bayes(prior, likelihood, evidence)


def test_bayes_out_of_bounds():
    with pytest.raises(InvariantViolationException):
        calculate_bayes(Decimal("1.5"), Decimal("0.5"), Decimal("0.5"))


def test_bayes_full_calculation():
    prior_a = Decimal("0.2")
    likelihood_given_a = Decimal("0.8")
    likelihood_given_not_a = Decimal("0.1")

    res = calculate_bayes_full(
        prior_a=prior_a,
        likelihood_b_given_a=likelihood_given_a,
        likelihood_b_given_not_a=likelihood_given_not_a
    )

    assert res.prior_a == Decimal("0.2")
    assert res.evidence_b == Decimal("0.240000")
    assert res.posterior_a_given_b == Decimal("0.666667")
    assert "incrementa la probabilidad" in res.interpretation
