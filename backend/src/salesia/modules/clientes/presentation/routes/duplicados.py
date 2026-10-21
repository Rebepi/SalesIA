from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import duplicados as service
from salesia.modules.clientes.application.contracts.duplicados import DuplicateCheckRequest, FiscalValidationRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/duplicates")
def detect_duplicates(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.detect_duplicates(current_user=current_user, db=db)


@router.post("/duplicates/check")
def check_duplicate_candidate(
    req: DuplicateCheckRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.check_duplicate_candidate(req=req, current_user=current_user, db=db)


@router.post("/fiscal/validate")
def validate_fiscal_identity(req: FiscalValidationRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    return service.validate_fiscal_identity(req=req, current_user=current_user)
