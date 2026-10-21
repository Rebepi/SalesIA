from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import creacion as service
from salesia.modules.clientes.application.contracts.clientes import CustomerCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer(
    req: CustomerCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer(req=req, current_user=current_user, db=db)


@router.post("/walk-in/ensure")
def ensure_walk_in_customer(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.ensure_walk_in_customer(current_user=current_user, db=db)
