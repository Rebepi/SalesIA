from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from salesia.modules.analitica.application.auxiliares.resolve_dataset_values import resolve_dataset_values
from salesia.modules.analitica.application.contracts.variables_aleatorias import VariableAnalyzeRequest
from salesia.modules.analitica.domain.statistics import (
    VariableScale,
    compute_statistical_summary,
    sanitize_numeric_values,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.domain.exceptions import EmptySampleException, IncompatibleVariableScaleException


async def post_analyze_variable(payload: VariableAnalyzeRequest, current_user: AuthenticatedUser, db: Session):
    return await run_in_threadpool(post_analyze_variable_sync, payload, current_user, db)


def post_analyze_variable_sync(payload: VariableAnalyzeRequest, current_user: AuthenticatedUser, db: Session):
    try:
        clean_name = payload.name.strip().lower()

        if clean_name in ("canal", "channel", "numero_documento", "document_number", "nro_documento"):
            if payload.scale in (VariableScale.QUALITATIVE_NOMINAL, VariableScale.QUALITATIVE_ORDINAL):
                obs = payload.observations or []

                distinct_vals = len(set(obs)) if obs else 0

                return {
                    "name": payload.name,
                    "scale": payload.scale.value,
                    "observations_count": len(obs),
                    "distinct_values_count": distinct_vals,
                    "mean": None,
                    "median": None,
                    "minimum": None,
                    "maximum": None,
                    "sum_total": None,
                    "skewness_direction": "no_aplicable",
                    "explanation": "Canal y número de documento son identificadores categóricos y no admiten media numérica aunque sus códigos sean dígitos.",
                }

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Canal y número de documento no admiten media numérica aunque sus códigos sean dígitos",
                )

        if payload.dataset_id is not None:
            var_name = payload.variable_name or payload.name

            cleaned, _, _ = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_name,
            )

        elif payload.observations is not None:
            if not payload.observations:
                raise EmptySampleException()

            cleaned, _ = sanitize_numeric_values(payload.observations)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Debe proporcionar 'observations' o 'dataset_id'"
            )

        if not cleaned:
            raise EmptySampleException()

        summary = compute_statistical_summary(cleaned)

        distinct_vals = len(set(cleaned))

        return {
            "name": payload.name,
            "scale": payload.scale.value,
            "observations_count": summary.count,
            "distinct_values_count": distinct_vals,
            "mean": str(summary.mean),
            "median": str(summary.median),
            "minimum": str(summary.minimum),
            "maximum": str(summary.maximum),
            "sum_total": str(summary.sum_total),
            "skewness_direction": summary.skewness_direction,
            "explanation": summary.explanation,
            "didactic_concept": (
                "En variables continuas intervalos y probabilidades puntuales son conceptos distintos."
                if payload.scale == VariableScale.QUANTITATIVE_CONTINUOUS
                else "En variables discretas la masa probabilistica total suma 1."
            ),
        }

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

    except IncompatibleVariableScaleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
