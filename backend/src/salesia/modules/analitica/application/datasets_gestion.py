import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.datasets_gestion import (
    DatasetCreateRequest,
    DatasetExpireRequest,
    SamplingRequest,
)
from salesia.modules.analitica.domain.advanced import execute_reproducible_sampling
from salesia.modules.analitica.domain.dataset import build_data_quality_report
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_dataset(payload: DatasetCreateRequest, current_user: AuthenticatedUser, db: Session):
    dataset_id = uuid4()

    data = {
        "id": str(dataset_id),
        "name": payload.name,
        "description": payload.description,
        "variable_scale": payload.variable_scale.value,
        "grain": payload.grain,
        "source_entity": payload.source_entity,
        "filters": payload.filters or {},
        "variables": payload.variables or [],
        "current_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            id=dataset_id,
            company_id=current_user.company_id,
            kind="dataset",
            artifact_key=str(dataset_id),
            version=1,
            status="active",
            data_json=json.dumps(data),
            created_by=current_user.user_id,
        )
    )

    v1_cols = (
        [v.get("name") for v in payload.variables if isinstance(v, dict) and "name" in v]
        if payload.variables
        else ["total_amount", "paid_amount"]
    )

    v1_data = {
        "dataset_id": str(dataset_id),
        "version": 1,
        "row_count": 0,
        "data_hash": "sha256-empty",
        "sha256_hash": "sha256-empty",
        "schema_snapshot": {"columns": v1_cols, "grain": payload.grain},
        "quality_report": build_data_quality_report(0, [], {}, []),
        "storage_type": "inline",
        "file_path": None,
        "scope_type": "sample",
        "sample_size": 0,
        "total_population": 0,
        "sampling_method": "full",
        "parameters": {},
        "preview_sample": [],
        "sample": [],
        "variables": payload.variables or [],
        "status": "immutable",
        "created_by": str(current_user.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            company_id=current_user.company_id,
            kind="dataset_version",
            artifact_key=str(dataset_id),
            version=1,
            status="immutable",
            data_json=json.dumps(v1_data),
            parent_id=dataset_id,
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return {**data, "active_version": 1, "row_count": 0}


def list_datasets(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
            AnalyticsArtifact.status == "active",
        )
        .order_by(AnalyticsArtifact.created_at.desc())
    ).all()

    items = []

    for row in rows:
        data = json.loads(row.data_json)

        current_version = int(data.get("current_version", 0))

        version_data = None

        if current_version > 0:
            version_row = db.scalar(
                select(AnalyticsArtifact).where(
                    AnalyticsArtifact.company_id == current_user.company_id,
                    AnalyticsArtifact.kind == "dataset_version",
                    AnalyticsArtifact.artifact_key == str(row.id),
                    AnalyticsArtifact.version == current_version,
                )
            )

            if version_row:
                version_data = json.loads(version_row.data_json)

        items.append(
            {
                **data,
                "id": str(row.id),
                "active_version": current_version,
                "row_count": int((version_data or {}).get("row_count", 0)),
                "status": row.status,
            }
        )

    return {"items": items, "count": len(items)}


def get_dataset(dataset_id: UUID, current_user: AuthenticatedUser, db: Session):
    root = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == dataset_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
        )
    )

    if not root:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")

    return json.loads(root.data_json)


def expire_dataset_version(
    dataset_id: UUID,
    version: int,
    payload: Optional[DatasetExpireRequest],
    current_user: AuthenticatedUser,
    db: Session,
):
    row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == str(dataset_id),
            AnalyticsArtifact.version == version,
        )
    )

    if not row:
        raise HTTPException(status_code=404, detail="Versión de dataset no encontrada.")

    data = json.loads(row.data_json)

    data["status"] = "expired"

    data["data_available"] = False

    data["retention_reason"] = payload.retention_reason if payload else "politica_retencion"

    row.status = "expired"

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return data


def post_dataset_sample(payload: SamplingRequest):
    return execute_reproducible_sampling(
        rows=payload.rows,
        size=payload.size,
        fraction=payload.fraction,
        seed=payload.seed,
        replace=payload.replace,
        strata_column=payload.strata_column,
    )
