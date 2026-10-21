from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import contactos as service
from salesia.modules.clientes.application.contracts.contactos import CustomerContactCreateModel
from salesia.modules.clientes.application.contracts.contactos import CustomerContactUpdateModel
from salesia.modules.clientes.application.contactos_edicion import edit_customer_detail
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.put("/{customer_id}/contacts/{contact_id}")
def update_customer_contact(customer_id: UUID, contact_id: UUID, req: CustomerContactUpdateModel, current_user: AuthenticatedUser = Depends(require_permission("customers:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return edit_customer_detail(db, current_user, customer_id, contact_id, req, "contact", key)


@router.get("/{customer_id}/contacts")
def list_customer_contacts(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_customer_contacts(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/contacts", status_code=status.HTTP_201_CREATED)
def create_customer_contact(
    customer_id: UUID,
    req: CustomerContactCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_contact(customer_id=customer_id, req=req, current_user=current_user, db=db)


@router.delete("/{customer_id}/contacts/{contact_id}")
def delete_customer_contact(
    customer_id: UUID,
    contact_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.delete_customer_contact(
        customer_id=customer_id, contact_id=contact_id, current_user=current_user, db=db
    )
