from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.infrastructure.models import CustomerModel, CustomerProfileModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import SaleModel


def list_customers(
    search: Optional[str],
    status: Optional[str],
    is_active: Optional[bool],
    sales_rep_id: Optional[UUID],
    limit: int,
    offset: int,
    cursor: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
    order: str = "recent",
):
    query = select(CustomerModel).where(CustomerModel.company_id == current_user.company_id)
    if is_active is not None:
        query = query.where(CustomerModel.is_active.is_(is_active))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                CustomerModel.legal_name.ilike(pattern),
                CustomerModel.doc_number.ilike(pattern),
                CustomerModel.code.ilike(pattern),
                CustomerModel.phone.ilike(pattern),
            )
        )
    if status and sales_rep_id:
        query = query.join(CustomerProfileModel, CustomerProfileModel.customer_id == CustomerModel.id).where(
            CustomerProfileModel.status == status, CustomerProfileModel.assigned_sales_rep_id == sales_rep_id
        )
    elif status:
        query = query.join(CustomerProfileModel, CustomerProfileModel.customer_id == CustomerModel.id).where(
            CustomerProfileModel.status == status
        )
    elif sales_rep_id:
        query = query.join(CustomerProfileModel, CustomerProfileModel.customer_id == CustomerModel.id).where(
            CustomerProfileModel.assigned_sales_rep_id == sales_rep_id
        )

    if order == "random":
        query = query.where(CustomerModel.doc_type != "SIN_DOCUMENTO", CustomerModel.code != "CONSUMIDOR_FINAL")
    total_count = db.scalar(select(func.count()).select_from(query.subquery()))
    customers = db.execute(query.order_by(func.random() if order == "random" else CustomerModel.created_at.desc()).limit(min(limit, 5) if order == "random" else limit).offset(offset)).scalars().all()

    can_sensitive = user_can_read_sensitive(current_user)
    items = []
    for c in customers:
        item = {
            "id": str(c.id),
            "customer_id": str(c.id),
            "company_id": str(c.company_id),
            "code": c.code,
            "doc_type": c.doc_type,
            "doc_number": c.doc_number,
            "legal_name": c.legal_name,
            "email": c.email,
            "phone": c.phone,
            "credit_limit": str(c.credit_limit) if can_sensitive else None,
            "current_balance": str(c.current_balance) if can_sensitive else None,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat(),
        }
        items.append(item)

    next_cursor = str(customers[-1].id) if len(customers) == limit else None
    return {"items": items, "total_count": total_count, "limit": limit, "offset": offset, "cursor": next_cursor}


def get_customer(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    customer = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    ).scalar_one_or_none()
    if not customer:
        raise DomainNotFoundException("Cliente no encontrado en este tenant.")

    profile = ensure_customer_profile(db, customer)
    can_sensitive = user_can_read_sensitive(current_user)

    sales_summary = db.execute(
        select(
            func.count(SaleModel.id),
            func.coalesce(func.sum(SaleModel.total_amount), Decimal("0")),
            func.coalesce(func.sum(SaleModel.paid_amount), Decimal("0")),
        ).where(SaleModel.company_id == current_user.company_id, SaleModel.customer_id == customer_id)
    ).one()

    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "company_id": str(customer.company_id),
        "code": customer.code,
        "doc_type": customer.doc_type,
        "doc_number": customer.doc_number,
        "legal_name": customer.legal_name,
        "email": customer.email,
        "phone": customer.phone,
        "credit_limit": str(customer.credit_limit) if can_sensitive else None,
        "current_balance": str(customer.current_balance) if can_sensitive else None,
        "is_active": customer.is_active,
        "status": profile.status,
        "version": profile.version,
        "preferred_currency": profile.preferred_currency,
        "payment_terms_days": profile.payment_terms_days,
        "price_list_id": profile.price_list_id,
        "is_credit_blocked": profile.is_credit_blocked,
        "credit_block_until": profile.credit_block_until.isoformat() if profile.credit_block_until else None,
        "credit_block_reason": profile.credit_block_reason,
        "created_at": customer.created_at.isoformat(),
        "summary": {
            "sales_count": sales_summary[0],
            "total_billed": str(sales_summary[1]) if can_sensitive else None,
            "total_paid": str(sales_summary[2]) if can_sensitive else None,
        },
    }
