from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.infrastructure.models import CustomerContactModel, CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.errors import DomainForbiddenException


def get_portal_customer(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> CustomerModel:
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id,
            CustomerModel.email == current_user.email,
            CustomerModel.is_active.is_(True),
        )
    )
    if not cust:
        contact = db.scalar(
            select(CustomerContactModel).where(
                CustomerContactModel.company_id == current_user.company_id,
                CustomerContactModel.email == current_user.email,
            )
        )
        if contact:
            cust = db.scalar(
                select(CustomerModel).where(
                    CustomerModel.id == contact.customer_id,
                    CustomerModel.company_id == current_user.company_id,
                    CustomerModel.is_active.is_(True),
                )
            )
    if not cust:
        raise DomainForbiddenException("Usuario sin acceso a portal de clientes.")
    return cust
