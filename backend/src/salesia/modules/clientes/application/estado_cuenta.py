from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import SaleModel


def get_customer_statement(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    customer = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    ).scalar_one_or_none()
    if not customer:
        raise DomainNotFoundException("Cliente no encontrado.")

    sales = (
        db.execute(
            select(SaleModel)
            .where(SaleModel.company_id == current_user.company_id, SaleModel.customer_id == customer_id)
            .order_by(SaleModel.created_at.desc())
        )
        .scalars()
        .all()
    )

    can_sensitive = user_can_read_sensitive(current_user)
    invoices = []
    total_sales = Decimal("0.000000")
    total_paid = Decimal("0.000000")
    for s in sales:
        total_sales += s.total_amount
        total_paid += s.paid_amount
        invoices.append(
            {
                "sale_id": str(s.id),
                "series_number": f"{s.series}-{s.number:06d}",
                "status": s.status,
                "currency": s.currency,
                "is_credit": s.is_credit,
                "total_amount": str(s.total_amount) if can_sensitive else None,
                "paid_amount": str(s.paid_amount) if can_sensitive else None,
                "pending_balance": str(s.total_amount - s.paid_amount) if can_sensitive else None,
                "created_at": s.created_at.isoformat(),
            }
        )

    return {
        "customer_id": str(customer.id),
        "legal_name": customer.legal_name,
        "doc_number": customer.doc_number,
        "credit_limit": str(customer.credit_limit) if can_sensitive else None,
        "current_balance": str(customer.current_balance) if can_sensitive else None,
        "total_billed": str(total_sales) if can_sensitive else None,
        "total_paid": str(total_paid) if can_sensitive else None,
        "invoices_count": len(invoices),
        "invoices": invoices,
    }
