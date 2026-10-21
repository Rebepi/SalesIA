from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import direcciones as service
from salesia.modules.clientes.application.contracts.contactos import CustomerAddressCreateModel
from salesia.modules.clientes.application.contracts.contactos import CustomerAddressUpdateModel
from salesia.modules.clientes.application.contactos_edicion import edit_customer_detail
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.put("/{customer_id}/addresses/{address_id}")
def update_customer_address(customer_id: UUID, address_id: UUID, req: CustomerAddressUpdateModel, current_user: AuthenticatedUser = Depends(require_permission("customers:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return edit_customer_detail(db, current_user, customer_id, address_id, req, "address", key)


@router.get("/{customer_id}/addresses")
def list_customer_addresses(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_customer_addresses(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/addresses", status_code=status.HTTP_201_CREATED)
def create_customer_address(
    customer_id: UUID,
    req: CustomerAddressCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_address(customer_id=customer_id, req=req, current_user=current_user, db=db)


@router.delete("/{customer_id}/addresses/{address_id}")
def delete_customer_address(
    customer_id: UUID,
    address_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.delete_customer_address(
        customer_id=customer_id, address_id=address_id, current_user=current_user, db=db
    )
