from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.analitica_variables as service_analitica_variables
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/analytics/variables")
def get_analytics_variables(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_analitica_variables.get_analytics_variables(current_user=current_user, db=db)
