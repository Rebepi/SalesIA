from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.clientes.infrastructure.models import CustomerAddressModel, CustomerContactModel, CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def get_customer_quality(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    contacts_count = db.scalar(
        select(func.count(CustomerContactModel.id)).where(
            CustomerContactModel.company_id == current_user.company_id, CustomerContactModel.customer_id == customer_id
        )
    )
    addresses_count = db.scalar(
        select(func.count(CustomerAddressModel.id)).where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == customer_id
        )
    )

    missing = []
    points = 0
    total_weights = 6

    if cust.legal_name:
        points += 1
    if cust.email:
        points += 1
    else:
        missing.append({"field": "email", "action": "Registrar correo electrónico para facturación y notificaciones"})
    if cust.phone:
        points += 1
    else:
        missing.append({"field": "phone", "action": "Registrar teléfono de contacto directo"})
    if addresses_count > 0:
        points += 1
    else:
        missing.append({"field": "addresses", "action": "Registrar al menos una dirección fiscal o de entrega"})
    if contacts_count > 0:
        points += 1
    else:
        missing.append({"field": "contacts", "action": "Registrar una persona de contacto comercial"})
    if profile.assigned_sales_rep_id:
        points += 1
    else:
        missing.append({"field": "assigned_sales_rep_id", "action": "Asignar un representante de ventas titular"})

    score = int((points / total_weights) * 100)
    return {
        "customer_id": str(customer_id),
        "score_percentage": score,
        "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
        "missing_fields": [m["field"] for m in missing],
        "alerts": [m["action"] for m in missing],
        "blocking_purchases": False,
    }
