import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from salesia.modules.inventario.service import move_stock
from salesia.modules.operaciones.import_files import read_import_file
from salesia.modules.operaciones.infrastructure_models import UploadGrant
from salesia.shared.infrastructure.models import AttachmentModel, CompanyModel, CustomerModel, ProductModel, WarehouseModel


def parse_decimal(value, field):
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"Valor decimal inválido en {field}") from exc


def execute_import(db, job):
    db.scalar(select(CompanyModel).where(CompanyModel.id == job.company_id).with_for_update())
    payload = json.loads(job.payload_json)
    att_id = UUID(str(payload["attachment_id"]))
    attachment = db.scalar(
        select(AttachmentModel).where(
            AttachmentModel.id == att_id,
            AttachmentModel.company_id == job.company_id,
            AttachmentModel.verified.is_(True),
        )
    )
    grant = db.get(UploadGrant, attachment.id) if attachment else None
    if not attachment or not grant:
        raise ValueError("El adjunto dejó de estar disponible")
    rows, _, _ = read_import_file(
        grant.storage_path,
        payload.get("delimiter"),
        payload.get("encoding"),
        payload.get("column_mapping"),
        payload.get("corrections"),
    )
    entity = job.job_type.split(":", 1)[1]
    if entity != "customers":
        from salesia.modules.organizacion.application.perfil_operativo import require_area
        require_area(db, job.company_id, "inventory")
        db.info["period_modules"] = ["inventory"]
        db.info["period_request"] = {"job_id": str(job.id), "type": job.job_type}
        if job.requested_by:
            from salesia.shared.infrastructure.models import UserModel
            actor = db.scalar(select(UserModel).where(UserModel.id == job.requested_by, UserModel.company_id == job.company_id))
            if actor:
                db.info["period_actor"] = {"id": actor.id, "email": actor.email}
    invalid_row_numbers = set(payload.get("invalid_row_numbers", []))
    processed_rows = 0
    for index, row in enumerate(rows, 1):
        if job.cancel_requested:
            raise InterruptedError("Cancelado por el usuario")
        if index in invalid_row_numbers:
            continue
        if entity == "customers":
            existing = db.scalar(
                select(CustomerModel).where(
                    CustomerModel.company_id == job.company_id,
                    CustomerModel.doc_type == row["doc_type"],
                    CustomerModel.doc_number == row["doc_number"],
                )
            )
            if existing:
                existing.legal_name = row["legal_name"]
                if row.get("email"):
                    existing.email = row["email"]
                if row.get("phone"):
                    existing.phone = row["phone"]
                if row.get("credit_limit"):
                    existing.credit_limit = parse_decimal(row["credit_limit"], "credit_limit")
            else:
                db.add(
                    CustomerModel(
                        company_id=job.company_id,
                        code=row["code"],
                        doc_type=row["doc_type"],
                        doc_number=row["doc_number"],
                        legal_name=row["legal_name"],
                        email=row.get("email") or None,
                        phone=row.get("phone") or None,
                        credit_limit=parse_decimal(row.get("credit_limit", "0"), "credit_limit"),
                        current_balance=Decimal("0"),
                    )
                )
        elif entity == "products":
            existing_prod = db.scalar(
                select(ProductModel).where(ProductModel.company_id == job.company_id, ProductModel.sku == row["sku"])
            )
            if existing_prod:
                existing_prod.name = row["name"]
                existing_prod.category = row["category"]
                existing_prod.unit_price = parse_decimal(row["unit_price"], "unit_price")
                existing_prod.unit_cost = parse_decimal(row["unit_cost"], "unit_cost")
            else:
                db.add(
                    ProductModel(
                        company_id=job.company_id,
                        sku=row["sku"],
                        name=row["name"],
                        category=row["category"],
                        unit_of_measure=row["unit_of_measure"],
                        unit_price=parse_decimal(row["unit_price"], "unit_price"),
                        unit_cost=parse_decimal(row["unit_cost"], "unit_cost"),
                        tax_rate=parse_decimal(row["tax_rate"], "tax_rate"),
                    )
                )
        else:
            warehouse = db.scalar(
                select(WarehouseModel).where(
                    WarehouseModel.company_id == job.company_id, WarehouseModel.code == row["warehouse_code"]
                )
            )
            product = db.scalar(
                select(ProductModel).where(
                    ProductModel.company_id == job.company_id, ProductModel.sku == row["product_sku"]
                )
            )
            if not warehouse or not product:
                raise ValueError("El almacén o producto de la importación dejó de estar disponible")
            move_stock(
                db,
                job.company_id,
                warehouse.id,
                product.id,
                parse_decimal(row["quantity_delta"], "quantity_delta"),
                parse_decimal(row["unit_cost"], "unit_cost"),
                job.id,
                "IMPORT_ADJUSTMENT",
            )
        processed_rows += 1
        job.progress = min(99, int(index / len(rows) * 100))
    return {"processed_rows": processed_rows, "skipped_rows": len(invalid_row_numbers), "entity": entity}
