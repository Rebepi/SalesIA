from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import segmentos as service
from salesia.modules.clientes.application.contracts.comercial import CustomerSegmentCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/segments")
def list_customer_segments(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.list_customer_segments(current_user=current_user, db=db)


@router.post("/segments", status_code=status.HTTP_201_CREATED)
def create_customer_segment(
    req: CustomerSegmentCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_segment(req=req, current_user=current_user, db=db)


@router.get("/{customer_id}/segments")
def evaluate_customer_segments(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.evaluate_customer_segments(customer_id=customer_id, current_user=current_user, db=db)
