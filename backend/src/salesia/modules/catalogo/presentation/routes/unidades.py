from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.unidades as service_unidades
from salesia.modules.catalogo.application.contracts.unidades import (
    UnitConversionCreateModel,
    UnitConvertRequest,
    UnitCreateModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/units")
def list_units(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_unidades.list_units(current_user=current_user, db=db)


@router.post("/units", status_code=status.HTTP_201_CREATED)
def create_unit(
    req: UnitCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_unidades.create_unit(req=req, current_user=current_user, db=db)


@router.post("/units/conversions", status_code=status.HTTP_201_CREATED)
def create_unit_conversion(
    req: UnitConversionCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_unidades.create_unit_conversion(req=req, current_user=current_user, db=db)


@router.get("/units/conversions")
def list_unit_conversions(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_unidades.list_unit_conversions(current_user=current_user, db=db)


@router.post("/units/convert")
def convert_unit_endpoint(
    req: UnitConvertRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_unidades.convert_unit_endpoint(req=req, current_user=current_user, db=db)
