import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.historial import AnalysisCreateRequest, AnalysisRepeatRequest
from salesia.modules.analitica.domain.dataset import apply_variable_transformations
from salesia.modules.analitica.domain.statistics import calculate_mean, calculate_median_exact, sanitize_numeric_values
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings


def create_analysis(payload: AnalysisCreateRequest, current_user: AuthenticatedUser, db: Session):
    dataset_root = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == payload.dataset_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
        )
    )

    if not dataset_root:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")

    root_data = json.loads(dataset_root.data_json)

    target_version = payload.dataset_version or int(root_data.get("current_version", 1))

    version_artifact = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == str(payload.dataset_id),
            AnalyticsArtifact.version == target_version,
        )
    )

    if not version_artifact:
        raise HTTPException(status_code=404, detail="Versión de dataset no encontrada.")

    v_data = json.loads(version_artifact.data_json)

    rows = []

    if v_data.get("storage_type") == "private_file" and v_data.get("file_path"):
        fpath = Path(settings.private_storage_path).resolve() / v_data["file_path"]

        if not fpath.is_file():
            raise HTTPException(409, "El archivo de la versión del dataset no está disponible. No se puede calcular un resultado reproducible.")
        with open(fpath, "r", encoding="utf-8") as f:
            rows = json.load(f)

    else:
        rows = v_data.get("rows") or v_data.get("preview_sample", [])

    param_dict = payload.parameters or {}

    transformations = param_dict.get("transformations", [])

    raw_values = []

    for r in rows:
        val = r.get(payload.variable_name)

        if val is not None and str(val).strip().lower() not in ("", "none", "null"):
            try:
                numeric = Decimal(str(val))
                if numeric.is_finite():
                    raw_values.append(numeric)

            except Exception:
                pass

    if not raw_values:
        result = {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "variance": None,
            "stdev": None,
        }

        raw_metrics = dict(result)

        transformed_metrics = dict(result)

    else:
        raw_sum = sum(raw_values)

        raw_mean = (raw_sum / Decimal(len(raw_values))).quantize(Decimal("0.000001"))

        sorted_vals = sorted(raw_values)

        mid = len(sorted_vals) // 2

        raw_median = (
            sorted_vals[mid]
            if len(sorted_vals) % 2 != 0
            else ((sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal("2")).quantize(Decimal("0.000001"))
        )

        raw_metrics = {
            "count": len(raw_values),
            "mean": str(raw_mean),
            "median": str(raw_median),
            "minimum": str(sorted_vals[0]),
            "maximum": str(sorted_vals[-1]),
        }

        _, trans_metrics = apply_variable_transformations(raw_values, transformations)

        transformed_metrics = trans_metrics

        result = {
            "count": len(raw_values),
            "mean": str(raw_mean),
            "median": str(raw_median),
            "minimum": str(sorted_vals[0]),
            "maximum": str(sorted_vals[-1]),
            "raw_metrics": raw_metrics,
            "transformed_metrics": transformed_metrics,
        }

    analysis_id = uuid4()

    context = dict(root_data.get("filters", {}))

    explanation = f"Distribución estadística para la variable {payload.variable_name} con {len(raw_values)} observaciones analizadas. Las diferencias observadas describen la muestra y no implican causalidad operativa (no implica causalidad ni confirmación de dolo)."

    analysis_record = {
        "id": str(analysis_id),
        "name": payload.name,
        "dataset_id": str(payload.dataset_id),
        "dataset_version": target_version,
        "variable_name": payload.variable_name,
        "analysis_type": payload.analysis_type,
        "context": context,
        "result": result,
        "transformations_applied": transformations,
        "algorithm_version": "v1.2.0",
        "explanation": explanation,
        "status": "completed",
        "created_by": str(current_user.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            id=analysis_id,
            company_id=current_user.company_id,
            kind="analysis",
            artifact_key=str(analysis_id),
            version=1,
            status="completed",
            data_json=json.dumps(analysis_record),
            parent_id=version_artifact.id,
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return analysis_record


def list_analyses(
    dataset_id: Optional[UUID],
    status_filter: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(AnalyticsArtifact).where(
        AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "analysis"
    )

    if status_filter:
        query = query.where(AnalyticsArtifact.status == status_filter)

    ordered = query.order_by(AnalyticsArtifact.created_at.desc(), AnalyticsArtifact.id.desc())
    if not dataset_id:
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.scalars(ordered.offset(offset).limit(limit)).all()
        return {"items": [json.loads(row.data_json) for row in rows], "count": total, "total_count": total}
    filtered = [json.loads(row.data_json) for row in db.scalars(ordered).all()]
    filtered = [row for row in filtered if row.get("dataset_id") == str(dataset_id)]
    return {"items": filtered[offset:offset + limit], "count": len(filtered), "total_count": len(filtered)}


def get_analysis(analysis_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == analysis_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "analysis",
        )
    )

    if not row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")

    return json.loads(row.data_json)


def repeat_analysis(
    analysis_id: UUID, payload: Optional[AnalysisRepeatRequest], current_user: AuthenticatedUser, db: Session
):
    original = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == analysis_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "analysis",
        )
    )

    if not original:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")

    orig_data = json.loads(original.data_json)

    if orig_data.get("status") != "completed":
        raise HTTPException(409, "Solo se pueden repetir análisis completados.")
    if not orig_data.get("dataset_id"):
        raise HTTPException(409, "Esta ejecución no conserva un dataset versionado. Vuelva a ejecutarla desde Estadística con los datos originales.")
    if orig_data.get("analysis_type", "summary") not in ("summary", "mean", "median"):
        raise HTTPException(409, "Este tipo de análisis debe ejecutarse desde su módulo de origen para conservar sus parámetros.")
    if payload and payload.parameters:
        raise HTTPException(422, "Repetir conserva los parámetros originales. Cree un nuevo análisis para cambiarlos.")
    target_version = payload.new_version if payload and payload.new_version else orig_data.get("dataset_version", 1)

    version_artifact = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == orig_data["dataset_id"],
            AnalyticsArtifact.version == target_version,
        )
    )

    if not version_artifact:
        raise HTTPException(status_code=404, detail="Versión de dataset congelado no encontrada.")

    v_data = json.loads(version_artifact.data_json)

    rows = []

    if v_data.get("storage_type") == "private_file" and v_data.get("file_path"):
        fpath = Path(settings.private_storage_path).resolve() / v_data["file_path"]

        if not fpath.is_file():
            raise HTTPException(409, "El archivo de la versión del dataset no está disponible. No se puede calcular un resultado reproducible.")
        with open(fpath, "r", encoding="utf-8") as f:
            rows = json.load(f)

    else:
        rows = v_data.get("rows") or v_data.get("preview_sample", [])

    transformations = orig_data.get("transformations_applied", [])

    raw_values = []

    for r in rows:
        val = r.get(orig_data.get("variable_name", "total_amount"))

        if val is not None and str(val).strip().lower() not in ("", "none", "null"):
            try:
                numeric = Decimal(str(val))
                if numeric.is_finite():
                    raw_values.append(numeric)

            except Exception:
                pass

    if not raw_values:
        result = {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "variance": None,
            "stdev": None,
        }

    else:
        raw_sum = sum(raw_values)

        raw_mean = (raw_sum / Decimal(len(raw_values))).quantize(Decimal("0.000001"))

        sorted_vals = sorted(raw_values)

        mid = len(sorted_vals) // 2

        raw_median = (
            sorted_vals[mid]
            if len(sorted_vals) % 2 != 0
            else ((sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal("2")).quantize(Decimal("0.000001"))
        )

        raw_metrics = {
            "count": len(raw_values),
            "mean": str(raw_mean),
            "median": str(raw_median),
            "minimum": str(sorted_vals[0]),
            "maximum": str(sorted_vals[-1]),
        }

        _, trans_metrics = apply_variable_transformations(raw_values, transformations)

        result = {
            "count": len(raw_values),
            "mean": str(raw_mean),
            "median": str(raw_median),
            "minimum": str(sorted_vals[0]),
            "maximum": str(sorted_vals[-1]),
            "raw_metrics": raw_metrics,
            "transformed_metrics": trans_metrics,
        }

    analysis_type = orig_data.get("analysis_type", "summary")
    if analysis_type in ("mean", "median"):
        null_policy = (orig_data.get("result") or {}).get("null_policy", "skip")
        variable_name = orig_data.get("variable_name") or "total_amount"
        try:
            cleaned, null_count = sanitize_numeric_values([row.get(variable_name) for row in rows], null_policy=null_policy)
            value = calculate_mean(cleaned, null_policy) if analysis_type == "mean" else calculate_median_exact(cleaned, null_policy)
        except (EmptySampleException, InvariantViolationException, ValueError) as cause:
            raise HTTPException(422, str(cause)) from cause
        result = {"count": len(cleaned), analysis_type: str(value), "null_count": null_count, "null_policy": null_policy, "variable_name": variable_name, "algorithm_version": "v1.2.0", "tolerance": "0.000001"}

    execution_id = uuid4()

    repeated_record = {
        "id": str(execution_id),
        "name": f"Repetición de {orig_data.get('name', 'Análisis')}",
        "dataset_id": orig_data["dataset_id"],
        "dataset_version": target_version,
        "variable_name": orig_data.get("variable_name", "total_amount"),
        "analysis_type": orig_data.get("analysis_type", "summary"),
        "original_analysis_id": str(analysis_id),
        "parent_id": str(analysis_id),
        "context": orig_data.get("context", {}),
        "result": result,
        "transformations_applied": transformations,
        "algorithm_version": "v1.2.0",
        "explanation": orig_data.get("explanation", ""),
        "status": "completed",
        "created_by": str(current_user.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            id=execution_id,
            company_id=current_user.company_id,
            kind="analysis",
            artifact_key=str(execution_id),
            version=1,
            status="completed",
            data_json=json.dumps(repeated_record),
            parent_id=original.id,
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return repeated_record


def cancel_analysis(analysis_id: UUID, current_user: AuthenticatedUser, db: Session):
    analysis_row = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == analysis_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "analysis",
        )
    )

    if not analysis_row:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")

    data = json.loads(analysis_row.data_json)

    data["status"] = "cancelled"

    data["result"] = None

    data["cancelled_at"] = datetime.now(timezone.utc).isoformat()

    data["cancelled_by"] = str(current_user.user_id)

    analysis_row.status = "cancelled"

    analysis_row.data_json = json.dumps(data)

    analysis_row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return data
