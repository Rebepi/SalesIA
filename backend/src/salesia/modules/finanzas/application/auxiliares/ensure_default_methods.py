from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.infrastructure_models import PaymentMethodConfigModel


def ensure_default_methods(db: Session, company_id: UUID):

    existing = db.scalars(
        select(PaymentMethodConfigModel.code).where(PaymentMethodConfigModel.company_id == company_id)
    ).all()

    defaults = [
        ("CASH", "Efectivo", False, True),
        ("TRANSFER", "Transferencia Bancaria", True, False),
        ("CARD", "Tarjeta de Débito / Crédito", True, False),
        ("CREDIT", "Crédito Comercial", False, False),
    ]

    for code, name, req_ref, req_cs in defaults:
        if code not in existing:
            db.add(
                PaymentMethodConfigModel(
                    id=uuid4(),
                    company_id=company_id,
                    code=code,
                    name=name,
                    is_active=True,
                    requires_reference=req_ref,
                    requires_cash_session=req_cs,
                    allowed_currencies="USD,PEN,EUR",
                )
            )

    db.flush()
