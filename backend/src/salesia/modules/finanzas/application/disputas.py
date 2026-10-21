from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.infrastructure_models import PaymentDisputeModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def list_payment_disputes(current_user: AuthenticatedUser, db: Session):
    disps = db.scalars(
        select(PaymentDisputeModel).where(PaymentDisputeModel.company_id == current_user.company_id)
    ).all()

    return [
        {
            "id": str(d.id),
            "payment_id": str(d.payment_id),
            "sale_id": str(d.sale_id),
            "amount": str(d.amount),
            "reason": d.reason,
            "status": d.status,
        }
        for d in disps
    ]
