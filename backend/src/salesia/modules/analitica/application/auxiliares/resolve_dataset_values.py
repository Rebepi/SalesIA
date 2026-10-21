import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.statistics import sanitize_numeric_values
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.shared.infrastructure.config import settings


def resolve_dataset_values(
    db: Session,
    company_id: UUID,
    dataset_id: UUID,
    dataset_version: Optional[int],
    variable_name: str,
    null_policy: str = "skip",
) -> tuple[list[Decimal], int, Any]:

    dataset_root = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == dataset_id,
            AnalyticsArtifact.company_id == company_id,
            AnalyticsArtifact.kind == "dataset",
        )
    )

    if not dataset_root:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset no encontrado.")

    root_data = json.loads(dataset_root.data_json)

    target_version = dataset_version or int(root_data.get("current_version", 1))

    version_artifact = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == str(dataset_id),
            AnalyticsArtifact.version == target_version,
        )
    )

    if not version_artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión de dataset no encontrada.")

    v_data = json.loads(version_artifact.data_json)

    rows = []

    if v_data.get("storage_type") == "private_file" and v_data.get("file_path"):
        fpath = Path(settings.private_storage_path).resolve() / v_data["file_path"]

        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                rows = json.load(f)

    else:
        rows = v_data.get("rows") or v_data.get("preview_sample", [])

    clean_var = variable_name.strip().lower()

    if clean_var in ("canal", "channel", "numero_documento", "document_number", "nro_documento"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Canal y número de documento no admiten media numérica aunque sus códigos sean dígitos",
        )

    raw_vals = [r.get(variable_name) for r in rows]

    cleaned, null_count = sanitize_numeric_values(raw_vals, null_policy=null_policy)

    return cleaned, null_count, version_artifact
