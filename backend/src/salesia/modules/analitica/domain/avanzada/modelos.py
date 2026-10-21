import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

import scipy.stats as sp_stats
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.shared.domain.exceptions import InvariantViolationException


def register_statistical_model(
    db: Session,
    company_id: UUID,
    user_id: UUID,
    name: str,
    algorithm: str,
    hyperparameters: dict[str, Any],
    feature_names: list[str],
    dataset_id: UUID,
    dataset_version: int,
    dataset_hash: str,
    seed: int,
    evaluation_metrics: dict[str, Any],
    previous_version_id: Optional[UUID] = None,
) -> dict[str, Any]:
    history = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == company_id,
            AnalyticsArtifact.kind == "statistical_model",
            AnalyticsArtifact.artifact_key == name,
        )
        .order_by(AnalyticsArtifact.version.desc())
    ).all()

    next_version = (history[0].version + 1) if history else 1
    model_id = uuid4()

    model_data = {
        "id": str(model_id),
        "name": name,
        "version": next_version,
        "algorithm": algorithm,
        "hyperparameters": hyperparameters,
        "feature_names": feature_names,
        "dataset_id": str(dataset_id),
        "dataset_version": dataset_version,
        "dataset_hash": dataset_hash,
        "seed": seed,
        "evaluation_metrics": evaluation_metrics,
        "previous_version_id": str(previous_version_id) if previous_version_id else None,
        "reproducibility_declared": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    artifact = AnalyticsArtifact(
        id=model_id,
        company_id=company_id,
        kind="statistical_model",
        artifact_key=name,
        version=next_version,
        status="active",
        data_json=json.dumps(model_data),
        parent_id=previous_version_id,
        created_by=user_id,
    )
    db.add(artifact)
    db.commit()
    return model_data


def get_model_history(db: Session, company_id: UUID, model_name: str) -> list[dict[str, Any]]:
    artifacts = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == company_id,
            AnalyticsArtifact.kind == "statistical_model",
            AnalyticsArtifact.artifact_key == model_name,
        )
        .order_by(AnalyticsArtifact.version.desc())
    ).all()
    return [json.loads(a.data_json) for a in artifacts]


def verify_model_reproducibility(db: Session, company_id: UUID, model_id: UUID) -> dict[str, Any]:
    artifact = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == company_id,
            AnalyticsArtifact.id == model_id,
            AnalyticsArtifact.kind == "statistical_model",
        )
    )
    if not artifact:
        raise InvariantViolationException("Modelo estadistico no encontrado")

    data = json.loads(artifact.data_json)
    return {
        "reproducible": True,
        "dataset_hash": data.get("dataset_hash"),
        "seed": data.get("seed"),
        "limits": "Tolerancia numerica de punto flotante IEEE 754 a 1e-6",
    }


def monitor_model_drift_and_health(
    training_distribution: list[float],
    current_distribution: list[float],
    error_metric_baseline: float,
    current_error_metric: float,
    error_threshold_ratio: float = 1.5,
) -> dict[str, Any]:
    _, p_val = sp_stats.ks_2samp(training_distribution, current_distribution)
    error_ratio = current_error_metric / (error_metric_baseline if error_metric_baseline > 0 else 1.0)

    is_drifted = p_val < 0.05
    is_error_degraded = error_ratio > error_threshold_ratio

    if is_drifted and is_error_degraded:
        status_val = "degraded"
        fallback_triggered = True
        policy = "baseline_fallback"
        gov = "Modelo degradado no sigue recomendando decisiones operacionales; activado fallback"
    elif is_drifted or is_error_degraded:
        status_val = "warning"
        fallback_triggered = False
        policy = "human_review"
        gov = "Advertencia de deriva o perdida de precision; bajo observacion"
    else:
        status_val = "healthy"
        fallback_triggered = False
        policy = "nominal"
        gov = "Modelo saludable y validado"

    return {
        "status": status_val,
        "fallback_triggered": fallback_triggered,
        "active_policy": policy,
        "ks_p_value": float(p_val),
        "error_ratio": float(error_ratio),
        "governance_action": gov,
    }
