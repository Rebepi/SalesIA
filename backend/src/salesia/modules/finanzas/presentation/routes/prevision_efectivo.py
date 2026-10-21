from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import prevision_efectivo as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/cash-forecast", tags=["Previsión interna de efectivo"])


@router.get("/view")
def base_cash_forecast(user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.build_forecast(db, user, service.ForecastConfig())


@router.post("/preview")
def preview_cash_forecast(payload: service.ForecastConfig, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.build_forecast(db, user, payload)


@router.get("/scenarios")
def cash_forecast_scenarios(user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.list_scenarios(db, user)


@router.post("/scenarios", status_code=201)
def create_cash_forecast_scenario(payload: service.ScenarioSave, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_scenario(db, user, None, payload, key)


@router.put("/scenarios/{scenario_id}")
def update_cash_forecast_scenario(scenario_id: UUID, payload: service.ScenarioSave, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_scenario(db, user, scenario_id, payload, key)


@router.get("/scenarios/{scenario_id}/history")
def cash_forecast_scenario_history(scenario_id: UUID, user: AuthenticatedUser = Depends(require_permission("cash:register:manage")), db: Session = Depends(get_db)):
    return service.scenario_history(db, user, scenario_id)
