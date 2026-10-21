from decimal import ROUND_HALF_EVEN, Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.probabilidad_bayes import (
    BayesCalculationRequest,
    SmoothedBayesRequest,
)
from salesia.modules.analitica.domain.probability import calculate_empirical_bayes_full, validate_manual_bayes_inputs
from salesia.modules.analitica.domain.statistics import calculate_bayes_full, calculate_smoothed_bayes
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException, ZeroEvidenceException


def post_probability_bayes(
    payload: BayesCalculationRequest, current_user: AuthenticatedUser = None, db: Session = None
):
    if payload.dataset_id:
        ds = db.scalar(
            select(AnalyticsArtifact).where(
                AnalyticsArtifact.id == payload.dataset_id, AnalyticsArtifact.kind == "dataset"
            )
        )

        if not ds or ds.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset no encontrado o no pertenece a la empresa"
            )

    if (
        payload.sample_space_size is not None
        and payload.event_a_count is not None
        and payload.event_b_count is not None
        and payload.intersection_count is not None
    ):
        try:
            return calculate_empirical_bayes_full(
                sample_space_size=payload.sample_space_size,
                event_a_count=payload.event_a_count,
                event_b_count=payload.event_b_count,
                intersection_count=payload.intersection_count,
                smoothing_enabled=payload.smoothing_enabled,
                alpha=payload.alpha,
                min_support_threshold=payload.min_support_threshold,
            )

        except (ZeroEvidenceException, InvariantViolationException, EmptySampleException) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    if payload.prior_a is None or payload.likelihood_b_given_a is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere prior_a y likelihood_b_given_a o conteos muestrales",
        )

    try:
        if payload.evidence_b is not None:
            norm_prior, norm_lik_a, norm_ev = validate_manual_bayes_inputs(
                prior_a=payload.prior_a,
                likelihood_b_given_a=payload.likelihood_b_given_a,
                evidence_b=payload.evidence_b,
                mode=payload.mode,
            )

            posterior = ((norm_lik_a * norm_prior) / norm_ev).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

            norm_lik_not_a = Decimal("0.000000")

            if (Decimal("1") - norm_prior) > Decimal("0"):
                raw_not_a = (norm_ev - (norm_lik_a * norm_prior)) / (Decimal("1") - norm_prior)

                norm_lik_not_a = max(Decimal("0"), min(Decimal("1"), raw_not_a)).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                )

            rounded_post = posterior.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

            rounded_ev = norm_ev.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        else:
            if payload.likelihood_b_given_not_a is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe proporcionar evidence_b o likelihood_b_given_not_a",
                )

            p_a = payload.prior_a

            l_a = payload.likelihood_b_given_a

            l_not_a = payload.likelihood_b_given_not_a

            if payload.mode == "percentage":
                if not (
                    Decimal("0") <= p_a <= Decimal("100")
                    and Decimal("0") <= l_a <= Decimal("100")
                    and Decimal("0") <= l_not_a <= Decimal("100")
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="En modo porcentaje, los valores deben estar entre 0 y 100",
                    )

                p_a = p_a / Decimal("100")

                l_a = l_a / Decimal("100")

                l_not_a = l_not_a / Decimal("100")

            else:
                if p_a > Decimal("1") or l_a > Decimal("1") or l_not_a > Decimal("1"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="En modo proporcion, los valores deben estar en [0, 1]. Si ingreso valores porcentuales, active modo porcentaje explicitamente",
                    )

            res = calculate_bayes_full(prior_a=p_a, likelihood_b_given_a=l_a, likelihood_b_given_not_a=l_not_a)

            norm_prior = res.prior_a

            norm_lik_a = res.likelihood_b_given_a

            norm_lik_not_a = res.likelihood_b_given_not_a

            rounded_ev = res.evidence_b

            rounded_post = res.posterior_a_given_b

        formula_cards = [
            {"term": "P(A)", "label": "Prior", "value": str(norm_prior), "formula": "P(A)"},
            {"term": "P(B|A)", "label": "Verosimilitud", "value": str(norm_lik_a), "formula": "P(B|A)"},
            {
                "term": "P(B|~A)",
                "label": "Verosimilitud complementaria",
                "value": str(norm_lik_not_a),
                "formula": "P(B|~A)",
            },
            {"term": "P(B)", "label": "Evidencia", "value": str(rounded_ev), "formula": "P(B)"},
            {"term": "P(A|B)", "label": "Posterior", "value": str(rounded_post), "formula": "P(B|A) × P(A) / P(B)"},
        ]

        return {
            "mode": payload.mode,
            "prior_a": str(norm_prior),
            "likelihood_b_given_a": str(norm_lik_a),
            "likelihood_b_given_not_a": str(norm_lik_not_a),
            "evidence_b": str(rounded_ev),
            "posterior_a_given_b": str(rounded_post),
            "formula_cards": formula_cards,
            "interpretation": f"La probabilidad posterior P(A|B) calculada es de {rounded_post}",
            "causality_disclaimer": "Asociacion condicional calculada formalmente. No representa causalidad automatica",
        }

    except (ZeroEvidenceException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


def post_smoothed_bayes(payload: SmoothedBayesRequest):
    return calculate_smoothed_bayes(
        count_a_and_b=payload.count_a_and_b,
        count_not_a_and_b=payload.count_not_a_and_b,
        total_a=payload.total_a,
        total_not_a=payload.total_not_a,
        prior_a=payload.prior_a,
        alpha=payload.alpha,
    )
