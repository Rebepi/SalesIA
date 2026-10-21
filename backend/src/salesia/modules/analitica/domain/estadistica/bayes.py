from decimal import ROUND_HALF_EVEN, Decimal

from salesia.modules.analitica.domain.estadistica.tipos import BayesResult
from salesia.shared.domain.exceptions import InvariantViolationException, ZeroEvidenceException


def calculate_bayes(prior_a: Decimal, likelihood_b_given_a: Decimal, evidence_b: Decimal) -> Decimal:
    if not (Decimal("0") <= prior_a <= Decimal("1")):
        raise InvariantViolationException("La probabilidad a priori P(A) debe estar entre 0 y 1")
    if not (Decimal("0") <= likelihood_b_given_a <= Decimal("1")):
        raise InvariantViolationException("La verosimilitud P(B|A) debe estar entre 0 y 1")
    if not (Decimal("0") <= evidence_b <= Decimal("1")):
        raise InvariantViolationException("La evidencia P(B) debe estar entre 0 y 1")
    if evidence_b == Decimal("0"):
        raise ZeroEvidenceException()

    posterior = (likelihood_b_given_a * prior_a) / evidence_b
    if posterior > Decimal("1.0000000001"):
        raise InvariantViolationException("Inconsistencia probabilística: P(A|B) supera 1")
    if posterior > Decimal("1"):
        posterior = Decimal("1")

    return posterior.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)


def calculate_bayes_full(
    prior_a: Decimal, likelihood_b_given_a: Decimal, likelihood_b_given_not_a: Decimal
) -> BayesResult:
    if not (Decimal("0") <= prior_a <= Decimal("1")):
        raise InvariantViolationException("P(A) debe estar en el intervalo [0, 1]")
    if not (Decimal("0") <= likelihood_b_given_a <= Decimal("1")):
        raise InvariantViolationException("P(B|A) debe estar en el intervalo [0, 1]")
    if not (Decimal("0") <= likelihood_b_given_not_a <= Decimal("1")):
        raise InvariantViolationException("P(B|~A) debe estar en el intervalo [0, 1]")

    prior_not_a = Decimal("1") - prior_a
    evidence_b = (likelihood_b_given_a * prior_a) + (likelihood_b_given_not_a * prior_not_a)

    if evidence_b == Decimal("0"):
        raise ZeroEvidenceException()

    posterior = (likelihood_b_given_a * prior_a) / evidence_b
    if posterior > Decimal("1"):
        posterior = Decimal("1")

    rounded_post = posterior.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    rounded_evidence = evidence_b.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if rounded_post > prior_a:
        interp = "La evidencia observada B incrementa la probabilidad del suceso A"
    elif rounded_post < prior_a:
        interp = "La evidencia observada B reduce la probabilidad del suceso A"
    else:
        interp = "La evidencia observada B es neutral respecto al suceso A"

    return BayesResult(
        prior_a=prior_a,
        likelihood_b_given_a=likelihood_b_given_a,
        likelihood_b_given_not_a=likelihood_b_given_not_a,
        evidence_b=rounded_evidence,
        posterior_a_given_b=rounded_post,
        interpretation=interp,
    )


def calculate_smoothed_bayes(
    count_a_and_b: int,
    count_not_a_and_b: int,
    total_a: int,
    total_not_a: int,
    prior_a: Decimal,
    alpha: Decimal = Decimal("1.0"),
) -> dict:
    smooth_num_a = Decimal(str(count_a_and_b)) + alpha
    smooth_den_a = Decimal(str(total_a)) + (Decimal("2.0") * alpha)
    likelihood_a = (smooth_num_a / smooth_den_a).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    smooth_num_not_a = Decimal(str(count_not_a_and_b)) + alpha
    smooth_den_not_a = Decimal(str(total_not_a)) + (Decimal("2.0") * alpha)
    likelihood_not_a = (smooth_num_not_a / smooth_den_not_a).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    prior_not_a = Decimal("1") - prior_a
    evidence = (likelihood_a * prior_a) + (likelihood_not_a * prior_not_a)
    posterior = (likelihood_a * prior_a) / evidence if evidence > 0 else Decimal("0.000000")
    if posterior > Decimal("1.0"):
        posterior = Decimal("1.0")
    rounded_post = posterior.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    return {
        "smoothed_likelihood_b_given_a": str(likelihood_a),
        "smoothed_likelihood_b_given_not_a": str(likelihood_not_a),
        "evidence_b": str(evidence.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
        "posterior_a_given_b": str(rounded_post),
        "alpha_applied": str(alpha),
    }
