from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

import salesia.modules.operaciones.application.eventos as service_eventos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.get("/events/stream")
async def stream_events(
    cursor: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    request: Request = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
):

    return await service_eventos.stream_events(cursor=cursor, limit=limit, request=request, current_user=current_user)
