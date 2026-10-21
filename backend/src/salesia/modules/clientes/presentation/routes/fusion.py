from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import fusion as service
from salesia.modules.clientes.application.contracts.duplicados import CustomerMergeModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.post("/merge/preview")
def preview_customer_merge(
    req: CustomerMergeModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.preview_customer_merge(req=req, current_user=current_user, db=db)


@router.post("/merge")
def merge_customers(
    req: CustomerMergeModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.merge_customers(req=req, current_user=current_user, db=db)
