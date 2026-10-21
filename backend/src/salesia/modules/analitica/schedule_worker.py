import json
from datetime import datetime, timezone

from sqlalchemy import select

from salesia.modules.analitica.schedules import next_schedule_time
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.sessions import permissions_for
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company


def process_report_schedules(limit=20, at=None):
    from salesia.modules.analitica.application.reportes_programacion import execute_report_schedule

    current = at or datetime.now(timezone.utc)
    processed = 0
    with sync_session_factory() as db:
        company_ids = db.scalars(select(CompanyModel.id).where(CompanyModel.is_active.is_(True))).all()
    for company_id in company_ids:
        with sync_session_factory() as db:
            bind_company(db, company_id)
            schedule_ids = db.scalars(
                select(AnalyticsArtifact.id).where(
                    AnalyticsArtifact.company_id == company_id,
                    AnalyticsArtifact.kind == "report_schedule",
                    AnalyticsArtifact.status == "active",
                )
            ).all()
        for schedule_id in schedule_ids:
            with sync_session_factory() as db:
                bind_company(db, company_id)
                row = db.scalar(
                    select(AnalyticsArtifact)
                    .where(
                        AnalyticsArtifact.id == schedule_id,
                        AnalyticsArtifact.company_id == company_id,
                        AnalyticsArtifact.status == "active",
                    )
                    .with_for_update(skip_locked=True)
                )
                if not row:
                    continue
                data = json.loads(row.data_json)
                if (
                    not data.get("schedule")
                    or not data.get("next_run_at")
                    or datetime.fromisoformat(data["next_run_at"]) > current
                ):
                    continue
                owner = db.scalar(
                    select(UserModel).where(
                        UserModel.id == row.created_by,
                        UserModel.company_id == company_id,
                        UserModel.is_active.is_(True),
                    )
                )
                permissions = permissions_for(db, owner) if owner else []
                if "reports:read" not in permissions or "reports:export" not in permissions:
                    data["is_active"] = False
                    data["error_message"] = (
                        "El responsable ya no tiene permisos para generar reportes. Reasigna o recrea la programación."
                    )
                    row.status = "paused"
                    row.data_json = json.dumps(data)
                    db.commit()
                    continue
                data["next_run_at"] = next_schedule_time(data["schedule"], data["timezone"], current).isoformat()
                row.data_json = json.dumps(data)
                user = AuthenticatedUser(
                    user_id=owner.id, email=owner.email, company_id=company_id, role=owner.role, permissions=permissions
                )
                try:
                    execute_report_schedule(row.id, user, db)
                    db.commit()
                    processed += 1
                except Exception:
                    db.rollback()
                    bind_company(db, company_id)
                    failed = db.scalar(
                        select(AnalyticsArtifact)
                        .where(AnalyticsArtifact.id == schedule_id, AnalyticsArtifact.company_id == company_id)
                        .with_for_update()
                    )
                    failed_data = json.loads(failed.data_json)
                    failed_data["error_message"] = (
                        "No se pudo generar el reporte. Revisa los parámetros o ejecuta nuevamente desde Reportes."
                    )
                    failed_data["next_run_at"] = data["next_run_at"]
                    failed.data_json = json.dumps(failed_data)
                    db.add(
                        Notification(
                            company_id=company_id,
                            user_id=owner_id,
                            title="Reporte programado fallido",
                            message=failed_data["error_message"],
                            event_type="REPORT_FAILED",
                        )
                    )
                    db.commit()
                if processed >= limit:
                    return processed
    return processed
