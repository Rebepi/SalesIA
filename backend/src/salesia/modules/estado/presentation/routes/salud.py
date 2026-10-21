from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

import salesia.modules.estado.application.salud as service_salud
from salesia.modules.estado.application.contracts.salud import HealthResponse, ReadinessResponse
from salesia.shared.infrastructure.database import get_db_session

router = APIRouter(prefix="/health")


@router.get("", response_model=HealthResponse, deprecated=True)
async def check_health_legacy(response: Response):
    return await service_salud.check_health_legacy(response=response)


@router.get("/live", response_model=HealthResponse)
async def check_health_live():
    return await service_salud.check_health_live()


@router.get("/ready", response_model=ReadinessResponse)
async def check_readiness(session: AsyncSession = Depends(get_db_session)):
    return await service_salud.check_readiness(session=session)
