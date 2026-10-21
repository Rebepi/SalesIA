import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.procesamiento_trabajos.importaciones import execute_import
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact, Notification
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import BackupSnapshotModel, CompanyModel, JobModel, UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company
from salesia.shared.infrastructure.workers import TenantFairnessLimiter, is_transient_error, record_dead_letter_job


def now():
    return datetime.now(timezone.utc)


def claim_job(db: Session):
    limiter = TenantFairnessLimiter(max_concurrent_per_tenant=2)
    company_ids = db.scalars(
        select(CompanyModel.id).where(CompanyModel.is_active.is_(True)).order_by(CompanyModel.id)
    ).all()
    for company_id in company_ids:
        bind_company(db, company_id)
        db.execute(
            update(JobModel)
            .where(
                JobModel.company_id == company_id,
                JobModel.status == "running",
                JobModel.lease_until.is_not(None),
                JobModel.lease_until < now(),
            )
            .values(status="pending", lease_until=None)
        )
        candidates = db.scalars(
            select(JobModel)
            .where(JobModel.company_id == company_id, JobModel.status == "pending")
            .order_by(JobModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(20)
        ).all()
        for candidate in candidates:
            if candidate.cancel_requested:
                candidate.status = "cancelled"
                candidate.progress = 0
                continue
            if limiter.can_schedule_job(db, candidate.company_id):
                candidate.status = "running"
                candidate.progress = 1
                candidate.attempts += 1
                candidate.lease_until = now() + timedelta(minutes=10)
                if candidate.job_type == "report_generate":
                    artifact = db.scalar(
                        select(AnalyticsArtifact)
                        .where(
                            AnalyticsArtifact.id == candidate.id, AnalyticsArtifact.company_id == candidate.company_id
                        )
                        .with_for_update()
                    )
                    if artifact:
                        data = json.loads(artifact.data_json)
                        data.update({"status": "processing", "progress_percent": 1, "progress_pct": 1})
                        artifact.status = "processing"
                        artifact.data_json = json.dumps(data)
                db.flush()
                return candidate
    return None


def pg_dump_path():
    located = shutil.which("pg_dump")
    if located:
        return located
    root = Path("C:/Program Files/PostgreSQL")
    candidates = sorted(root.glob("*/bin/pg_dump.exe"), reverse=True)
    if not candidates:
        raise RuntimeError("pg_dump no está instalado")
    return str(candidates[0])


def database_backup():
    url = (settings.backup_database_url or settings.database_url).replace("+asyncpg", "").replace("+aiosqlite", "")
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "database.dump"
        if url.startswith("sqlite"):
            source = url.split("///", 1)[1]
            source_path = Path(source).resolve()
            origin = sqlite3.connect(source_path)
            destination = sqlite3.connect(str(target))
            try:
                origin.backup(destination)
            finally:
                destination.close()
                origin.close()
        else:
            parsed = urlsplit(url)
            username = parsed.username or ""
            hostname = parsed.hostname or ""
            port = parsed.port or 5432
            database = parsed.path.lstrip("/")
            safe_host = f"{hostname}:{port}"
            safe_url = urlunsplit((parsed.scheme, safe_host, f"/{database}", parsed.query, parsed.fragment))
            environment = os.environ.copy()
            if parsed.password:
                environment["PGPASSWORD"] = parsed.password
            command = [
                pg_dump_path(),
                "--format=custom",
                "--no-owner",
                "--no-acl",
                "--file",
                str(target),
                "--dbname",
                safe_url,
            ]
            if username:
                command.extend(["--username", username])
            subprocess.run(command, check=True, timeout=900, capture_output=True, env=environment)
        return target.read_bytes()


def execute_backup(db, job):
    if not settings.backup_encryption_key:
        raise RuntimeError("BACKUP_ENCRYPTION_KEY no está configurada")
    clear = database_backup()
    snapshot_id = f"backup-{now().strftime('%Y%m%dT%H%M%SZ')}-{job.id.hex[:8]}"
    nonce = os.urandom(12)
    key = hashlib.sha256(settings.backup_encryption_key.encode()).digest()
    encrypted = AESGCM(key).encrypt(nonce, clear, snapshot_id.encode())
    root = Path(settings.private_storage_path).resolve() / "backups"
    root.mkdir(parents=True, exist_ok=True)
    target = (root / f"{snapshot_id}.aesgcm").resolve()
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(encrypted)
    os.replace(temporary, target)
    checksum = hashlib.sha256(encrypted).hexdigest()
    snapshot = BackupSnapshotModel(
        company_id=job.company_id,
        snapshot_id=snapshot_id,
        status="completed",
        encrypted=True,
        checksum=checksum,
        size_bytes=len(encrypted),
        artifact_path=str(target),
        nonce=nonce.hex(),
        source_revision=settings.source_revision,
    )
    db.add(snapshot)
    return {
        "snapshot_id": snapshot_id,
        "checksum": checksum,
        "size_bytes": len(encrypted),
        "source_revision": settings.source_revision,
    }


def execute_report_job(db, job):
    from salesia.modules.analitica.application.auxiliares.write_report_artifact import write_report_artifact
    from salesia.modules.analitica.application.reportes.datos import execute_report_data
    from salesia.modules.seguridad.infrastructure.sessions import permissions_for

    owner = db.scalar(
        select(UserModel).where(
            UserModel.id == job.requested_by, UserModel.company_id == job.company_id, UserModel.is_active.is_(True)
        )
    )
    if not owner or not {"reports:read", "reports:export"} <= set(permissions_for(db, owner)):
        raise ValueError("El responsable ya no tiene permiso para generar este reporte.")
    payload = json.loads(job.payload_json)
    from salesia.modules.analitica.application.reportes.operativos import required_report_permissions
    if not required_report_permissions(payload["report_type"]) <= set(permissions_for(db, owner)):
        raise ValueError("El responsable ya no tiene acceso a los datos del reporte.")
    artifact = db.scalar(
        select(AnalyticsArtifact)
        .where(AnalyticsArtifact.id == job.id, AnalyticsArtifact.company_id == job.company_id)
        .with_for_update()
    )
    if not artifact or artifact.status == "cancelled" or job.cancel_requested:
        raise InterruptedError("Cancelado por el usuario")
    columns, rows = execute_report_data(
        payload["report_type"],
        job.company_id,
        db,
        limit=payload.get("limit", 50000),
        parameters=payload.get("parameters", {}),
    )
    company = db.scalar(select(CompanyModel).where(CompanyModel.id == job.company_id))
    target, media_type, digest = write_report_artifact(
        job.id,
        job.company_id,
        payload["format"],
        columns,
        rows,
        payload["report_type"],
        payload.get("parameters", {}).get("status"),
        company,
    )
    data = json.loads(artifact.data_json)
    data.update(
        {
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
            "completed_at": now().isoformat(),
            "expires_at": (now() + timedelta(minutes=15)).isoformat(),
            "error_message": None,
            "download_url": f"/api/v1/report-runs/{job.id}/download",
        }
    )
    artifact.status = "completed"
    artifact.data_json = json.dumps(data)
    return {"run_id": str(job.id), "row_count": len(rows)}


def mark_report_failure(db, job):
    if job.job_type != "report_generate":
        return
    artifact = db.scalar(
        select(AnalyticsArtifact)
        .where(AnalyticsArtifact.id == job.id, AnalyticsArtifact.company_id == job.company_id)
        .with_for_update()
    )
    if artifact:
        data = json.loads(artifact.data_json)
        data["status"] = "failed" if job.status == "failed" else "cancelled" if job.status == "cancelled" else "queued"
        data["error_message"] = (
            "No se pudo generar el reporte. Revisa los filtros, permisos y configuración. Puedes volver a intentar desde el historial."
            if job.status == "failed"
            else None
        )
        artifact.status = data["status"]
        artifact.data_json = json.dumps(data)


def process_one():
    job_id = None
    company_id = None
    with sync_session_factory() as db:
        job = claim_job(db)
        if not job:
            db.commit()
            return False
        job_id = job.id
        company_id = job.company_id
        db.commit()
    try:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            job_type = db.scalar(select(JobModel.job_type).where(JobModel.id == job_id, JobModel.company_id == company_id))
            if job_type and job_type.startswith("import:"):
                db.scalar(select(CompanyModel).where(CompanyModel.id == company_id).with_for_update())
            job = db.scalar(select(JobModel).where(JobModel.id == job_id).with_for_update())
            if job is None or job.cancel_requested or job.status != "running":
                return True
            result = (
                execute_backup(db, job)
                if job.job_type == "backup"
                else execute_report_job(db, job)
                if job.job_type == "report_generate"
                else execute_import(db, job)
            )
            job.status = "completed"
            job.progress = 100
            job.result = json.dumps({**json.loads(job.result or "{}"), **result})
            job.lease_until = None
            if job.requested_by:
                db.add(
                    Notification(
                        company_id=job.company_id,
                        user_id=job.requested_by,
                        title="Trabajo completado",
                        message=f"{job.job_type} finalizó correctamente.",
                        event_type="JOB_COMPLETED",
                    )
                )
            db.commit()
    except InterruptedError as exc:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            job = db.get(JobModel, job_id)
            job.status = "cancelled"
            job.result = json.dumps({"detail": str(exc)})
            job.lease_until = None
            mark_report_failure(db, job)
            db.commit()
    except Exception as exc:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            job = db.get(JobModel, job_id)
            if job:
                transient = is_transient_error(exc)
                if transient and job.attempts < 3:
                    job.status = "pending"
                    job.lease_until = None
                else:
                    job.status = "failed"
                    job.result = json.dumps({"detail": str(exc)[:1000]})
                    job.lease_until = None
                    payload_data = {}
                    try:
                        payload_data = json.loads(job.payload_json or "{}")
                    except Exception:
                        pass
                    record_dead_letter_job(db, job.company_id, job.id, job.job_type, exc, job.attempts, payload_data)
                if job.requested_by and job.status == "failed":
                    db.add(
                        Notification(
                            company_id=job.company_id,
                            user_id=job.requested_by,
                            title="Trabajo fallido",
                            message="La operación no pudo completarse. Revisa el detalle del trabajo.",
                            event_type="JOB_FAILED",
                        )
                    )
                mark_report_failure(db, job)
            db.commit()
    return True


def process_jobs(limit=100):
    processed = 0
    while processed < limit and process_one():
        processed += 1
    return processed
