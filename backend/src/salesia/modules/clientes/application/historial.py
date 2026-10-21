from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.infrastructure.models import (
    CustomerActivityModel,
    CustomerAddressModel,
    CustomerContactModel,
    CustomerModel,
    CustomerNoteModel,
    CustomerOpportunityModel,
)
from salesia.modules.finanzas.infrastructure_models import ReturnModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import AuditLogModel, OrderModel, PaymentModel, QuotationModel, SaleModel


def get_customer_history(
    customer_id: UUID,
    event_type: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    can_sensitive = user_can_read_sensitive(current_user)
    sales = db.scalars(
        select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.customer_id == customer_id)
    ).all()
    quotes = db.scalars(
        select(QuotationModel).where(
            QuotationModel.company_id == current_user.company_id, QuotationModel.customer_id == customer_id
        )
    ).all()
    orders = db.scalars(
        select(OrderModel).where(
            OrderModel.company_id == current_user.company_id, OrderModel.customer_id == customer_id
        )
    ).all()
    notes = db.scalars(
        select(CustomerNoteModel).where(
            CustomerNoteModel.company_id == current_user.company_id, CustomerNoteModel.customer_id == customer_id
        )
    ).all()
    acts = db.scalars(
        select(CustomerActivityModel).where(
            CustomerActivityModel.company_id == current_user.company_id,
            CustomerActivityModel.customer_id == customer_id,
        )
    ).all()
    opportunities = db.scalars(
        select(CustomerOpportunityModel).where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.customer_id == customer_id,
        )
    ).all()
    payments = db.scalars(
        select(PaymentModel)
        .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
        .where(PaymentModel.company_id == current_user.company_id, SaleModel.customer_id == customer_id)
    ).all()
    returns = db.scalars(
        select(ReturnModel).where(
            ReturnModel.company_id == current_user.company_id, ReturnModel.customer_id == customer_id
        )
    ).all()
    audits = db.scalars(
        select(AuditLogModel).where(
            AuditLogModel.company_id == current_user.company_id,
            AuditLogModel.entity_type == "Customer",
            AuditLogModel.entity_id == customer_id,
        )
    ).all()
    contacts = db.scalars(
        select(CustomerContactModel).where(
            CustomerContactModel.company_id == current_user.company_id, CustomerContactModel.customer_id == customer_id
        )
    ).all()
    addresses = db.scalars(
        select(CustomerAddressModel).where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == customer_id
        )
    ).all()

    timeline = []
    for s in sales:
        timeline.append(
            {
                "type": "sale",
                "id": str(s.id),
                "reference": f"{s.series}-{s.number}",
                "date": s.created_at.isoformat(),
                "status": s.status,
                "amount": str(s.total_amount) if can_sensitive else None,
                "currency": s.currency,
            }
        )
    for q in quotes:
        timeline.append(
            {
                "type": "quotation",
                "id": str(q.id),
                "reference": q.quotation_number,
                "date": q.created_at.isoformat(),
                "status": q.status,
                "amount": str(q.total_amount) if can_sensitive else None,
                "currency": q.currency,
            }
        )
    for o in orders:
        timeline.append(
            {
                "type": "order",
                "id": str(o.id),
                "reference": o.order_number,
                "date": o.created_at.isoformat(),
                "status": o.status,
                "amount": str(o.total_amount) if can_sensitive else None,
                "currency": o.currency,
            }
        )
    for n in notes:
        if can_sensitive or n.category == "comercial":
            timeline.append(
                {
                    "type": "note",
                    "id": str(n.id),
                    "reference": n.category,
                    "date": n.created_at.isoformat(),
                    "content": n.content,
                    "author": n.author_email,
                }
            )
    for a in acts:
        timeline.append(
            {
                "type": "activity",
                "id": str(a.id),
                "reference": a.activity_type,
                "date": a.due_date.isoformat(),
                "subject": a.subject,
                "status": a.status,
            }
        )
    for opportunity in opportunities:
        timeline.append(
            {
                "type": "opportunity",
                "id": str(opportunity.id),
                "reference": opportunity.title,
                "date": opportunity.created_at.isoformat(),
                "status": opportunity.stage,
                "amount": str(opportunity.estimated_amount) if can_sensitive else None,
            }
        )
    for payment in payments:
        timeline.append(
            {
                "type": "payment",
                "id": str(payment.id),
                "reference": payment.payment_method,
                "date": payment.created_at.isoformat(),
                "status": payment.status,
                "amount": str(payment.amount) if can_sensitive else None,
                "currency": payment.currency,
            }
        )
    for returned in returns:
        timeline.append(
            {
                "type": "return",
                "id": str(returned.id),
                "reference": returned.reason,
                "date": returned.created_at.isoformat(),
                "status": returned.status,
            }
        )
    for audit in audits:
        timeline.append(
            {
                "type": "audit",
                "id": str(audit.id),
                "reference": audit.action,
                "date": audit.created_at.isoformat(),
                "status": "recorded",
                "actor": audit.actor_email,
            }
        )
    for contact in contacts:
        timeline.append(
            {
                "type": "contact",
                "id": str(contact.id),
                "reference": contact.name,
                "date": contact.created_at.isoformat(),
                "status": "primary" if contact.is_primary else "active",
            }
        )
    for address in addresses:
        timeline.append(
            {
                "type": "address",
                "id": str(address.id),
                "reference": f"{address.address_type}: {address.street}",
                "date": address.created_at.isoformat(),
                "status": "primary" if address.is_primary else "active",
            }
        )

    if event_type:
        timeline = [t for t in timeline if t["type"] == event_type]
    if start_date:
        start = datetime.fromisoformat(start_date).astimezone(timezone.utc)
        timeline = [t for t in timeline if datetime.fromisoformat(t["date"]).astimezone(timezone.utc) >= start]
    if end_date:
        end = datetime.fromisoformat(end_date).astimezone(timezone.utc)
        timeline = [t for t in timeline if datetime.fromisoformat(t["date"]).astimezone(timezone.utc) <= end]
    timeline.sort(key=lambda x: x["date"], reverse=True)

    total_billed = sum(s.total_amount for s in sales if s.status in ("confirmed", "paid"))
    total_paid = sum(s.paid_amount for s in sales)
    reconciled_balance = total_billed - total_paid

    return {
        "customer_id": str(customer_id),
        "total_operations": len(timeline),
        "total_billed": str(total_billed) if can_sensitive else None,
        "total_paid": str(total_paid) if can_sensitive else None,
        "reconciled_balance": str(reconciled_balance) if can_sensitive else None,
        "credit_limit": str(cust.credit_limit) if can_sensitive else None,
        "timeline": timeline,
    }
