import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.public_quotation import public_quotation
from salesia.modules.pedidos.application.auxiliares.quotation_pdf import quotation_pdf
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response
from salesia.modules.pedidos.application.contracts.portal_cotizaciones import PublicQuotationAcceptance
from salesia.shared.infrastructure.models import AuditLogModel, CompanyModel


def open_public_quotation(quotation_id: UUID, authorization: Optional[str], db: Session):
    row = public_quotation(db, quotation_id, authorization, lock=True)

    if row.opened_at is None:
        row.opened_at = now()

        log = json.loads(row.communication_log_json or "[]")

        log.append({"event": "OPENED_BY_RECIPIENT", "at": row.opened_at.isoformat()})

        row.communication_log_json = json.dumps(log)

        db.commit()

    result = quotation_response(row)

    result["lines"] = [
        {
            key: value
            for key, value in line.items()
            if key
            in {
                "product_id",
                "sku",
                "name",
                "quantity",
                "unit_price",
                "discount_pct",
                "tax_rate",
                "line_subtotal",
                "line_tax",
            }
        }
        for line in result["lines"]
    ]

    company = db.get(CompanyModel, row.company_id)

    return {
        key: value
        for key, value in result.items()
        if key
        in {
            "quotation_number",
            "version",
            "status",
            "valid_until",
            "payment_terms_days",
            "delivery_terms",
            "notes",
            "special_conditions",
            "currency",
            "lines",
            "subtotal_amount",
            "tax_amount",
            "total_amount",
            "accepted_at",
        }
    } | {"company_name": company.trade_name or company.legal_name}


def accept_public_quotation(
    quotation_id: UUID, payload: PublicQuotationAcceptance, authorization: Optional[str], db: Session
):
    row = public_quotation(db, quotation_id, authorization, lock=True)

    if not payload.conditions_accepted:
        raise HTTPException(422, "Debes aceptar los términos comerciales de la propuesta.")

    if row.status in ("accepted", "converted"):
        return {
            "status": row.status,
            "accepted_at": row.accepted_at.astimezone(timezone.utc).isoformat() if row.accepted_at else None,
        }

    if row.valid_until and datetime.fromisoformat(row.valid_until).astimezone(timezone.utc) < now():
        raise HTTPException(409, "La propuesta ha vencido. Solicita una cotización actualizada.")

    row.status = "accepted"

    row.accepted_at = now()

    log = json.loads(row.communication_log_json or "[]")

    log.append(
        {"event": "ACCEPTED_BY_RECIPIENT", "at": row.accepted_at.isoformat(), "accepted_by": payload.accepted_by}
    )

    row.communication_log_json = json.dumps(log)

    db.add(
        AuditLogModel(
            company_id=row.company_id,
            actor_id=None,
            actor_email="quotation-recipient",
            action="ACCEPT",
            entity_type="Quotation",
            entity_id=row.id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"accepted_by": payload.accepted_by}),
            created_at=now(),
        )
    )

    db.commit()

    return {"status": row.status, "accepted_at": row.accepted_at.astimezone(timezone.utc).isoformat()}


def public_quotation_pdf(quotation_id: UUID, authorization: Optional[str], db: Session):
    row = public_quotation(db, quotation_id, authorization)

    return StreamingResponse(
        quotation_pdf(db, row),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{row.quotation_number}-v{row.version}.pdf"',
            "Cache-Control": "no-store",
        },
    )
