from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import notas as service
from salesia.modules.clientes.application.contracts.comercial import CustomerNoteCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/notes")
def list_customer_notes(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_customer_notes(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/notes", status_code=status.HTTP_201_CREATED)
def create_customer_note(
    customer_id: UUID,
    req: CustomerNoteCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_note(customer_id=customer_id, req=req, current_user=current_user, db=db)


@router.delete("/{customer_id}/notes/{note_id}")
def delete_customer_note(
    customer_id: UUID,
    note_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.delete_customer_note(customer_id=customer_id, note_id=note_id, current_user=current_user, db=db)
