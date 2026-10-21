import hashlib
import json
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from salesia.modules.analitica.application.reportes.formatos import (
    build_csv_content,
    build_pdf_content,
    build_xlsx_content,
)


def write_report_artifact_v2(
    run_id: UUID,
    company_id: UUID,
    report_format: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    report_type: str,
    storage_root_path: str,
    branding: dict[str, Any],
    status_condition: Optional[str] = None,
) -> tuple[Path, str, str]:
    root = (Path(storage_root_path).resolve() / "reports" / str(company_id)).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if report_format == "csv":
        content = build_csv_content(columns, rows)
        extension, media_type = "csv", "text/csv; charset=utf-8"
    elif report_format == "json":
        content = json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        extension, media_type = "json", "application/json"
    elif report_format == "xlsx":
        content = build_xlsx_content(columns, rows, report_type)
        extension, media_type = "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif report_format == "pdf":
        content = build_pdf_content(columns, rows, report_type, branding, status_condition)
        extension, media_type = "pdf", "application/pdf"
    else:
        raise ValueError(f"Formato no soportado: {report_format}")

    target = root / f"{run_id}.{extension}"
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(target)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    digest = hashlib.sha256(content).hexdigest()
    return target, media_type, digest
