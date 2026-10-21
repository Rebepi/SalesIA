from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.shared.infrastructure.models import OrderModel, SaleModel


def portal_get_my_profile(customer: CustomerModel):
    return {
        "customer_id": str(customer.id),
        "code": customer.code,
        "doc_type": customer.doc_type,
        "doc_number": customer.doc_number,
        "legal_name": customer.legal_name,
        "email": customer.email,
        "phone": customer.phone,
        "credit_limit": str(customer.credit_limit),
        "current_balance": str(customer.current_balance),
    }


def portal_get_my_invoices(customer: CustomerModel, db: Session):
    sales = db.scalars(
        select(SaleModel)
        .where(SaleModel.company_id == customer.company_id, SaleModel.customer_id == customer.id)
        .order_by(SaleModel.created_at.desc())
    ).all()
    return [
        {
            "sale_id": str(s.id),
            "series_number": f"{s.series}-{s.number:06d}",
            "status": s.status,
            "total_amount": str(s.total_amount),
            "paid_amount": str(s.paid_amount),
            "pending_balance": str(s.total_amount - s.paid_amount),
            "created_at": s.created_at.isoformat(),
        }
        for s in sales
    ]


def portal_get_my_orders(customer: CustomerModel, db: Session):
    orders = db.scalars(
        select(OrderModel)
        .where(OrderModel.company_id == customer.company_id, OrderModel.customer_id == customer.id)
        .order_by(OrderModel.created_at.desc())
    ).all()
    return [
        {
            "order_id": str(o.id),
            "order_number": o.order_number,
            "status": o.status,
            "total_amount": str(o.total_amount),
            "created_at": o.created_at.isoformat(),
        }
        for o in orders
    ]


def portal_get_my_statement(customer: CustomerModel, db: Session):
    sales = db.scalars(
        select(SaleModel)
        .where(SaleModel.company_id == customer.company_id, SaleModel.customer_id == customer.id)
        .order_by(SaleModel.created_at.desc())
    ).all()

    total_billed = sum(s.total_amount for s in sales)
    total_paid = sum(s.paid_amount for s in sales)
    return {
        "customer_id": str(customer.id),
        "legal_name": customer.legal_name,
        "credit_limit": str(customer.credit_limit),
        "current_balance": str(customer.current_balance),
        "total_billed": str(total_billed),
        "total_paid": str(total_paid),
        "invoices_count": len(sales),
    }
