import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.auxiliares.report_run_data import report_run_data
from salesia.modules.analitica.application.auxiliares.report_run_row import report_run_row
from salesia.modules.analitica.application.auxiliares.write_report_artifact import write_report_artifact
from salesia.modules.analitica.application.contracts.reportes_ejecuciones import ReportRunRequest
from salesia.modules.analitica.domain.reports import execute_report_data, get_report_catalog
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import CompanyModel, JobModel, UserModel
from salesia.modules.analitica.application.reportes.operativos import authorize_report, required_report_permissions


def trigger_report_run(payload: ReportRunRequest, current_user: AuthenticatedUser, db: Session):
    authorize_report(current_user, payload.report_type)
    if payload.limit > 50000 or payload.limit < 1:
        raise HTTPException(422, "El límite debe estar entre 1 y 50000 filas.")

    if payload.async_execution:
        template = next((item for item in get_report_catalog() if item["code"] == payload.report_type), None)

        if not template or payload.format not in template["formats"]:
            raise HTTPException(422, "Selecciona una plantilla y formato de reporte válidos.")

        run_id = uuid4()

        created = datetime.now(timezone.utc).isoformat()

        data = {
            "run_id": str(run_id),
            "company_id": str(current_user.company_id),
            "author_email": current_user.email,
            "report_type": payload.report_type,
            "template_code": payload.report_type,
            "parameters": payload.parameters,
            "format": payload.format,
            "status": "queued",
            "progress_percent": 0,
            "progress_pct": 0,
            "row_count": 0,
            "file_size_kb": 0,
            "sha256_hash": None,
            "cutoff_at": created,
            "created_at": created,
            "completed_at": None,
            "expires_at": None,
            "error_message": None,
        }

        db.add(
            AnalyticsArtifact(
                id=run_id,
                company_id=current_user.company_id,
                kind="report_run",
                artifact_key=str(run_id),
                version=1,
                status="queued",
                data_json=json.dumps(data),
                created_by=current_user.user_id,
            )
        )

        db.add(
            JobModel(
                id=run_id,
                company_id=current_user.company_id,
                requested_by=current_user.user_id,
                job_type="report_generate",
                status="pending",
                progress=0,
                payload_json=json.dumps(payload.model_dump(mode="json")),
            )
        )

        db.commit()

        return data

    try:
        columns, rows = execute_report_data(
            payload.report_type, current_user.company_id, db, limit=payload.limit, parameters=payload.parameters
        )

    except ValueError as e:
        raise HTTPException(400, str(e))

    run_id = uuid4()

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id))

    try:
        target, media_type, digest = write_report_artifact(
            run_id,
            current_user.company_id,
            payload.format,
            columns,
            rows,
            payload.report_type,
            payload.parameters.get("status"),
            company,
        )

    except Exception as e:
        raise HTTPException(500, f"Error en generador de reporte: {str(e)}")

    created = datetime.now(timezone.utc)

    data = {
        "run_id": str(run_id),
        "company_id": str(current_user.company_id),
        "author_email": current_user.email,
        "report_type": payload.report_type,
        "template_code": payload.report_type,
        "parameters": payload.parameters,
        "format": payload.format,
        "status": "completed",
        "progress_percent": 100,
        "progress_pct": 100,
        "row_count": len(rows),
        "columns": columns,
        "artifact_path": str(target),
        "content_type": media_type,
        "data_hash": f"sha256-{digest}",
        "sha256_hash": f"sha256-{digest}",
        "file_size_kb": round(target.stat().st_size / 1024, 2),
        "downloads_count": 0,
        "is_revoked": False,
        "created_at": created.isoformat(),
        "cutoff_at": created.isoformat(),
        "completed_at": created.isoformat(),
        "error_message": None,
        "expires_at": (created + timedelta(minutes=15)).isoformat(),
        "download_url": f"/api/v1/report-runs/{run_id}/download",
    }

    db.add(
        AnalyticsArtifact(
            id=run_id,
            company_id=current_user.company_id,
            kind="report_run",
            artifact_key=str(run_id),
            version=1,
            status="completed",
            data_json=json.dumps(data),
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return {
        key: data[key]
        for key in (
            "run_id",
            "report_type",
            "template_code",
            "format",
            "status",
            "progress_percent",
            "progress_pct",
            "row_count",
            "file_size_kb",
            "data_hash",
            "sha256_hash",
            "cutoff_at",
            "created_at",
            "completed_at",
            "expires_at",
            "error_message",
            "parameters",
            "download_url",
        )
    } | {"started_at": data["created_at"]}


def list_report_runs(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "report_run")
        .order_by(AnalyticsArtifact.created_at.desc())
    ).all()

    items = []

    for row in rows:
        data = report_run_data(row)
        if not required_report_permissions(data["report_type"]) <= set(current_user.permissions):
            continue

        data.setdefault("template_code", data.get("report_type"))

        data.setdefault("progress_pct", data.get("progress_percent", 100))

        data.setdefault("sha256_hash", data.get("data_hash"))

        data.setdefault("file_size_kb", 0)

        data.setdefault("cutoff_at", data.get("created_at"))

        data.setdefault("completed_at", data.get("created_at") if data.get("status") == "completed" else None)

        data.setdefault("error_message", None)

        data.setdefault("parameters", {})

        items.append(
            {
                key: data.get(key)
                for key in (
                    "run_id",
                    "report_type",
                    "template_code",
                    "format",
                    "status",
                    "progress_percent",
                    "progress_pct",
                    "row_count",
                    "file_size_kb",
                    "data_hash",
                    "sha256_hash",
                    "cutoff_at",
                    "author_email",
                    "downloads_count",
                    "created_at",
                    "completed_at",
                    "expires_at",
                    "error_message",
                    "parameters",
                )
            }
        )

    return {"items": items, "count": len(items)}


def get_report_run_status(run_id: UUID, current_user: AuthenticatedUser, db: Session):
    data = report_run_data(report_run_row(db, current_user.company_id, run_id))
    authorize_report(current_user, data["report_type"])

    return {
        "run_id": str(run_id),
        "report_type": data["report_type"],
        "template_code": data["report_type"],
        "status": data["status"],
        "progress_percent": data.get("progress_percent", 100),
        "progress_pct": data.get("progress_percent", 100),
        "row_count": data.get("row_count", 0),
        "data_hash": data.get("data_hash"),
        "sha256_hash": data.get("data_hash"),
        "completed_at": data.get("created_at"),
        "expires_at": data.get("expires_at"),
        "download_url": data.get("download_url"),
    }


def cancel_report_run(run_id: UUID, current_user: AuthenticatedUser, db: Session):
    job = db.scalar(
        select(JobModel).where(JobModel.id == run_id, JobModel.company_id == current_user.company_id).with_for_update()
    )

    row = report_run_row(db, current_user.company_id, run_id, True)

    data = report_run_data(row)
    authorize_report(current_user, data["report_type"])

    if data["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(409, "La ejecución ya terminó.")

    data["status"] = "cancelled"

    if job:
        job.cancel_requested = True

        if job.status == "pending":
            job.status = "cancelled"

    row.status = "cancelled"

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"run_id": str(run_id), "status": "cancelled"}


def retry_report_run(run_id: UUID, current_user: AuthenticatedUser, db: Session):
    job = db.scalar(
        select(JobModel).where(JobModel.id == run_id, JobModel.company_id == current_user.company_id).with_for_update()
    )

    row = report_run_row(db, current_user.company_id, run_id, True)

    data = report_run_data(row)
    authorize_report(current_user, data["report_type"])

    if data["status"] not in ("failed", "cancelled"):
        raise HTTPException(409, "Solo se puede reintentar una ejecución fallida o cancelada.")

    if job:
        job.status = "pending"

        job.cancel_requested = False

        job.lease_until = None

        job.attempts = 0

        job.progress = 0

        job.result = None

        data.update(
            {"status": "queued", "progress_pct": 0, "progress_percent": 0, "error_message": None, "completed_at": None}
        )

        row.data_json = json.dumps(data)

        row.status = "queued"

        db.commit()

        return data

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id))

    columns, rows = execute_report_data(
        data["report_type"], current_user.company_id, db, limit=50000, parameters=data.get("parameters", {})
    )

    target, media_type, digest = write_report_artifact(
        run_id,
        current_user.company_id,
        data["format"],
        columns,
        rows,
        data["report_type"],
        data.get("parameters", {}).get("status"),
        company,
    )

    data.update(
        {
            "status": "completed",
            "progress_percent": 100,
            "row_count": len(rows),
            "artifact_path": str(target),
            "content_type": media_type,
            "data_hash": f"sha256-{digest}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        }
    )

    row.status = "completed"

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"run_id": str(run_id), "status": "completed", "row_count": len(rows), "data_hash": data["data_hash"]}


def download_report_run(run_id: UUID, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(select(UserModel).where(UserModel.id == current_user.user_id))

    if user and not user.is_active:
        raise HTTPException(403, "Usuario suspendido o sin permisos vigentes.")

    row = report_run_row(db, current_user.company_id, run_id, True)

    data = report_run_data(row)
    authorize_report(current_user, data["report_type"])

    if data.get("is_revoked") or row.status == "revoked":
        raise HTTPException(403, "La descarga de este reporte ha sido revocada.")

    if data["status"] != "completed":
        raise HTTPException(409, "El reporte no está disponible.")

    if datetime.fromisoformat(data["expires_at"]).astimezone(timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(410, "El enlace de descarga ha expirado.")

    path = Path(data["artifact_path"]).resolve()

    expected_root = (Path(settings.private_storage_path).resolve() / "reports" / str(current_user.company_id)).resolve()

    if (
        expected_root not in path.parents
        or not path.is_file()
        or f"sha256-{hashlib.sha256(path.read_bytes()).hexdigest()}" != data["data_hash"]
    ):
        raise HTTPException(409, "El artefacto no está disponible o no supera la verificación de integridad.")

    data["downloads_count"] += 1

    row.data_json = json.dumps(data)

    db.commit()

    return FileResponse(
        path, media_type=data["content_type"], filename=f"{data['report_type']}-{run_id}.{data['format']}"
    )
