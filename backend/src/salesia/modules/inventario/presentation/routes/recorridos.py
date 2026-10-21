from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import recorridos as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Recorridos y capacidad de reparto"])


@router.get("/delivery-route-options")
def route_options(user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.options(db, user)


@router.post("/delivery-vehicles", status_code=201)
def create_vehicle(payload: service.VehicleRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_vehicle(db, user, None, payload, key)


@router.put("/delivery-vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: UUID, payload: service.VehicleRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_vehicle(db, user, vehicle_id, payload, key)


@router.get("/delivery-routes")
def delivery_routes(status: Literal["draft", "planned", "in_progress", "completed", "cancelled"] | None = None, service_date: date | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.list_routes(db, user, status, service_date, limit, offset)


@router.post("/delivery-routes", status_code=201)
def create_route(payload: service.RouteRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_route(db, user, None, payload, key)


@router.get("/delivery-routes/{route_id}")
def get_route(route_id: UUID, user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.route_data(db, user, service.scoped(db, user, service.DeliveryRouteModel, route_id))


@router.put("/delivery-routes/{route_id}")
def update_route(route_id: UUID, payload: service.RouteRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_route(db, user, route_id, payload, key)


@router.post("/delivery-routes/{route_id}/actions")
def route_action(route_id: UUID, payload: service.RouteAction, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.route_action(db, user, route_id, payload, key)
