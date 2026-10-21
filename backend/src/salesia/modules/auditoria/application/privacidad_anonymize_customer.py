import hashlib

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.contracts.privacidad_anonymize_customer import AnonymizeCustomerRequest
from salesia.modules.operaciones.infrastructure_models import LegalHold
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CustomerModel


def anonymize_customer(payload: AnonymizeCustomerRequest, current_user: AuthenticatedUser, db: Session):
    hold = db.scalar(
        select(LegalHold).where(
            LegalHold.company_id == current_user.company_id,
            LegalHold.entity_type == "customer",
            LegalHold.entity_id == payload.customer_id,
            LegalHold.lifted_at.is_(None),
        )
    )
    if hold:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"No se puede anonimizar la entidad: cuenta con retención legal activa ({hold.reason})",
        )

    cust = db.execute(
        select(CustomerModel).where(
            CustomerModel.id == payload.customer_id, CustomerModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado para anonimizar")

    cust.legal_name = "PERSONA ANONIMIZADA - DERECHO AL OLVIDO"
    cust.doc_type = "ANON"
    cust.doc_number = hashlib.sha256(f"{current_user.company_id}:{cust.id}".encode()).hexdigest()[:32]
    cust.email = None
    cust.phone = None
    cust.is_active = False
    db.commit()

    return {
        "customer_id": str(payload.customer_id),
        "status": "anonymized",
        "detail": "Nombre e identidad disociados. Registros fiscales preservados según ley tributaria.",
    }
