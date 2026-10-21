from datetime import datetime, timezone

from fastapi import Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from salesia.modules.estado.application.contracts.salud import HealthResponse, ReadinessResponse
from salesia.shared.infrastructure.config import settings


async def check_health_legacy(response: Response):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Thu, 31 Dec 2026 23:59:59 GMT"
    response.headers["Link"] = '</api/v1/health/live>; rel="successor-version"'
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def check_health_live():
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def check_readiness(session: AsyncSession):
    try:
        await session.execute(text("SELECT 1"))
        return ReadinessResponse(status="ready", database="connected", timestamp=datetime.now(timezone.utc).isoformat())
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
