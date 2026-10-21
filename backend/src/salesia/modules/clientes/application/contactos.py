import json
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.contactos import CustomerContactCreateModel
from salesia.modules.clientes.application.contactos_edicion import contact_data
from salesia.modules.clientes.application.validacion import validate_customer_email, validate_customer_phone
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerContactModel, CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def list_customer_contacts(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    contacts = db.scalars(
        select(CustomerContactModel)
        .where(
            CustomerContactModel.company_id == current_user.company_id, CustomerContactModel.customer_id == customer_id
        )
        .order_by(CustomerContactModel.is_primary.desc(), CustomerContactModel.name.asc())
    ).all()
    return [contact_data(contact) for contact in contacts]


def create_customer_contact(
    customer_id: UUID, req: CustomerContactCreateModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        ).with_for_update()
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    validate_customer_email(req.email)
    validate_customer_phone(req.phone)

    if req.is_primary and req.is_active:
        db.execute(
            update(CustomerContactModel)
            .where(
                CustomerContactModel.company_id == current_user.company_id,
                CustomerContactModel.customer_id == customer_id,
                CustomerContactModel.purpose == req.purpose,
            )
            .values(is_primary=False, version=CustomerContactModel.version + 1)
        )

    contact = CustomerContactModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        name=sanitize_text(req.name) or "Contacto",
        role=sanitize_text(req.role) or "Contacto",
        email=req.email.lower().strip() if req.email else None,
        phone=req.phone.strip() if req.phone else None,
        is_primary=req.is_primary and req.is_active,
        preferences_json=json.dumps(req.preferences or {}),
        purpose=req.purpose, valid_from=req.valid_from, valid_until=req.valid_until, is_active=req.is_active, can_purchase=req.can_purchase, can_receive=req.can_receive, version=1,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact_data(contact)


def delete_customer_contact(customer_id: UUID, contact_id: UUID, current_user: AuthenticatedUser, db: Session):
    customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id).with_for_update())
    if customer is None:
        raise DomainNotFoundException("Cliente no encontrado.")

    contact = db.scalar(
        select(CustomerContactModel).where(
            CustomerContactModel.company_id == current_user.company_id,
            CustomerContactModel.customer_id == customer_id,
            CustomerContactModel.id == contact_id,
        )
    )
    if not contact:
        raise DomainNotFoundException("Contacto no encontrado.")

    if contact.is_active:
        contact.is_active, contact.is_primary, contact.version = False, False, contact.version + 1
    db.commit()
    return {"status": "archived", "contact_id": str(contact_id)}
