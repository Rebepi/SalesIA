from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.auxiliares.ensure_default_methods import ensure_default_methods
from salesia.modules.finanzas.application.contracts.medios_pago import (
    PaymentMethodCreateRequest,
    PaymentMethodUpdateRequest,
)
from salesia.modules.finanzas.infrastructure_models import PaymentMethodConfigModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def list_payment_methods(current_user: AuthenticatedUser, db: Session):
    ensure_default_methods(db, current_user.company_id)

    methods = db.scalars(
        select(PaymentMethodConfigModel)
        .where(PaymentMethodConfigModel.company_id == current_user.company_id)
        .order_by(PaymentMethodConfigModel.code)
    ).all()

    return [
        {
            "id": str(m.id),
            "code": m.code,
            "name": m.name,
            "is_active": m.is_active,
            "requires_reference": m.requires_reference,
            "requires_cash_session": m.requires_cash_session,
            "allowed_currencies": m.allowed_currencies.split(","),
        }
        for m in methods
    ]


def create_payment_method(payload: PaymentMethodCreateRequest, current_user: AuthenticatedUser, db: Session):
    existing = db.scalar(
        select(PaymentMethodConfigModel).where(
            PaymentMethodConfigModel.company_id == current_user.company_id,
            PaymentMethodConfigModel.code == payload.code.upper(),
        )
    )

    if existing:
        raise HTTPException(409, "El código de método de pago ya existe.")

    m = PaymentMethodConfigModel(
        id=uuid4(),
        company_id=current_user.company_id,
        code=payload.code.upper(),
        name=payload.name,
        is_active=payload.is_active,
        requires_reference=payload.requires_reference,
        requires_cash_session=payload.requires_cash_session,
        allowed_currencies=payload.allowed_currencies,
    )

    db.add(m)

    db.commit()

    return {
        "id": str(m.id),
        "code": m.code,
        "name": m.name,
        "is_active": m.is_active,
        "requires_reference": m.requires_reference,
        "requires_cash_session": m.requires_cash_session,
        "allowed_currencies": m.allowed_currencies.split(","),
    }


def update_payment_method(
    method_id: UUID, payload: PaymentMethodUpdateRequest, current_user: AuthenticatedUser, db: Session
):
    m = db.scalar(
        select(PaymentMethodConfigModel).where(
            PaymentMethodConfigModel.company_id == current_user.company_id, PaymentMethodConfigModel.id == method_id
        )
    )

    if not m:
        raise HTTPException(404, "Método de pago no encontrado.")

    if payload.name is not None:
        m.name = payload.name

    if payload.is_active is not None:
        m.is_active = payload.is_active

    if payload.requires_reference is not None:
        m.requires_reference = payload.requires_reference

    if payload.requires_cash_session is not None:
        m.requires_cash_session = payload.requires_cash_session

    if payload.allowed_currencies is not None:
        m.allowed_currencies = payload.allowed_currencies

    db.commit()

    return {
        "id": str(m.id),
        "code": m.code,
        "name": m.name,
        "is_active": m.is_active,
        "requires_reference": m.requires_reference,
        "requires_cash_session": m.requires_cash_session,
        "allowed_currencies": m.allowed_currencies.split(","),
    }
