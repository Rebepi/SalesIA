from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import importacion as service
from salesia.modules.clientes.application.contracts.archivos import CustomerImportModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/import/template")
def get_import_template():
    return service.get_import_template()


@router.post("/import")
def import_customers(
    req: CustomerImportModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.import_customers(req=req, current_user=current_user, db=db)
