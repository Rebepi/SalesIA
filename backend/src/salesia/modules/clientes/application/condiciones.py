from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.application.contracts.comercial import CreditCheckRequest, CustomerCommercialTermsModel
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.modules.ventas.application.validacion import credit_block_active


def get_customer_commercial_terms(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    can_sensitive = user_can_read_sensitive(current_user)

    return {
        "customer_id": str(customer_id),
        "price_list_id": profile.price_list_id,
        "payment_terms_days": profile.payment_terms_days,
        "preferred_currency": profile.preferred_currency,
        "credit_limit": str(cust.credit_limit) if can_sensitive else None,
        "current_balance": str(cust.current_balance) if can_sensitive else None,
        "is_credit_blocked": profile.is_credit_blocked,
        "credit_block_until": profile.credit_block_until.isoformat() if profile.credit_block_until else None,
        "credit_block_reason": profile.credit_block_reason,
    }


def update_customer_commercial_terms(
    customer_id: UUID, req: CustomerCommercialTermsModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    cust.credit_limit = req.credit_limit
    profile.price_list_id = req.price_list_id
    profile.payment_terms_days = req.payment_terms_days
    profile.preferred_currency = req.preferred_currency.upper()
    profile.is_credit_blocked = req.is_credit_blocked
    profile.credit_block_until = req.credit_block_until
    profile.credit_block_reason = req.credit_block_reason
    profile.version += 1
    db.commit()

    return {
        "customer_id": str(customer_id),
        "credit_limit": str(cust.credit_limit),
        "payment_terms_days": profile.payment_terms_days,
        "preferred_currency": profile.preferred_currency,
        "is_credit_blocked": profile.is_credit_blocked,
    }


def check_customer_credit(customer_id: UUID, req: CreditCheckRequest, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    now_utc = datetime.now(timezone.utc)

    if credit_block_active(profile, now_utc):
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": f"Cliente bloqueado para crédito: {profile.credit_block_reason or 'Bloqueo administrativo activo'}",
            "available_credit": "0.000000",
        }

    future_balance = cust.current_balance + req.amount
    available = max(Decimal("0.000000"), cust.credit_limit - cust.current_balance)
    if future_balance > cust.credit_limit:
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": f"Exceso de límite de crédito. Solicitado: {req.amount}, Disponible: {available}",
            "available_credit": str(available),
        }

    return {
        "allowed": True,
        "requires_approval": False,
        "reason": "Crédito aprobado dentro del límite autorizado",
        "available_credit": str(available),
    }
