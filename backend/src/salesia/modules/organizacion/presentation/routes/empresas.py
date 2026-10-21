from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.organizacion.application.empresas as service_empresas
from salesia.modules.organizacion.application.contracts.empresas import CompanyUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/companies/current")
def get_current_company(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_empresas.get_current_company(current_user=current_user, db=db)


@router.patch("/companies/current")
def update_current_company(
    req: CompanyUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_empresas.update_current_company(req=req, current_user=current_user, db=db)
