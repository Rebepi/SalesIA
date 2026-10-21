from fastapi import APIRouter

from salesia.modules.estado.application.contracts.salud import HealthResponse as HealthResponse
from salesia.modules.estado.application.contracts.salud import ReadinessResponse as ReadinessResponse
from salesia.modules.estado.presentation.routes import salud

router = APIRouter(tags=["Salud del Sistema"])
router.include_router(salud.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "check_health_legacy",
            "check_health_live",
            "check_readiness",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
check_health_legacy = salud.check_health_legacy
check_health_live = salud.check_health_live
check_readiness = salud.check_readiness
