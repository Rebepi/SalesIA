import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from salesia.modules.analitica.application.auxiliares.resolve_dataset_values import resolve_dataset_values
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import (
    CompareRequest,
    DescriptiveSummaryRequest,
    MeanRequest,
    MedianRequest,
    WeightedMeanRequest,
)
from salesia.modules.analitica.domain.statistics import (
    ALGORITHM_VERSION,
    DEFAULT_DECIMAL_PRECISION,
    VariableScale,
    calculate_mean,
    calculate_median,
    calculate_median_exact,
    calculate_weighted_mean,
    compute_descriptive_summary,
    sanitize_numeric_values,
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.domain.exceptions import (
    EmptySampleException,
    IncompatibleVariableScaleException,
    InvariantViolationException,
)


async def post_mean(payload: MeanRequest, current_user: AuthenticatedUser, db: Session):
    return await run_in_threadpool(post_mean_sync, payload, current_user, db)


def post_mean_sync(payload: MeanRequest, current_user: AuthenticatedUser, db: Session):
    try:
        version_artifact = None

        var_name = payload.variable_name or "total_amount"

        if var_name.strip().lower() in ("canal", "channel", "numero_documento", "document_number", "nro_documento"):
            raise IncompatibleVariableScaleException(
                "Canal y número de documento no admiten media numérica aunque sus códigos sean dígitos"
            )

        if payload.dataset_id is not None:
            cleaned, null_cnt, version_artifact = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_name,
                null_policy=payload.null_policy,
            )

            if not cleaned:
                raise EmptySampleException()

            mean_val = calculate_mean(cleaned, payload.null_policy)

            count_val = len(cleaned)

        elif payload.values is not None:
            if not payload.values:
                raise EmptySampleException()

            cleaned, null_cnt = sanitize_numeric_values(payload.values, null_policy=payload.null_policy)

            if not cleaned:
                raise EmptySampleException()

            mean_val = calculate_mean(cleaned, payload.null_policy)

            count_val = len(cleaned)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Debe proporcionar 'values' o 'dataset_id'"
            )

        res_data = {
            "count": count_val,
            "mean": str(mean_val),
            "null_count": null_cnt,
            "null_policy": payload.null_policy,
            "variable_name": var_name,
            "algorithm_version": ALGORITHM_VERSION,
            "tolerance": str(DEFAULT_DECIMAL_PRECISION),
            "didactic_explanation": {
                "formula": "media = sum(x_i) / n",
                "valid_count": count_val,
                "mean": str(mean_val),
                "unit": "monetaria/numerica",
            },
        }

        if payload.record_run or payload.dataset_id:
            exec_id = uuid4()

            record = {
                "id": str(exec_id),
                "name": f"Media de {var_name}",
                "dataset_id": str(payload.dataset_id) if payload.dataset_id else None,
                "dataset_version": version_artifact.version if version_artifact is not None else payload.dataset_version or 1,
                "variable_name": var_name,
                "analysis_type": "mean",
                "result": res_data,
                "algorithm_version": ALGORITHM_VERSION,
                "status": "completed",
                "created_by": str(current_user.user_id),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            db.add(
                AnalyticsArtifact(
                    id=exec_id,
                    company_id=current_user.company_id,
                    kind="analysis",
                    artifact_key=str(exec_id),
                    version=1,
                    status="completed",
                    data_json=json.dumps(record),
                    parent_id=version_artifact.id if version_artifact else None,
                    created_by=current_user.user_id,
                )
            )

            db.commit()

            res_data["execution_id"] = str(exec_id)

        return res_data

    except IncompatibleVariableScaleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def post_median(payload: MedianRequest, current_user: AuthenticatedUser, db: Session):
    return await run_in_threadpool(post_median_sync, payload, current_user, db)


def post_median_sync(payload: MedianRequest, current_user: AuthenticatedUser, db: Session):
    try:
        version_artifact = None

        var_name = payload.variable_name or "total_amount"

        if var_name.strip().lower() in ("canal", "channel", "numero_documento", "document_number", "nro_documento"):
            raise IncompatibleVariableScaleException(
                "Canal y número de documento no admiten media numérica aunque sus códigos sean dígitos"
            )

        if payload.dataset_id is not None:
            cleaned, null_cnt, version_artifact = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_name,
                null_policy=payload.null_policy,
            )

            if not cleaned:
                raise EmptySampleException()

            med_val = calculate_median_exact(cleaned, payload.null_policy)

            count_val = len(cleaned)

        elif payload.values is not None:
            if not payload.values:
                raise EmptySampleException()

            cleaned, null_cnt = sanitize_numeric_values(payload.values, null_policy=payload.null_policy)

            if not cleaned:
                raise EmptySampleException()

            med_val = calculate_median(cleaned, payload.null_policy)

            count_val = len(cleaned)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Debe proporcionar 'values' o 'dataset_id'"
            )

        res_data = {
            "count": count_val,
            "median": str(med_val),
            "null_count": null_cnt,
            "null_policy": payload.null_policy,
            "variable_name": var_name,
            "algorithm_version": ALGORITHM_VERSION,
            "tolerance": str(DEFAULT_DECIMAL_PRECISION),
            "didactic_explanation": {
                "formula": "mediana = x_{(n+1)/2} o (x_{n/2} + x_{n/2+1})/2",
                "valid_count": count_val,
                "median": str(med_val),
                "unit": "monetaria/numerica",
            },
        }

        if payload.record_run or payload.dataset_id:
            exec_id = uuid4()

            record = {
                "id": str(exec_id),
                "name": f"Mediana de {var_name}",
                "dataset_id": str(payload.dataset_id) if payload.dataset_id else None,
                "dataset_version": version_artifact.version if version_artifact is not None else payload.dataset_version or 1,
                "variable_name": var_name,
                "analysis_type": "median",
                "result": res_data,
                "algorithm_version": ALGORITHM_VERSION,
                "status": "completed",
                "created_by": str(current_user.user_id),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            db.add(
                AnalyticsArtifact(
                    id=exec_id,
                    company_id=current_user.company_id,
                    kind="analysis",
                    artifact_key=str(exec_id),
                    version=1,
                    status="completed",
                    data_json=json.dumps(record),
                    parent_id=version_artifact.id if version_artifact else None,
                    created_by=current_user.user_id,
                )
            )

            db.commit()

            res_data["execution_id"] = str(exec_id)

        return res_data

    except IncompatibleVariableScaleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def post_compare(payload: CompareRequest, current_user: AuthenticatedUser, db: Session):
    return await run_in_threadpool(post_compare_sync, payload, current_user, db)


def post_compare_sync(payload: CompareRequest, current_user: AuthenticatedUser, db: Session):
    try:
        if payload.dataset_id is not None:
            var_a = payload.variable_a or "total_amount"

            var_b = payload.variable_b or "paid_amount"

            cleaned_a, _, _ = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_a,
            )

            cleaned_b, _, _ = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_b,
            )

        elif payload.values_a is not None and payload.values_b is not None:
            if not payload.values_a or not payload.values_b:
                raise EmptySampleException()

            cleaned_a, _ = sanitize_numeric_values(payload.values_a)

            cleaned_b, _ = sanitize_numeric_values(payload.values_b)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar series 'values_a' y 'values_b' o 'dataset_id'",
            )

        if not cleaned_a or not cleaned_b:
            raise EmptySampleException()

        mean_a = calculate_mean(cleaned_a)

        median_a = calculate_median(cleaned_a)

        mean_b = calculate_mean(cleaned_b)

        median_b = calculate_median(cleaned_b)

        delta_mean = mean_b - mean_a

        delta_median = median_b - median_a

        rel_delta_mean = (
            (abs(delta_mean) / abs(mean_a)).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
            if mean_a != Decimal("0")
            else None
        )

        rel_delta_median = (
            (abs(delta_median) / abs(median_a)).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
            if median_a != Decimal("0")
            else None
        )

        explanation = (
            "La comparación entre series y entre media y mediana describe asimetría muestral empírica, "
            "pero no permite concluir por sí sola causalidad operativa, presencia de fraude o la forma exacta de la distribución."
        )

        return {
            "series_a": {
                "label": payload.label_a,
                "count": len(cleaned_a),
                "mean": str(mean_a),
                "median": str(median_a),
            },
            "series_b": {
                "label": payload.label_b,
                "count": len(cleaned_b),
                "mean": str(mean_b),
                "median": str(median_b),
            },
            "differences": {
                "delta_mean": str(delta_mean),
                "delta_median": str(delta_median),
                "relative_delta_mean": str(rel_delta_mean) if rel_delta_mean is not None else None,
                "relative_delta_median": str(rel_delta_median) if rel_delta_median is not None else None,
            },
            "explanation": explanation,
            "universe_note": "Asegúrese de comparar series bajo el mismo universo comercial y periodo elegible.",
        }

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def post_descriptive_summary(payload: DescriptiveSummaryRequest, current_user: AuthenticatedUser, db: Session):
    values, excluded_count, version_artifact = resolve_dataset_values(
        db=db,
        company_id=current_user.company_id,
        dataset_id=payload.dataset_id,
        dataset_version=payload.dataset_version,
        variable_name=payload.variable_name,
        null_policy=payload.null_policy,
    )

    result = compute_descriptive_summary(
        values=values,
        scale=VariableScale.QUANTITATIVE_CONTINUOUS,
        null_policy="error",
        variable_name=payload.variable_name,
    )

    quantum = Decimal("1").scaleb(-payload.precision)

    def formatted(value):

        if value is None:
            return None

        return str(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_EVEN))

    direction = result.get("skewness_direction", "no_determinado")

    explanation = f"La variable {payload.variable_name} fue calculada sobre {result['count']} observaciones de la versión {version_artifact.version}. La relación entre media y mediana indica {direction.replace('_', ' ')}."

    return {
        "variable_name": payload.variable_name,
        "n": result["count"],
        "excluded_count": excluded_count,
        "mean": formatted(result.get("mean")),
        "median": formatted(result.get("median")),
        "variance": formatted(result.get("variance")),
        "stdev": formatted(result.get("stdev")),
        "skewness": direction,
        "min": formatted(result.get("minimum")),
        "max": formatted(result.get("maximum")),
        "precision": payload.precision,
        "algorithm": "Decimal deterministic descriptive statistics",
        "algorithm_version": "STATS_DECIMAL_V1",
        "symmetry_diagnosis": direction.replace("_", " ").capitalize(),
        "explanation": explanation,
        "dataset_id": str(payload.dataset_id),
        "dataset_version": version_artifact.version,
    }


def post_weighted_mean(payload: WeightedMeanRequest, current_user: AuthenticatedUser):
    try:
        return calculate_weighted_mean(values=payload.values, weights=payload.weights, method=payload.method)

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=400, detail=e.message)
