from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import exportacion as service
from salesia.modules.clientes.application.contracts.archivos import CustomerExportModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.post("/export")
def export_customers(
    req: CustomerExportModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:read")),
    db: Session = Depends(get_db),
):
    return service.export_customers(req=req, current_user=current_user, db=db)
