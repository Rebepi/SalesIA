import json
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.acceso import user_can_read_sensitive
from salesia.modules.clientes.application.contracts.comercial import CustomerNoteCreateModel
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerModel, CustomerNoteModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException, DomainNotFoundException


def list_customer_notes(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    can_sensitive = user_can_read_sensitive(current_user)
    query = select(CustomerNoteModel).where(
        CustomerNoteModel.company_id == current_user.company_id, CustomerNoteModel.customer_id == customer_id
    )
    if not can_sensitive:
        query = query.where(CustomerNoteModel.category == "comercial")

    notes = db.scalars(query.order_by(CustomerNoteModel.created_at.desc())).all()
    return [
        {
            "id": str(n.id),
            "category": n.category,
            "content": n.content,
            "author_email": n.author_email,
            "attachments": json.loads(n.attachments_json),
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]


def create_customer_note(customer_id: UUID, req: CustomerNoteCreateModel, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    if req.category in ("personal", "interno") and not user_can_read_sensitive(current_user):
        raise DomainForbiddenException("Permiso insuficiente para registrar notas internas o personales.")

    clean_content = sanitize_text(req.content)
    if not clean_content:
        raise HTTPException(422, {"field": "content", "rule": "Contenido no puede ser vacío"})

    sanitized_attachments = [sanitize_text(a) for a in (req.attachments or []) if sanitize_text(a)]
    note = CustomerNoteModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        author_id=current_user.user_id,
        author_email=current_user.email,
        category=req.category,
        content=clean_content,
        attachments_json=json.dumps(sanitized_attachments),
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "id": str(note.id),
        "customer_id": str(customer_id),
        "category": note.category,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
    }


def delete_customer_note(customer_id: UUID, note_id: UUID, current_user: AuthenticatedUser, db: Session):
    note = db.scalar(
        select(CustomerNoteModel).where(
            CustomerNoteModel.company_id == current_user.company_id,
            CustomerNoteModel.customer_id == customer_id,
            CustomerNoteModel.id == note_id,
        )
    )
    if not note:
        raise DomainNotFoundException("Nota no encontrada.")

    if note.category in ("personal", "interno") and not user_can_read_sensitive(current_user):
        raise DomainForbiddenException("Permiso insuficiente para eliminar notas restringidas.")

    db.delete(note)
    db.commit()
    return {"status": "deleted", "note_id": str(note_id)}
