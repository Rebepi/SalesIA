from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CustomerModel


def export_customer_personal_data(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.execute(
        select(CustomerModel).where(
            CustomerModel.id == customer_id, CustomerModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Titular de datos no encontrado")
    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="PRIVILEGED_ACCESS_EXPORT_PII",
        entity_type="Customer",
        entity_id=cust.id,
        diff={"doc_type": cust.doc_type, "doc_number": cust.doc_number},
        reason="Acceso y exportación de datos personales PII",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.commit()
    return {
        "customer_id": str(cust.id),
        "doc_type": cust.doc_type,
        "doc_number": cust.doc_number,
        "legal_name": cust.legal_name,
        "credit_limit": str(cust.credit_limit),
        "current_balance": str(cust.current_balance),
        "is_active": cust.is_active,
        "created_at": cust.created_at.isoformat(),
        "arco_rights_url": "https://salesia.enterprise/privacy/rights",
    }
