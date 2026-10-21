import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.analitica_models import ModelMonitorRequest, ModelRegisterRequest
from salesia.modules.analitica.domain.advanced import monitor_model_drift_and_health, register_statistical_model
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def post_model_registration(payload: ModelRegisterRequest, current_user: AuthenticatedUser, db: Session):
    try:
        ds_id = UUID(payload.dataset_id)

    except Exception:
        ds_id = uuid4()

    return register_statistical_model(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.user_id,
        name=payload.name,
        algorithm=payload.algorithm,
        hyperparameters=payload.hyperparameters,
        feature_names=payload.feature_names,
        dataset_id=ds_id,
        dataset_version=payload.dataset_version,
        dataset_hash=payload.dataset_hash,
        seed=payload.seed,
        evaluation_metrics=payload.evaluation_metrics,
        previous_version_id=payload.previous_version_id,
    )


def get_models_list(name: Optional[str], current_user: AuthenticatedUser, db: Session):
    q = select(AnalyticsArtifact).where(
        AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "statistical_model"
    )

    if name:
        q = q.where(AnalyticsArtifact.artifact_key == name)

    q = q.order_by(AnalyticsArtifact.version.desc())

    arts = db.scalars(q).all()

    return [json.loads(a.data_json) for a in arts]


def get_model_by_id(model_id: UUID, current_user: AuthenticatedUser, db: Session):
    art = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == model_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "statistical_model",
        )
    )

    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo no encontrado")

    return json.loads(art.data_json)


def post_model_monitoring(model_id: UUID, payload: ModelMonitorRequest, current_user: AuthenticatedUser, db: Session):
    art = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == model_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "statistical_model",
        )
    )

    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo no encontrado")

    return monitor_model_drift_and_health(
        training_distribution=payload.training_distribution,
        current_distribution=payload.current_distribution,
        error_metric_baseline=payload.error_metric_baseline,
        current_error_metric=payload.current_error_metric,
        error_threshold_ratio=payload.error_threshold_ratio,
    )
