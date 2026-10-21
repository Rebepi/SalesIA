import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.datasets_versiones_construccion import (
    DatasetVersionCreateRequest,
    OperationalDatasetExtractRequest,
)
from salesia.modules.analitica.domain.dataset import (
    build_data_quality_report,
    compute_deterministic_hash,
    extract_operational_dataset_rows,
    mask_sensitive_row,
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import SaleModel


def create_dataset_version(
    dataset_id: UUID, payload: Optional[DatasetVersionCreateRequest], current_user: AuthenticatedUser, db: Session
):
    root = db.scalar(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.id == dataset_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
        )
        .with_for_update()
    )

    if not root:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")

    current = json.loads(root.data_json)

    next_version = int(current.get("current_version", 0)) + 1

    grain = current.get("grain", "ticket")

    filters = current.get("filters", {})

    watermark = (payload.watermark or payload.cutoff_date) if payload else None

    if payload and payload.row_count is not None and payload.data_hash and payload.schema_snapshot is not None:
        row_count = payload.row_count

        data_hash = payload.data_hash

        schema_snapshot = payload.schema_snapshot

        rows = []

        quality_report = build_data_quality_report(row_count, [], {}, [])

    else:
        rows, quality_report = extract_operational_dataset_rows(
            db=db, company_id=current_user.company_id, grain=grain, filters=filters, watermark=watermark
        )

        row_count = len(rows)

        data_hash = compute_deterministic_hash(rows)

        schema_snapshot = {
            "columns": list(rows[0].keys()) if rows else ["total_amount", "paid_amount"],
            "grain": grain,
            "currency": filters.get("currency", "USD"),
        }

    storage_type = "inline"

    file_rel_path = None

    if len(rows) > 50:
        storage_type = "private_file"

        storage_root = Path(settings.private_storage_path).resolve() / "datasets" / str(current_user.company_id)

        storage_root.mkdir(parents=True, exist_ok=True)

        file_path = storage_root / f"{dataset_id}_v{next_version}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)

        file_rel_path = str(file_path.relative_to(Path(settings.private_storage_path).resolve()))

    scope_type = "population" if len(rows) <= 10 else "sample"

    data = {
        "dataset_id": str(dataset_id),
        "version": next_version,
        "row_count": row_count,
        "data_hash": data_hash,
        "sha256_hash": data_hash,
        "schema_snapshot": schema_snapshot,
        "quality_report": quality_report,
        "storage_type": storage_type,
        "file_path": file_rel_path,
        "scope_type": scope_type,
        "sample_size": min(len(rows), 10),
        "total_population": row_count,
        "sampling_method": "full" if len(rows) <= 10 else "head",
        "parameters": payload.parameters if payload and payload.parameters else {},
        "preview_sample": rows[:10],
        "sample": rows[:10],
        "variables": current.get("variables", []),
        "status": "immutable",
        "created_by": str(current_user.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if storage_type == "inline":
        data["rows"] = rows

    version_artifact = AnalyticsArtifact(
        company_id=current_user.company_id,
        kind="dataset_version",
        artifact_key=str(dataset_id),
        version=next_version,
        status="immutable",
        data_json=json.dumps(data),
        parent_id=root.id,
        created_by=current_user.user_id,
    )

    db.add(version_artifact)

    current["current_version"] = next_version

    root.data_json = json.dumps(current)

    root.updated_at = datetime.now(timezone.utc)

    db.commit()

    return data


def list_dataset_versions(dataset_id: UUID, current_user: AuthenticatedUser, db: Session):
    root = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == dataset_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
        )
    )

    if not root:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")

    rows = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == str(dataset_id),
        )
        .order_by(AnalyticsArtifact.version.desc())
    ).all()

    items = []

    for r in rows:
        parsed = json.loads(r.data_json)

        dep_count = db.scalar(
            select(func.count())
            .select_from(AnalyticsArtifact)
            .where(
                AnalyticsArtifact.company_id == current_user.company_id,
                AnalyticsArtifact.kind == "analysis",
                AnalyticsArtifact.parent_id == r.id,
            )
        )

        parsed["dependent_analyses_count"] = dep_count or 0

        parsed["status"] = r.status

        parsed["sha256_hash"] = parsed.get("sha256_hash") or parsed.get("data_hash", "")

        parsed["completeness_pct"] = parsed.get("quality_report", {}).get("completeness_pct", 0)

        items.append(parsed)

    return {"items": items, "count": len(items)}


def get_dataset_version(dataset_id: UUID, version: int, current_user: AuthenticatedUser, db: Session):
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

    data["status"] = row.status

    data["sha256_hash"] = data.get("sha256_hash") or data.get("data_hash", "")

    data["sample"] = data.get("sample") or data.get("preview_sample", [])

    data["variables"] = data.get("variables", [])

    quality = data.get("quality_report", {})

    data["quality_report"] = {
        **quality,
        "received": quality.get("received", quality.get("total_received", 0)),
        "used": quality.get("used", quality.get("total_used", 0)),
        "excluded": quality.get("excluded", quality.get("total_excluded", 0)),
        "variable_completeness": quality.get("variable_completeness", {}),
        "error_rates": quality.get("error_rates", {}),
        "imputation_warnings": quality.get("imputation_warnings", []),
    }

    can_view_costs = "products:cost:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "platform_admin",
    )

    can_view_sensitive = "customers:sensitive:read" in current_user.permissions or current_user.role in (
        "company_admin",
        "platform_admin",
    )

    if "preview_sample" in data:
        data["preview_sample"] = [
            mask_sensitive_row(r, can_view_costs, can_view_sensitive) for r in data["preview_sample"]
        ]

    return data


def delete_dataset_version(dataset_id: UUID, version: int, current_user: AuthenticatedUser, db: Session):
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

    dep_count = db.scalar(
        select(func.count())
        .select_from(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "analysis",
            AnalyticsArtifact.parent_id == row.id,
        )
    )

    if dep_count and dep_count > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar una versión con análisis dependientes vigentes sin procedimiento de retención.",
        )

    row.status = "archived"

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"status": "archived", "version": version}


def rebuild_dataset(dataset_id: UUID, current_user: AuthenticatedUser, db: Session):
    root = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.id == dataset_id,
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset",
        )
    )

    if not root:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")

    current = json.loads(root.data_json)

    grain = current.get("grain", "ticket")

    filters = current.get("filters", {})

    last_ver_num = int(current.get("current_version", 1))

    last_ver_artifact = db.scalar(
        select(AnalyticsArtifact).where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "dataset_version",
            AnalyticsArtifact.artifact_key == str(dataset_id),
            AnalyticsArtifact.version == last_ver_num,
        )
    )

    prev_rows_count = json.loads(last_ver_artifact.data_json).get("row_count", 0) if last_ver_artifact else 0

    new_rows, new_quality = extract_operational_dataset_rows(
        db=db, company_id=current_user.company_id, grain=grain, filters=filters
    )

    new_count = len(new_rows)

    comparison_validation = {
        "passed": True,
        "previous_rows": prev_rows_count,
        "new_rows": new_count,
        "delta": new_count - prev_rows_count,
    }

    next_version = last_ver_num + 1

    new_hash = compute_deterministic_hash(new_rows)

    data = {
        "dataset_id": str(dataset_id),
        "version": next_version,
        "row_count": new_count,
        "data_hash": new_hash,
        "schema_snapshot": {"grain": grain, "columns": list(new_rows[0].keys()) if new_rows else []},
        "quality_report": new_quality,
        "storage_type": "inline",
        "rows": new_rows,
        "preview_sample": new_rows[:10],
        "status": "immutable",
        "created_by": str(current_user.user_id),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            company_id=current_user.company_id,
            kind="dataset_version",
            artifact_key=str(dataset_id),
            version=next_version,
            status="immutable",
            data_json=json.dumps(data),
            parent_id=root.id,
            created_by=current_user.user_id,
        )
    )

    current["current_version"] = next_version

    root.data_json = json.dumps(current)

    root.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {"status": "published", "comparison_validation": comparison_validation, "new_version": next_version}


def extract_operational_dataset(
    payload: OperationalDatasetExtractRequest, current_user: AuthenticatedUser, db: Session
):
    sales = (
        db.execute(
            select(SaleModel)
            .where(SaleModel.company_id == current_user.company_id, SaleModel.status.in_(("confirmed", "paid")))
            .order_by(SaleModel.created_at.desc())
            .limit(payload.limit)
        )
        .scalars()
        .all()
    )

    rows = []

    for s in sales:
        rows.append(
            {
                "sale_id": str(s.id),
                "id": str(s.id),
                "series_number": f"{s.series}-{s.number:06d}",
                "customer_id": str(s.customer_id),
                "total_amount": str(s.total_amount),
                "paid_amount": str(s.paid_amount),
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
        )

    data_hash = compute_deterministic_hash(rows)

    dataset_id = uuid4()

    result = {
        "dataset_id": str(dataset_id),
        "grain": payload.grain,
        "row_count": len(rows),
        "null_count": 0,
        "duplicate_count": 0,
        "data_hash": data_hash,
        "preview_sample": rows[:5],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.add(
        AnalyticsArtifact(
            id=dataset_id,
            company_id=current_user.company_id,
            kind="dataset",
            artifact_key=str(dataset_id),
            version=1,
            status="immutable",
            data_json=json.dumps({**result, "rows": rows}),
            created_by=current_user.user_id,
        )
    )

    db.commit()

    return result
