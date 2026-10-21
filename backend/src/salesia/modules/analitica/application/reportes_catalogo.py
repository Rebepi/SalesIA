from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.auxiliares.report_run_data import report_run_data
from salesia.modules.analitica.application.auxiliares.report_run_row import report_run_row
from salesia.modules.analitica.application.contracts.reportes_catalogo import ReportCompareRequest
from salesia.modules.analitica.domain.reports import execute_report_data, get_report_catalog, sanitize_branding_payload
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel
from salesia.modules.analitica.application.reportes.operativos import authorize_report, required_report_permissions


def list_reports(area: Optional[str], format: Optional[str], current_user: AuthenticatedUser):
    items = []

    for report in get_report_catalog(area=area, format_type=format):
        if not required_report_permissions(report["code"]) <= set(current_user.permissions):
            continue
        if report.get("required_permission") and report["required_permission"] not in current_user.permissions:
            continue
        item = dict(report)

        item["allowed_formats"] = report["formats"]

        item["status_filter_support"] = report["status_filter"]

        item["required_permission"] = report.get("required_permission", "reports:read")

        item["schema_summary"] = {"columns": list(report["parameters_schema"].keys()), "grain": report["description"]}

        items.append(item)

    return {"items": items, "count": len(items)}


def get_report_preview(
    report_type: Optional[str], template_code: Optional[str], limit: int, current_user: AuthenticatedUser, db: Session
):
    selected_report_type = report_type or template_code

    if not selected_report_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Debe indicar report_type o template_code."
        )

    authorize_report(current_user, selected_report_type)

    try:
        columns, rows = execute_report_data(selected_report_type, current_user.company_id, db, limit=50)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    est_size = round(max(len(rows) * len(columns) * 0.08, 1.5), 2)

    return {
        "report_type": selected_report_type,
        "template_code": selected_report_type,
        "estimated_total_rows": len(rows),
        "estimated_row_count": len(rows),
        "estimated_file_size_kb": est_size,
        "columns": columns,
        "preview_sample": rows[:limit],
        "sample_rows": rows[:limit],
        "cutoff_at": datetime.now(timezone.utc).isoformat(),
        "authorized": True,
        "filters_applied": {"limit": limit},
        "allowed_formats": ["csv", "xlsx", "pdf", "json"],
    }


def compare_reports(payload: ReportCompareRequest, current_user: AuthenticatedUser, db: Session):
    first = report_run_data(report_run_row(db, current_user.company_id, payload.run_id_1))

    second = report_run_data(report_run_row(db, current_user.company_id, payload.run_id_2))
    authorize_report(current_user, first["report_type"])
    authorize_report(current_user, second["report_type"])

    if first["report_type"] != second["report_type"]:
        raise HTTPException(400, "Solo se pueden comparar ejecuciones del mismo tipo.")

    dt1 = datetime.fromisoformat(first["created_at"])

    dt2 = datetime.fromisoformat(second["created_at"])

    cutoff_delta = abs(int((dt2 - dt1).total_seconds()))

    return {
        "comparison_id": str(uuid4()),
        "report_type": first["report_type"],
        "run_id_1": str(payload.run_id_1),
        "run_id_2": str(payload.run_id_2),
        "run_1_row_count": first["row_count"],
        "run_2_row_count": second["row_count"],
        "row_count_delta": second["row_count"] - first["row_count"],
        "is_identical": first["data_hash"] == second["data_hash"],
        "cutoff_delta_seconds": cutoff_delta,
        "compatibility_note": "Cortes temporales comparados consistentemente",
        "report_a": {
            "run_id": str(payload.run_id_1),
            "row_count": first["row_count"],
            "sha256_hash": first["data_hash"],
            "cutoff_at": first["created_at"],
        },
        "report_b": {
            "run_id": str(payload.run_id_2),
            "row_count": second["row_count"],
            "sha256_hash": second["data_hash"],
            "cutoff_at": second["created_at"],
        },
        "identical_hash": first["data_hash"] == second["data_hash"],
        "rows_delta": second["row_count"] - first["row_count"],
        "same_cutoff_window": cutoff_delta == 0,
    }


def get_report_branding(current_user: AuthenticatedUser, db: Session):
    company = db.execute(select(CompanyModel).where(CompanyModel.id == current_user.company_id)).scalar_one_or_none()

    if not company:
        raise HTTPException(404, "Empresa no encontrada.")

    return sanitize_branding_payload(company)
