import json
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    HypothesisTestRequest,
    OperationalLiveCountsRequest,
    PreregisterHypothesisRequest,
    ProbabilityEventsRequest,
    ScenarioCompareRequest,
    TemporalLeakageValidationRequest,
)
from salesia.modules.analitica.domain.advanced import preregister_hypothesis
from salesia.modules.analitica.domain.probability import (
    calculate_empirical_probability,
    run_two_proportions_hypothesis_test,
    validate_structured_condition,
    validate_temporal_leakage,
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_probability_events(payload: ProbabilityEventsRequest, current_user: AuthenticatedUser, db: Session):
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

    if payload.event_a_definition and payload.event_a_definition.condition:
        try:
            validate_structured_condition(payload.event_a_definition.condition.model_dump())

        except InvariantViolationException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    if payload.event_b_definition and payload.event_b_definition.condition:
        try:
            validate_structured_condition(payload.event_b_definition.condition.model_dump())

        except InvariantViolationException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    if payload.predictor_fields:
        try:
            validate_temporal_leakage(
                predictor_fields=payload.predictor_fields,
                predictor_window_end=payload.predictor_window_end,
                outcome_window_start=payload.outcome_window_start,
            )

        except InvariantViolationException as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    space_size = payload.sample_space_size

    count_a = payload.event_a_count

    count_b = payload.event_b_count

    count_inter = payload.intersection_count

    if payload.dataset_id and space_size is None:
        target_version = payload.dataset_version or 1

        v_art = db.scalar(
            select(AnalyticsArtifact).where(
                AnalyticsArtifact.company_id == current_user.company_id,
                AnalyticsArtifact.kind == "dataset_version",
                AnalyticsArtifact.artifact_key == str(payload.dataset_id),
                AnalyticsArtifact.version == target_version,
            )
        )

        if not v_art:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version del dataset no encontrada")

        v_data = json.loads(v_art.data_json)

        rows = v_data.get("rows") or v_data.get("preview_sample", [])

        entity = payload.universe_definition.entity if payload.universe_definition else "sales"

        if entity == "customers":
            cust_ids = {str(r.get("customer_id")) for r in rows if r.get("customer_id")}

            space_size = len(cust_ids)

            count_a = min(space_size, count_a or 0)

            count_b = min(space_size, count_b or 0)

            count_inter = min(count_a, count_b, count_inter or 0)

        else:
            space_size = len(rows)

            count_a = min(space_size, count_a or 0)

            count_b = min(space_size, count_b or 0)

            count_inter = min(count_a, count_b, count_inter or 0)

    if space_size is None or count_a is None or count_b is None or count_inter is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe especificar los conteos de eventos y tamano del universo",
        )

    try:
        return calculate_empirical_probability(
            sample_space_size=space_size,
            event_a_count=count_a,
            event_b_count=count_b,
            intersection_count=count_inter,
            min_support_threshold=payload.min_support_threshold,
        )

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


def post_validate_temporal(payload: TemporalLeakageValidationRequest, current_user: AuthenticatedUser):
    try:
        validate_temporal_leakage(
            predictor_fields=payload.predictor_fields,
            predictor_window_end=payload.predictor_window_end,
            outcome_window_start=payload.outcome_window_start,
        )

        return {
            "valid": True,
            "message": "Evaluacion temporal correcta: no se detecto fuga temporal en las variables predictoras",
        }

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


def compare_probability_scenarios(payload: ScenarioCompareRequest, current_user: AuthenticatedUser, db: Session):
    art1 = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == payload.analysis_id_1,
            AnalyticsArtifact.kind == "probability_analysis",
            AnalyticsArtifact.company_id == current_user.company_id,
        )
    )

    art2 = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == payload.analysis_id_2,
            AnalyticsArtifact.kind == "probability_analysis",
            AnalyticsArtifact.company_id == current_user.company_id,
        )
    )

    if not art1 or not art2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o ambos analisis no fueron encontrados")

    d1 = json.loads(art1.data_json)

    d2 = json.loads(art2.data_json)

    p1_prior = Decimal(str(d1.get("probabilities", {}).get("prior_a", "0")))

    p2_prior = Decimal(str(d2.get("probabilities", {}).get("prior_a", "0")))

    p1_post = Decimal(str(d1.get("probabilities", {}).get("posterior_a_given_b", "0")))

    p2_post = Decimal(str(d2.get("probabilities", {}).get("posterior_a_given_b", "0")))

    return {
        "scenario_1": d1,
        "scenario_2": d2,
        "comparison": {
            "scenario_1_is_simulation": d1.get("is_simulation", False),
            "scenario_2_is_simulation": d2.get("is_simulation", False),
            "prior_diff": str((p2_prior - p1_prior).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
            "posterior_diff": str((p2_post - p1_post).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
        },
    }


def post_hypothesis_test(payload: HypothesisTestRequest, current_user: AuthenticatedUser):
    try:
        return run_two_proportions_hypothesis_test(
            count_1=payload.count_1,
            total_1=payload.total_1,
            count_2=payload.count_2,
            total_2=payload.total_2,
            confidence_level=payload.confidence_level,
        )

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


def post_preregister_hypothesis(payload: PreregisterHypothesisRequest):
    try:
        return preregister_hypothesis(
            hypothesis_id=payload.hypothesis_id,
            h0=payload.h0,
            h1=payload.h1,
            variable=payload.variable,
            group_a=payload.group_a,
            group_b=payload.group_b,
            direction=payload.direction,
            alpha=payload.alpha,
            test_type=payload.test_type,
        )

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def get_operational_live_counts(payload: OperationalLiveCountsRequest, current_user: AuthenticatedUser, db: Session):
    from salesia.modules.clientes.infrastructure.models import CustomerModel
    from salesia.modules.ventas.infrastructure.models import SaleModel

    now = datetime.now(tz=timezone.utc)
    period_map = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
    }
    cutoff = period_map.get(payload.period)

    if payload.entity == "sales":
        base_q = select(func.count()).select_from(SaleModel).where(
            SaleModel.company_id == current_user.company_id,
            SaleModel.status.in_(["confirmed", "paid"]),
        )
        if cutoff:
            base_q = base_q.where(SaleModel.created_at >= cutoff)

        total = db.scalar(base_q) or 0

        cond_a_q = base_q.where(SaleModel.is_credit.is_(True))
        if payload.condition_a == "high_amount":
            cond_a_q = base_q.where(SaleModel.total_amount >= payload.threshold_amount)
        elif payload.condition_a == "paid":
            cond_a_q = base_q.where(SaleModel.status == "paid")
        count_a = db.scalar(cond_a_q) or 0

        cond_b_q = base_q.where(SaleModel.total_amount >= payload.threshold_amount)
        if payload.condition_b == "credit":
            cond_b_q = base_q.where(SaleModel.is_credit.is_(True))
        elif payload.condition_b == "paid":
            cond_b_q = base_q.where(SaleModel.status == "paid")
        count_b = db.scalar(cond_b_q) or 0

        inter_q = select(func.count()).select_from(SaleModel).where(
            SaleModel.company_id == current_user.company_id,
            SaleModel.status.in_(["confirmed", "paid"]),
        )
        if cutoff:
            inter_q = inter_q.where(SaleModel.created_at >= cutoff)
        if payload.condition_a == "high_amount":
            inter_q = inter_q.where(SaleModel.total_amount >= payload.threshold_amount)
        elif payload.condition_a == "credit" or payload.condition_a == "with_balance":
            inter_q = inter_q.where(SaleModel.is_credit.is_(True))
        elif payload.condition_a == "paid":
            inter_q = inter_q.where(SaleModel.status == "paid")
        if payload.condition_b == "high_amount":
            inter_q = inter_q.where(SaleModel.total_amount >= payload.threshold_amount)
        elif payload.condition_b == "credit":
            inter_q = inter_q.where(SaleModel.is_credit.is_(True))
        elif payload.condition_b == "paid":
            inter_q = inter_q.where(SaleModel.status == "paid")
        count_inter = db.scalar(inter_q) or 0

    else:
        base_q = select(func.count(func.distinct(CustomerModel.id))).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.is_active.is_(True),
        )
        if cutoff:
            base_q = base_q.where(CustomerModel.created_at >= cutoff)

        total = db.scalar(base_q) or 0

        from sqlalchemy import exists

        sale_sub_a = (
            select(SaleModel.customer_id)
            .where(
                SaleModel.company_id == current_user.company_id,
                SaleModel.status.in_(["confirmed", "paid"]),
                SaleModel.total_amount >= payload.threshold_amount,
            )
            .distinct()
        )
        if payload.condition_a == "with_balance":
            sale_sub_a = (
                select(SaleModel.customer_id)
                .where(
                    SaleModel.company_id == current_user.company_id,
                    SaleModel.status.in_(["confirmed", "paid"]),
                )
                .distinct()
            )
        cond_a_q = select(func.count(func.distinct(CustomerModel.id))).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.is_active.is_(True),
            CustomerModel.id.in_(sale_sub_a),
        )
        if cutoff:
            cond_a_q = cond_a_q.where(CustomerModel.created_at >= cutoff)
        count_a = db.scalar(cond_a_q) or 0

        sale_sub_b = (
            select(SaleModel.customer_id)
            .where(
                SaleModel.company_id == current_user.company_id,
                SaleModel.status.in_(["confirmed", "paid"]),
                SaleModel.total_amount >= payload.threshold_amount,
            )
            .distinct()
        )
        if payload.condition_b == "multiple_purchases":
            sale_sub_b = (
                select(SaleModel.customer_id)
                .where(
                    SaleModel.company_id == current_user.company_id,
                    SaleModel.status.in_(["confirmed", "paid"]),
                )
                .group_by(SaleModel.customer_id)
                .having(func.count(SaleModel.id) > 1)
            )
        cond_b_q = select(func.count(func.distinct(CustomerModel.id))).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.is_active.is_(True),
            CustomerModel.id.in_(sale_sub_b),
        )
        if cutoff:
            cond_b_q = cond_b_q.where(CustomerModel.created_at >= cutoff)
        count_b = db.scalar(cond_b_q) or 0

        inter_q = select(func.count(func.distinct(CustomerModel.id))).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.is_active.is_(True),
            CustomerModel.id.in_(sale_sub_a),
            CustomerModel.id.in_(sale_sub_b),
        )
        if cutoff:
            inter_q = inter_q.where(CustomerModel.created_at >= cutoff)
        count_inter = db.scalar(inter_q) or 0

    return {
        "entity": payload.entity,
        "period": payload.period,
        "condition_a": payload.condition_a,
        "condition_b": payload.condition_b,
        "sample_space_size": total,
        "event_a_count": count_a,
        "event_b_count": count_b,
        "intersection_count": count_inter,
    }
