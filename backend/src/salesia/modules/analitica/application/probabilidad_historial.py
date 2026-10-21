import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.probabilidad_historial import (
    DuplicateScenarioRequest,
    ProbabilityAnalysisSaveRequest,
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def post_probability_analysis_save(
    payload: ProbabilityAnalysisSaveRequest, current_user: AuthenticatedUser, db: Session
):
    analysis_id = uuid4()

    if payload.dataset_id:
        ds = db.scalar(
            select(AnalyticsArtifact).where(
                AnalyticsArtifact.id == payload.dataset_id,
                AnalyticsArtifact.kind == "dataset",
                AnalyticsArtifact.company_id == current_user.company_id,
            )
        )

        if not ds:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset no encontrado o no pertenece a la empresa"
            )

    artifact_data = {
        "id": str(analysis_id),
        "name": payload.name,
        "dataset_id": str(payload.dataset_id) if payload.dataset_id else None,
        "dataset_version": payload.dataset_version,
        "universe_definition": payload.universe_definition.model_dump() if payload.universe_definition else None,
        "event_a_definition": payload.event_a_definition.model_dump() if payload.event_a_definition else None,
        "event_b_definition": payload.event_b_definition.model_dump() if payload.event_b_definition else None,
        "mode": payload.mode,
        "counts": payload.counts or {},
        "probabilities": payload.probabilities or {},
        "smoothing_enabled": payload.smoothing_enabled,
        "alpha": str(payload.alpha),
        "is_simulation": payload.is_simulation,
        "scenario_type": payload.scenario_type,
        "base_analysis_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": str(current_user.user_id),
    }

    db.add(
        AnalyticsArtifact(
            id=analysis_id,
            company_id=current_user.company_id,
            kind="probability_analysis",
            artifact_key=str(analysis_id),
            version=1,
            status="active",
            data_json=json.dumps(artifact_data),
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return artifact_data


def list_probability_analyses(current_user: AuthenticatedUser, db: Session):
    artifacts = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "probability_analysis"
        )
        .order_by(AnalyticsArtifact.created_at.desc())
    ).all()

    return [json.loads(a.data_json) for a in artifacts]


def get_probability_analysis(analysis_id: UUID, current_user: AuthenticatedUser, db: Session):
    art = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == analysis_id, AnalyticsArtifact.kind == "probability_analysis"
        )
    )

    if not art or art.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analisis de probabilidad no encontrado o no pertenece a la empresa",
        )

    return json.loads(art.data_json)


def duplicate_probability_scenario(
    analysis_id: UUID, payload: DuplicateScenarioRequest, current_user: AuthenticatedUser, db: Session
):
    art = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == analysis_id,
            AnalyticsArtifact.kind == "probability_analysis",
            AnalyticsArtifact.company_id == current_user.company_id,
        )
    )

    if not art:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis base no encontrado")

    base_data = json.loads(art.data_json)

    new_id = uuid4()

    new_probs = dict(base_data.get("probabilities", {}))

    if payload.modified_prior_a is not None:
        new_probs["prior_a"] = str(payload.modified_prior_a)

    if payload.modified_evidence_b is not None:
        new_probs["evidence_b"] = str(payload.modified_evidence_b)

    if payload.modified_likelihood_b_given_a is not None:
        new_probs["likelihood_b_given_a"] = str(payload.modified_likelihood_b_given_a)

    scenario_data = {
        **base_data,
        "id": str(new_id),
        "name": payload.scenario_name,
        "is_simulation": True,
        "scenario_type": "simulation",
        "simulation_label": "Simulacion hipotetica",
        "base_analysis_id": str(analysis_id),
        "probabilities": new_probs,
        "alpha": str(payload.modified_alpha) if payload.modified_alpha is not None else base_data.get("alpha"),
        "smoothing_enabled": payload.smoothing_enabled
        if payload.smoothing_enabled is not None
        else base_data.get("smoothing_enabled", False),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": str(current_user.user_id),
    }

    db.add(
        AnalyticsArtifact(
            id=new_id,
            company_id=current_user.company_id,
            kind="probability_analysis",
            artifact_key=str(new_id),
            version=1,
            status="active",
            parent_id=analysis_id,
            data_json=json.dumps(scenario_data),
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return scenario_data
