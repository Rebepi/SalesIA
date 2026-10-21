from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.variables_aleatorias as service_variables_aleatorias
from salesia.modules.analitica.application.contracts.variables_aleatorias import VariableAnalyzeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/random-variables/analyze")
async def post_analyze_variable(
    payload: VariableAnalyzeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return await service_variables_aleatorias.post_analyze_variable(payload=payload, current_user=current_user, db=db)
