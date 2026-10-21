from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.infrastructure.models import CustomerModel, CustomerProfileModel


def ensure_customer_profile(db: Session, customer: CustomerModel) -> CustomerProfileModel:
    profile = db.scalar(
        select(CustomerProfileModel).where(
            CustomerProfileModel.company_id == customer.company_id, CustomerProfileModel.customer_id == customer.id
        )
    )
    if not profile:
        profile = CustomerProfileModel(
            id=uuid4(),
            company_id=customer.company_id,
            customer_id=customer.id,
            status="active" if customer.is_active else "archived",
            version=1,
            payment_terms_days=30,
            preferred_currency="USD",
            is_credit_blocked=False,
            tags_json="[]",
            assignment_history_json="[]",
        )
        db.add(profile)
        db.flush()
    return profile
