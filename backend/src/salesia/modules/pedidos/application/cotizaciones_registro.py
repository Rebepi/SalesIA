import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.emit import emit
from salesia.modules.pedidos.application.auxiliares.price_lines import price_lines
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response
from salesia.modules.pedidos.application.auxiliares.validate_references import validate_references
from salesia.modules.pedidos.application.contracts.cotizaciones_registro import QuotationCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import QuotationModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


def create_quotation(req: QuotationCreateModel, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "quotations.create", idempotency_key, req.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    validate_references(db, current_user.company_id, req.customer_id, req.branch_id)

    if not req.is_draft and len(req.lines) == 0:
        raise HTTPException(422, "Una cotización formal requiere al menos una línea.")

    if len(req.lines) == 0:
        lines, subtotal, tax, total = [], Decimal("0"), Decimal("0"), Decimal("0")

    else:
        lines, subtotal, tax, total = price_lines(db, current_user.company_id, req.lines)

    status_val = "draft" if req.is_draft else "pending"

    row = QuotationModel(
        company_id=current_user.company_id,
        branch_id=req.branch_id,
        customer_id=req.customer_id,
        quotation_number=f"COT-{next_number(db, current_user.company_id, 'COT'):08d}",
        version=1,
        status=status_val,
        currency=req.currency,
        subtotal_amount=subtotal,
        tax_amount=tax,
        total_amount=total,
        valid_until=req.valid_until.isoformat() if req.valid_until else None,
        payment_terms_days=req.payment_terms_days,
        delivery_terms=req.delivery_terms,
        notes=req.notes,
        special_conditions=req.special_conditions,
        seller_id=req.seller_id,
        lines_json=json.dumps(lines),
    )

    db.add(row)

    db.flush()

    audit(db, current_user, "CREATE", "Quotation", row.id, {"number": row.quotation_number, "total": str(total)})

    emit(db, current_user.company_id, "QUOTATION_CREATED", "Quotation", row.id, {"quotation_id": str(row.id)})

    response = quotation_response(row)

    complete_request(record, response)

    db.commit()

    return response


def list_quotations(
    status_filter: Optional[str],
    customer_id: Optional[UUID],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(QuotationModel).where(QuotationModel.company_id == current_user.company_id)

    if status_filter and status_filter not in ("expired", "pending", "negotiating"):
        query = query.where(QuotationModel.status == status_filter)

    if customer_id:
        query = query.where(QuotationModel.customer_id == customer_id)

    if status_filter in ("expired", "pending", "negotiating"):
        from salesia.modules.pedidos.application.auxiliares.quotation_status import quotation_status
        candidates = db.scalars(query.where(QuotationModel.status.in_(("pending", "negotiating"))).order_by(QuotationModel.created_at.desc())).all()
        rows = [row for row in candidates if quotation_status(row) == status_filter][offset:offset + limit]
    else:
        rows = db.scalars(query.order_by(QuotationModel.created_at.desc()).offset(offset).limit(limit)).all()

    return [quotation_response(row) for row in rows]


def get_quotation(quotation_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(QuotationModel).where(
            QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id
        )
    )

    if not row:
        other = db.scalar(select(QuotationModel.id).where(QuotationModel.id == quotation_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Cotización no encontrada.")

    return quotation_response(row)
