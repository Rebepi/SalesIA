import json
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.archivos import CustomerImportModel
from salesia.modules.clientes.application.validacion import (
    validate_customer_document,
    validate_customer_email,
    validate_customer_phone,
)
from salesia.modules.clientes.infrastructure.models import CustomerImportBatchModel, CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_import_template():
    return {
        "columns": [
            {"name": "code", "type": "string", "required": True, "description": "Código interno único"},
            {"name": "doc_type", "type": "string", "required": True, "description": "RUC, DNI o PASSPORT"},
            {"name": "doc_number", "type": "string", "required": True, "description": "Número de documento"},
            {"name": "legal_name", "type": "string", "required": True, "description": "Razón social o nombre"},
            {"name": "email", "type": "string", "required": False, "description": "Correo electrónico"},
            {"name": "phone", "type": "string", "required": False, "description": "Teléfono internacional"},
            {"name": "credit_limit", "type": "decimal", "required": False, "description": "Límite de crédito"},
        ],
        "example_row": {
            "code": "CLI-1001",
            "doc_type": "RUC",
            "doc_number": "20555555555",
            "legal_name": "EJEMPLO IMPORTACION SAC",
            "email": "contacto@ejemplo.com",
            "phone": "+51999888777",
            "credit_limit": "5000.00",
        },
    }


def import_customers(req: CustomerImportModel, current_user: AuthenticatedUser, db: Session):
    prev = db.scalar(
        select(CustomerImportBatchModel).where(
            CustomerImportBatchModel.company_id == current_user.company_id,
            CustomerImportBatchModel.batch_key == req.import_batch_key,
        )
    )
    if prev and not req.dry_run:
        return json.loads(prev.result_json)

    errors = []
    valid_rows = []
    for idx, row in enumerate(req.rows):
        doc_type = str(row.get("doc_type") or "").upper().strip()
        doc_number = str(row.get("doc_number") or "").strip()
        legal_name = str(row.get("legal_name") or "").strip()
        code = str(row.get("code") or "").strip()

        if not code or len(code) < 2:
            errors.append({"row_index": idx, "field": "code", "cause": "Código requerido de al menos 2 caracteres"})
            continue
        if not legal_name or len(legal_name) < 2:
            errors.append({"row_index": idx, "field": "legal_name", "cause": "Razón social requerida"})
            continue
        try:
            validate_customer_document(doc_type, doc_number)
            if row.get("email"):
                validate_customer_email(row.get("email"))
            if row.get("phone"):
                validate_customer_phone(row.get("phone"))
        except HTTPException as e:
            detail = e.detail if isinstance(e.detail, dict) else {"field": "document", "rule": str(e.detail)}
            errors.append(
                {
                    "row_index": idx,
                    "field": detail.get("field", "document"),
                    "cause": detail.get("rule", "Formato inválido"),
                }
            )
            continue

        valid_rows.append(
            {
                "code": code,
                "doc_type": doc_type,
                "doc_number": doc_number,
                "legal_name": legal_name,
                "email": row.get("email"),
                "phone": row.get("phone"),
                "credit_limit": Decimal(str(row.get("credit_limit") or "0")),
            }
        )

    if req.dry_run:
        return {
            "dry_run": True,
            "total_rows": len(req.rows),
            "valid_count": len(valid_rows),
            "error_count": len(errors),
            "errors": errors,
        }

    created_count = 0
    skipped_count = 0
    for item in valid_rows:
        existing = db.scalar(
            select(CustomerModel).where(
                CustomerModel.company_id == current_user.company_id,
                CustomerModel.doc_type == item["doc_type"],
                CustomerModel.doc_number == item["doc_number"],
            )
        )
        if existing:
            if req.on_duplicate == "update":
                existing.legal_name = item["legal_name"]
                if item["email"]:
                    existing.email = item["email"]
                if item["phone"]:
                    existing.phone = item["phone"]
                created_count += 1
            else:
                skipped_count += 1
        else:
            cust = CustomerModel(
                id=uuid4(),
                company_id=current_user.company_id,
                code=item["code"],
                doc_type=item["doc_type"],
                doc_number=item["doc_number"],
                legal_name=item["legal_name"],
                email=item["email"],
                phone=item["phone"],
                credit_limit=item["credit_limit"],
                current_balance=Decimal("0.000000"),
                is_active=True,
            )
            db.add(cust)
            db.flush()
            ensure_customer_profile(db, cust)
            created_count += 1

    result = {
        "dry_run": False,
        "import_batch_key": req.import_batch_key,
        "total_rows": len(req.rows),
        "created_count": created_count,
        "skipped_count": skipped_count,
        "error_count": len(errors),
        "errors": errors,
    }

    batch_rec = CustomerImportBatchModel(
        id=uuid4(), company_id=current_user.company_id, batch_key=req.import_batch_key, result_json=json.dumps(result)
    )
    db.add(batch_rec)
    db.commit()

    return result
