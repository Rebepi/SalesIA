import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.auxiliares.write_report_artifact import write_report_artifact
from salesia.modules.analitica.application.contracts.reportes_programacion import ReportScheduleCreateRequest
from salesia.modules.analitica.domain.reports import execute_report_data, get_report_catalog
from salesia.modules.analitica.schedules import next_schedule_time, validate_schedule_zone
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.modules.analitica.application.reportes.operativos import OPERATIONAL_REPORTS, authorize_report, required_report_permissions
from salesia.modules.operaciones.infrastructure_models import Notification
from salesia.modules.seguridad.infrastructure.sessions import permissions_for


def internal_report_recipients(db, user, report_type, emails):
    addresses = {str(value).lower() for value in emails}
    if not addresses:
        addresses = {user.email.lower()}
    members = db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.is_active.is_(True), func.lower(UserModel.email).in_(addresses))).all()
    if len(members) != len(addresses):
        raise HTTPException(422, "Selecciona correos de miembros activos de esta empresa; los reportes se entregan en la bandeja interna.")
    for member in members:
        permissions = permissions_for(db, member)
        if "reports:read" not in permissions or not required_report_permissions(report_type) <= set(permissions):
            raise HTTPException(422, f"El destinatario {member.email} no tiene acceso a este reporte.")
    return [str(member.id) for member in members]


def create_report_schedule(payload: ReportScheduleCreateRequest, current_user: AuthenticatedUser, db: Session):
    authorize_report(current_user, payload.report_type)
    catalog = next((item for item in get_report_catalog() if item["code"] == payload.report_type), None)

    if not catalog or "reports:read" not in current_user.permissions:
        raise HTTPException(403, "No tiene permiso para programar este reporte.")

    if payload.format not in catalog["formats"]:
        raise HTTPException(422, "El formato no está disponible para este reporte.")

    try:
        validate_schedule_zone(payload.timezone)

    except ValueError as failure:
        raise HTTPException(422, str(failure))

    if payload.schedule:
        payload.cron_expression = payload.schedule.cron()

    if len(payload.cron_expression.split()) != 5:
        raise HTTPException(422, "La expresión cron debe contener cinco campos.")

    schedule_id = uuid4()

    data = {
        "version": 1,
        "recipient_user_ids": internal_report_recipients(db, current_user, payload.report_type, payload.recipients),
        "schedule_id": str(schedule_id),
        "company_id": str(current_user.company_id),
        "report_type": payload.report_type,
        "template_code": payload.report_type,
        "cron_expression": payload.cron_expression,
        "format": payload.format,
        "recipients": payload.recipients,
        "recipient_emails": payload.recipients,
        "timezone": payload.timezone,
        "schedule": payload.schedule.model_dump(mode="json") if payload.schedule else None,
        "next_run_at": next_schedule_time(
            payload.schedule.model_dump(mode="json"), payload.timezone, datetime.now(timezone.utc)
        ).isoformat()
        if payload.schedule
        else None,
        "created_by": current_user.email,
        "is_active": True,
        "runs_count": 0,
        "last_run_at": None,
        "last_run_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            id=schedule_id,
            company_id=current_user.company_id,
            kind="report_schedule",
            artifact_key=str(schedule_id),
            version=1,
            status="active",
            data_json=json.dumps(data),
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return data


def execute_report_schedule(schedule_id: UUID, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(select(UserModel).where(UserModel.id == current_user.user_id))

    if user and not user.is_active:
        raise HTTPException(403, "Usuario suspendido o sin permisos vigentes.")

    row = db.scalar(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id == schedule_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "report_schedule",
            AnalyticsArtifact.status.in_(("active", "paused")),
        )
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Programación no encontrada o inactiva.")

    sdata = json.loads(row.data_json)
    authorize_report(current_user, sdata["report_type"])

    columns, rows = execute_report_data(sdata["report_type"], current_user.company_id, db, limit=50000)

    run_id = uuid4()

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id))

    target, media_type, digest = write_report_artifact(
        run_id, current_user.company_id, sdata["format"], columns, rows, sdata["report_type"], None, company
    )

    created = datetime.now(timezone.utc)

    run_data = {
        "run_id": str(run_id),
        "company_id": str(current_user.company_id),
        "author_email": current_user.email,
        "report_type": sdata["report_type"],
        "template_code": sdata["report_type"],
        "parameters": {},
        "format": sdata["format"],
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
        "expires_at": (created + timedelta(days=7)).isoformat(),
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
            data_json=json.dumps(run_data),
            created_by=current_user.user_id,
        )
    )

    sdata["runs_count"] = sdata.get("runs_count", 0) + 1

    sdata["last_run_at"] = created.isoformat()

    sdata["last_run_id"] = str(run_id)

    row.data_json = json.dumps(sdata)

    row.updated_at = created

    recipient_ids = set(sdata.get("recipient_user_ids", [])) | {str(row.created_by)}
    for identifier in recipient_ids:
        recipient = db.scalar(select(UserModel).where(UserModel.company_id == current_user.company_id, UserModel.id == UUID(identifier), UserModel.is_active.is_(True)))
        if recipient is None:
            continue
        permissions = permissions_for(db, recipient)
        if "reports:read" not in permissions or not required_report_permissions(sdata["report_type"]) <= set(permissions):
            continue
        db.add(Notification(company_id=current_user.company_id, user_id=recipient.id, title="Reporte programado disponible", message=f"{sdata['report_type']} finalizó. Consulta su archivo desde Reportes.", event_type="REPORT_COMPLETED", category="operations", resource_type="report_run", resource_id=run_id))

    db.commit()

    return run_data


def list_report_schedules(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "report_schedule",
            AnalyticsArtifact.status.in_(["active", "paused"]),
        )
        .order_by(AnalyticsArtifact.created_at.desc())
    ).all()

    items = []

    for row in rows:
        data = json.loads(row.data_json)
        if not required_report_permissions(data["report_type"]) <= set(current_user.permissions):
            continue

        data.setdefault("template_code", data.get("report_type"))

        data.setdefault("recipient_emails", data.get("recipients", []))
        data["version"] = row.version

        items.append(data)

    return {"items": items, "count": len(items)}


def update_report_schedule(schedule_id, payload, current_user, db):
    row = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.id == schedule_id, AnalyticsArtifact.kind == "report_schedule", AnalyticsArtifact.status.in_(("active", "paused"))).with_for_update())
    if row is None:
        raise HTTPException(404, "Programación no encontrada.")
    if row.created_by != current_user.user_id and "operations:manage" not in current_user.permissions and "organization:manage" not in current_user.permissions:
        raise HTTPException(403, "Solo el responsable o un administrador puede cambiar la programación.")
    if row.version != payload.version:
        raise HTTPException(409, "La programación cambió; recarga antes de guardarla.")
    data = json.loads(row.data_json)
    authorize_report(current_user, data["report_type"])
    if payload.format:
        template = next((item for item in get_report_catalog() if item["code"] == data["report_type"]), None)
        if not template or payload.format not in template["formats"]:
            raise HTTPException(422, "Formato de reporte no disponible.")
        data["format"] = payload.format
    if payload.timezone:
        try:
            validate_schedule_zone(payload.timezone)
        except ValueError as failure:
            raise HTTPException(422, str(failure))
        data["timezone"] = payload.timezone
    if payload.schedule:
        data["schedule"] = payload.schedule.model_dump(mode="json")
        data["cron_expression"] = payload.schedule.cron()
    if payload.recipients is not None:
        data["recipient_user_ids"] = internal_report_recipients(db, current_user, data["report_type"], payload.recipients)
        data["recipients"] = [str(value) for value in payload.recipients]
        data["recipient_emails"] = data["recipients"]
    if payload.is_active is not None:
        data["is_active"] = payload.is_active
        row.status = "active" if payload.is_active else "paused"
    if data.get("schedule"):
        data["next_run_at"] = next_schedule_time(data["schedule"], data["timezone"], datetime.now(timezone.utc)).isoformat()
    row.version += 1
    data["version"] = row.version
    row.data_json = json.dumps(data)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return data


def delete_report_schedule(schedule_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id == schedule_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "report_schedule",
        )
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Programación no encontrada.")

    row.status = "deleted"

    data = json.loads(row.data_json)

    data["is_active"] = False

    row.data_json = json.dumps(data)

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"deleted": True, "schedule_id": str(schedule_id)}
