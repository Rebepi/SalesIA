import csv
import io
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.application.contracts.archivos import CustomerExportModel
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel


def export_customers(req: CustomerExportModel, current_user: AuthenticatedUser, db: Session):
    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CUSTOMERS_EXPORTED",
        entity_type="Customer",
        entity_id=current_user.company_id,
        trace_id=str(uuid4()),
        payload_diff=json.dumps({"format": req.format, "reason": req.reason}),
    )
    db.add(audit)
    db.commit()

    can_sensitive = user_can_read_sensitive(current_user) and req.include_sensitive
    customers = db.scalars(
        select(CustomerModel)
        .where(CustomerModel.company_id == current_user.company_id)
        .order_by(CustomerModel.legal_name, CustomerModel.id)
    ).all()

    rows = []
    for c in customers:
        row = {
            "code": c.code,
            "doc_type": c.doc_type,
            "doc_number": c.doc_number,
            "legal_name": c.legal_name,
            "email": c.email,
            "phone": c.phone,
            "is_active": c.is_active,
            "credit_limit": str(c.credit_limit) if can_sensitive else None,
            "current_balance": str(c.current_balance) if can_sensitive else None,
        }
        rows.append(row)

    if req.format == "csv":
        headers = ["code", "doc_type", "doc_number", "legal_name", "email", "phone", "is_active"]
        if can_sensitive:
            headers.extend(["credit_limit", "current_balance"])
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return {"format": "csv", "data": buffer.getvalue(), "count": len(rows)}

    return {"format": "json", "count": len(rows), "data": rows}
