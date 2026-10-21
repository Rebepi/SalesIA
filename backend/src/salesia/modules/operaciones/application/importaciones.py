import csv
import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.job_response import job_response
from salesia.modules.operaciones.application.contracts.importaciones import ImportJobCreateRequest
from salesia.modules.operaciones.import_files import read_import_file
from salesia.modules.operaciones.infrastructure_models import UploadGrant
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import AttachmentModel, JobModel, ProductModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def inspect_import(payload: ImportJobCreateRequest, current_user: AuthenticatedUser, db: Session):
    permission = {
        "customers": "customers:write",
        "products": "products:write",
        "inventory_adjustments": "inventory:write",
    }[payload.target_entity]

    if permission not in current_user.permissions:
        raise DomainForbiddenException("No tiene permiso para esta importación.")

    attachment = db.scalar(
        select(AttachmentModel).where(
            AttachmentModel.id == payload.attachment_id,
            AttachmentModel.company_id == current_user.company_id,
            AttachmentModel.verified.is_(True),
            AttachmentModel.mime_type == "text/csv",
        )
    )

    grant = db.get(UploadGrant, attachment.id) if attachment else None

    if not grant:
        raise HTTPException(422, "Adjunto CSV inexistente o no verificado.")

    try:
        rows, columns, detected = read_import_file(grant.storage_path, payload.delimiter, payload.encoding)

    except (OSError, UnicodeError, csv.Error, ValueError) as failure:
        raise HTTPException(422, f"No se pudo leer el CSV. {failure}")

    return {"columns": columns, "preview": rows[:10], "total_rows": len(rows), **detected}


def create_import_job(
    payload: ImportJobCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    required_permission = {
        "customers": "customers:write",
        "products": "products:write",
        "inventory_adjustments": "inventory:write",
    }[payload.target_entity]

    if required_permission not in current_user.permissions:
        raise DomainForbiddenException(f"Falta el permiso {required_permission}.")

    record, cached = claim_request(
        db, current_user.company_id, "imports.stage", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    attachment = db.scalar(
        select(AttachmentModel).where(
            AttachmentModel.id == payload.attachment_id,
            AttachmentModel.company_id == current_user.company_id,
            AttachmentModel.verified.is_(True),
            AttachmentModel.mime_type == "text/csv",
        )
    )

    grant = db.get(UploadGrant, payload.attachment_id)

    if not attachment or not grant:
        other = db.scalar(select(AttachmentModel.id).where(AttachmentModel.id == payload.attachment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(422, "Adjunto CSV inexistente o no verificado.")

    try:
        rows, columns, detected = read_import_file(
            grant.storage_path, payload.delimiter, payload.encoding, payload.column_mapping, payload.corrections
        )

    except (OSError, UnicodeError, csv.Error, ValueError) as failure:
        raise HTTPException(422, f"No se pudo leer el CSV. {failure}")

    if not rows or len(rows) > 100_000:
        raise HTTPException(422, "El CSV debe contener entre 1 y 100000 filas.")

    required = {
        "customers": {"code", "doc_type", "doc_number", "legal_name"},
        "products": {"sku", "name", "category", "unit_of_measure", "unit_price", "unit_cost", "tax_rate"},
        "inventory_adjustments": {"warehouse_code", "product_sku", "quantity_delta", "reason", "unit_cost"},
    }[payload.target_entity]

    if not required <= set(columns):
        raise HTTPException(422, f"Faltan columnas: {', '.join(sorted(required - set(columns)))}")

    if payload.source_import_id:
        source_job = db.scalar(
            select(JobModel)
            .where(
                JobModel.id == payload.source_import_id,
                JobModel.company_id == current_user.company_id,
                JobModel.requested_by == current_user.user_id,
                JobModel.job_type == f"import:{payload.target_entity}",
            )
            .with_for_update()
        )

        if not source_job or source_job.status != "staged":
            raise HTTPException(409, "Solo se puede corregir una simulación propia que todavía no se haya ejecutado.")

        if json.loads(source_job.payload_json or "{}").get("attachment_id") != str(payload.attachment_id):
            raise HTTPException(422, "Las correcciones deben pertenecer al archivo de la simulación original.")

        source_job.status = "superseded"

    row_errors = []

    seen_keys = set()

    for idx, row in enumerate(rows, 1):
        missing_required = False

        for col in required:
            val = (row.get(col) or "").strip()

            if not val:
                row_errors.append({"row": idx, "column": col, "error": f"Fila {idx}: campo requerido '{col}' vacío"})

                missing_required = True

        if missing_required:
            continue

        if payload.target_entity == "customers":
            key = (row.get("doc_type", "").strip(), row.get("doc_number", "").strip())

            if key in seen_keys:
                row_errors.append(
                    {"row": idx, "column": "doc_number", "error": f"Fila {idx}: documento duplicado en el archivo"}
                )

            seen_keys.add(key)

            try:
                credit_limit = Decimal((row.get("credit_limit") or "0").strip())

                if credit_limit < 0:
                    row_errors.append(
                        {
                            "row": idx,
                            "column": "credit_limit",
                            "error": f"Fila {idx}: el límite de crédito no puede ser negativo",
                        }
                    )

            except Exception:
                row_errors.append(
                    {"row": idx, "column": "credit_limit", "error": f"Fila {idx}: límite de crédito inválido"}
                )

        elif payload.target_entity == "products":
            key = row.get("sku", "").strip()

            if key in seen_keys:
                row_errors.append({"row": idx, "column": "sku", "error": f"Fila {idx}: SKU duplicado en el archivo"})

            seen_keys.add(key)

            try:
                unit_price = Decimal(row["unit_price"].strip())

                unit_cost = Decimal(row["unit_cost"].strip())

                tax_rate = Decimal(row["tax_rate"].strip())

                if unit_price < 0:
                    row_errors.append(
                        {"row": idx, "column": "unit_price", "error": f"Fila {idx}: el precio no puede ser negativo"}
                    )

                if unit_cost < 0:
                    row_errors.append(
                        {"row": idx, "column": "unit_cost", "error": f"Fila {idx}: el costo no puede ser negativo"}
                    )

                if tax_rate < 0 or tax_rate > 1:
                    row_errors.append(
                        {"row": idx, "column": "tax_rate", "error": f"Fila {idx}: la tasa debe estar entre 0 y 1"}
                    )

            except Exception:
                row_errors.append(
                    {"row": idx, "column": "unit_price", "error": f"Fila {idx}: precio, costo o tasa inválidos"}
                )

        else:
            try:
                warehouse_code = row["warehouse_code"].strip()

                product_sku = row["product_sku"].strip()

                quantity = Decimal(row["quantity_delta"].strip())

                unit_cost = Decimal(row["unit_cost"].strip())

                if quantity == 0:
                    row_errors.append(
                        {"row": idx, "column": "quantity_delta", "error": f"Fila {idx}: la cantidad no puede ser cero"}
                    )

                if unit_cost < 0:
                    row_errors.append(
                        {"row": idx, "column": "unit_cost", "error": f"Fila {idx}: el costo no puede ser negativo"}
                    )

                if not db.scalar(
                    select(WarehouseModel.id).where(
                        WarehouseModel.code == warehouse_code, WarehouseModel.company_id == current_user.company_id
                    )
                ):
                    row_errors.append(
                        {
                            "row": idx,
                            "column": "warehouse_code",
                            "error": f"Fila {idx}: código de almacén inexistente en la empresa",
                        }
                    )

                if not db.scalar(
                    select(ProductModel.id).where(
                        ProductModel.sku == product_sku, ProductModel.company_id == current_user.company_id
                    )
                ):
                    row_errors.append(
                        {"row": idx, "column": "product_sku", "error": f"Fila {idx}: SKU inexistente en la empresa"}
                    )

            except Exception:
                row_errors.append(
                    {
                        "row": idx,
                        "column": "warehouse_code",
                        "error": f"Fila {idx}: códigos, cantidad o costo inválidos",
                    }
                )

    invalid_row_numbers = sorted({e["row"] for e in row_errors})

    invalid_rows = len(invalid_row_numbers)

    valid_rows = len(rows) - invalid_rows

    duplicate_import = (
        db.scalar(
            select(JobModel.id).where(
                JobModel.company_id == current_user.company_id,
                JobModel.job_type == f"import:{payload.target_entity}",
                JobModel.status == "completed",
                JobModel.payload_json.contains(str(attachment.sha256_checksum)),
            )
        )
        is not None
    )

    job = JobModel(
        company_id=current_user.company_id,
        requested_by=current_user.user_id,
        job_type=f"import:{payload.target_entity}",
        status="staged",
        progress=0,
        result=json.dumps(
            {
                "total_rows": len(rows),
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "row_errors": row_errors,
                "rejected_rows": [{"row_number": index, "values": rows[index - 1]} for index in invalid_row_numbers],
                "detected": detected,
                "attachment_id": str(payload.attachment_id),
                "column_mapping": payload.column_mapping,
                "corrections": payload.corrections,
                "is_duplicate_file": duplicate_import,
                "preview": rows[:10],
            }
        ),
        payload_json=json.dumps(
            {
                **payload.model_dump(mode="json"),
                "checksum": attachment.sha256_checksum,
                "invalid_row_numbers": invalid_row_numbers,
                "delimiter": detected["delimiter"],
                "encoding": detected["encoding"],
            }
        ),
    )

    db.add(job)

    db.flush()

    result = job_response(job)

    complete_request(record, result)

    db.commit()

    return result


def list_import_jobs(current_user: AuthenticatedUser, db: Session):
    allowed = [
        entity
        for entity, permission in {
            "customers": "customers:write",
            "products": "products:write",
            "inventory_adjustments": "inventory:write",
        }.items()
        if permission in current_user.permissions
    ]

    if not allowed:
        raise DomainForbiddenException("No tiene permisos para consultar importaciones.")

    rows = db.scalars(
        select(JobModel)
        .where(
            JobModel.company_id == current_user.company_id,
            JobModel.requested_by == current_user.user_id,
            JobModel.job_type.in_([f"import:{entity}" for entity in allowed]),
        )
        .order_by(JobModel.created_at.desc())
        .limit(100)
    ).all()

    return {
        "items": [
            {
                **job_response(row),
                "target_entity": row.job_type.split(":", 1)[1],
                "created_at": row.created_at.isoformat(),
                "attachment_id": json.loads(row.payload_json or "{}").get("attachment_id"),
            }
            for row in rows
        ]
    }


def commit_import_job(import_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: Optional[str]):
    job = db.scalar(
        select(JobModel)
        .where(JobModel.id == import_id, JobModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not job:
        other = db.scalar(select(JobModel.id).where(JobModel.id == import_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Importación no encontrada.")

    job_payload = json.loads(job.payload_json or "{}")

    target_entity = job_payload.get("target_entity")

    required_permission = {
        "customers": "customers:write",
        "products": "products:write",
        "inventory_adjustments": "inventory:write",
    }.get(target_entity)

    if not required_permission or required_permission not in current_user.permissions:
        raise DomainForbiddenException("No tiene permiso para ejecutar esta importación.")

    if job.status == "staged":
        staged_result = json.loads(job.result or "{}")

        if staged_result.get("is_duplicate_file"):
            raise HTTPException(409, "El archivo ya fue procesado anteriormente.")

        if staged_result.get("valid_rows", 0) <= 0:
            raise HTTPException(409, "No hay filas válidas para importar.")

        job.status = "pending"

        db.commit()

    elif job.status not in ("pending", "running", "completed"):
        raise HTTPException(409, "La importación no puede ejecutarse en su estado actual.")

    return job_response(job)
