from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.busqueda as service_busqueda
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/search")
def unified_search(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    types: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_busqueda.unified_search(
        q=q, limit=limit, offset=offset, types=types, current_user=current_user, db=db
    )
