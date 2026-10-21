from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.application.contracts.clientes import CustomerUpdateModel
from salesia.modules.clientes.application.validacion import validate_customer_email, validate_customer_phone
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException


def update_customer(customer_id: UUID, req: CustomerUpdateModel, current_user: AuthenticatedUser, db: Session):
    customer = db.execute(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    ).scalar_one_or_none()
    if not customer:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, customer)

    if req.version is not None and req.version != profile.version:
        raise DomainConflictException("Conflicto de concurrencia: el cliente fue modificado por otra transacción.")

    if req.legal_name is not None:
        clean = sanitize_text(req.legal_name)
        if not clean:
            raise HTTPException(422, {"field": "legal_name", "rule": "Razón social no puede ser vacía"})
        customer.legal_name = clean

    if req.email is not None:
        validate_customer_email(req.email)
        customer.email = req.email.lower().strip() if req.email else None

    if req.phone is not None:
        validate_customer_phone(req.phone)
        customer.phone = req.phone.strip() if req.phone else None

    if req.credit_limit is not None:
        customer.credit_limit = req.credit_limit

    if req.status is not None:
        profile.status = req.status
        customer.is_active = req.status != "archived"

    if req.assigned_sales_rep_id is not None:
        profile.assigned_sales_rep_id = req.assigned_sales_rep_id
    if req.sales_team is not None:
        profile.sales_team = req.sales_team
    if req.backup_sales_rep_id is not None:
        profile.backup_sales_rep_id = req.backup_sales_rep_id
    if req.price_list_id is not None:
        profile.price_list_id = req.price_list_id
    if req.payment_terms_days is not None:
        profile.payment_terms_days = req.payment_terms_days
    if req.preferred_currency is not None:
        profile.preferred_currency = req.preferred_currency
    if req.is_credit_blocked is not None:
        profile.is_credit_blocked = req.is_credit_blocked
    if req.credit_block_until is not None:
        profile.credit_block_until = req.credit_block_until
    if req.credit_block_reason is not None:
        profile.credit_block_reason = req.credit_block_reason

    profile.version += 1
    db.commit()
    db.refresh(customer)
    db.refresh(profile)

    can_sensitive = user_can_read_sensitive(current_user)
    return {
        "id": str(customer.id),
        "customer_id": str(customer.id),
        "company_id": str(customer.company_id),
        "legal_name": customer.legal_name,
        "credit_limit": str(customer.credit_limit) if can_sensitive else None,
        "current_balance": str(customer.current_balance) if can_sensitive else None,
        "status": profile.status,
        "version": profile.version,
        "updated_at": customer.updated_at.isoformat(),
    }
