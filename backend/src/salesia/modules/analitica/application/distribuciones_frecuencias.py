import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.auxiliares.resolve_dataset_values import resolve_dataset_values
from salesia.modules.analitica.application.contracts.distribuciones_frecuencias import (
    DistributionRequest,
    FrequenciesRequest,
    OutliersAnalysisRequest,
)
from salesia.modules.analitica.domain.statistics import (
    analyze_extreme_values,
    calculate_distribution,
    calculate_frequencies,
    sanitize_numeric_values,
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.domain.exceptions import EmptySampleException


def post_frequencies(payload: FrequenciesRequest, current_user: AuthenticatedUser, db: Session):
    try:
        if payload.dataset_id is not None:
            var_name = payload.variable_name or "status"

            dataset_root = db.scalar(
                select(AnalyticsArtifact).where(
                    AnalyticsArtifact.id == payload.dataset_id,
                    AnalyticsArtifact.company_id == current_user.company_id,
                    AnalyticsArtifact.kind == "dataset",
                )
            )

            if not dataset_root:
                raise HTTPException(status_code=404, detail="Dataset no encontrado.")

            v_num = payload.dataset_version or json.loads(dataset_root.data_json).get("current_version", 1)

            v_art = db.scalar(
                select(AnalyticsArtifact).where(
                    AnalyticsArtifact.company_id == current_user.company_id,
                    AnalyticsArtifact.kind == "dataset_version",
                    AnalyticsArtifact.artifact_key == str(payload.dataset_id),
                    AnalyticsArtifact.version == v_num,
                )
            )

            if not v_art:
                raise HTTPException(status_code=404, detail="Versión de dataset no encontrada.")

            rows = json.loads(v_art.data_json).get("rows") or json.loads(v_art.data_json).get("preview_sample", [])

            vals = [r.get(var_name) for r in rows]

        elif payload.values is not None:
            vals = payload.values

        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar 'values' o 'dataset_id'")

        return calculate_frequencies(vals, order=payload.order)

    except EmptySampleException as e:
        raise HTTPException(status_code=400, detail=e.message)


def post_distribution(payload: DistributionRequest, current_user: AuthenticatedUser, db: Session):
    try:
        if payload.dataset_id is not None:
            var_name = payload.variable_name or "total_amount"

            cleaned, _, _ = resolve_dataset_values(
                db=db,
                company_id=current_user.company_id,
                dataset_id=payload.dataset_id,
                dataset_version=payload.dataset_version,
                variable_name=var_name,
            )

        elif payload.values is not None:
            cleaned, _ = sanitize_numeric_values(payload.values)

        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar 'values' o 'dataset_id'")

        return calculate_distribution(
            cleaned, num_bins=payload.num_bins, bin_width=payload.bin_width, bin_policy=payload.bin_policy
        )

    except EmptySampleException as e:
        raise HTTPException(status_code=400, detail=e.message)


def post_outliers(payload: OutliersAnalysisRequest, current_user: AuthenticatedUser):
    try:
        return analyze_extreme_values(payload.values, null_policy=payload.null_policy)

    except EmptySampleException as e:
        raise HTTPException(status_code=400, detail=e.message)
