import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel, DeliveryVehicleModel
from salesia.modules.inventario.infrastructure_models import DeliveryShipment, SupplyDocument
from salesia.modules.inventario.service import document, warehouse
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import ProductModel, UserModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number

ACTIVE = ("draft", "planned", "in_progress")
DELIVERABLE = ("ready", "dispatched", "in_transit", "out_for_delivery", "incident", "failed_attempt", "partially_delivered", "pending_redelivery")


class VehicleRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=255)
    max_weight_kg: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    max_volume_m3: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    is_active: bool = True
    reason: str = Field(min_length=5, max_length=2000)


class RouteStop(BaseModel):
    delivery_id: UUID
    weight_kg: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    volume_m3: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    notes: str = Field(default="", max_length=1000)


class RouteRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    service_date: date
    zone: str = Field(min_length=2, max_length=128)
    vehicle_id: UUID
    responsible_id: UUID
    warehouse_id: UUID
    stops: list[RouteStop] = Field(min_length=1, max_length=100)
    notes: str = Field(default="", max_length=4000)
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def unique_stops(self):
        if len({item.delivery_id for item in self.stops}) != len(self.stops):
            raise ValueError("Cada entrega debe figurar una sola vez en el recorrido.")
        return self


class RouteAction(BaseModel):
    version: int = Field(ge=1)
    action: Literal["plan", "start", "complete", "cancel", "reopen"]
    reason: str = Field(min_length=5, max_length=2000)


def scoped(db, user, model, identifier, lock=False):
    query = select(model).where(model.company_id == user.company_id, model.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Registro logístico no encontrado en la empresa activa.")
    return row


def audit(db, user, row, action, data):
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type=type(row).__name__, entity_id=row.id, diff=data)


def vehicle_data(row):
    return {"id": str(row.id), "code": row.code, "name": row.name, "max_weight_kg": str(row.max_weight_kg), "max_volume_m3": str(row.max_volume_m3), "is_active": row.is_active, "version": row.version}


def load_totals(stops):
    return sum((Decimal(item["weight_kg"]) for item in stops), Decimal("0")), sum((Decimal(item["volume_m3"]) for item in stops), Decimal("0"))


def route_data(db, user, row):
    vehicle = scoped(db, user, DeliveryVehicleModel, row.vehicle_id)
    responsible = db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == row.responsible_id))
    stops = json.loads(row.stops_json)
    weight, volume = load_totals(stops)
    for stop in stops:
        delivery = document(db, user, "DELIVERY", UUID(stop["delivery_id"]), lock=False)
        stop["current_status"] = delivery.status
        stop["current_version"] = delivery.version
    return {"id": str(row.id), "code": row.code, "service_date": row.service_date.isoformat(), "zone": row.zone, "vehicle": vehicle_data(vehicle), "responsible_id": str(row.responsible_id), "responsible_name": (responsible.full_name or responsible.email) if responsible else "Responsable histórico", "warehouse_id": str(row.warehouse_id), "status": row.status, "version": row.version, "stops": stops, "total_weight_kg": str(weight), "total_volume_m3": str(volume), "weight_available_kg": str(vehicle.max_weight_kg - weight), "volume_available_m3": str(vehicle.max_volume_m3 - volume), "notes": row.notes, "history": json.loads(row.history_json), "business_date": business_date(db, user.company_id).isoformat()}


def record_history(row, user, action, reason):
    values = json.loads(row.history_json or "[]")
    values.append({"action": action, "reason": reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "version": row.version, "manifest": json.loads(row.stops_json)})
    row.history_json = json.dumps(values)


def save_vehicle(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_vehicle.save:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = scoped(db, user, DeliveryVehicleModel, identifier, True) if identifier else None
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "El vehículo cambió; recarga antes de guardar.")
    code = payload.code.upper()
    existing = db.scalar(select(DeliveryVehicleModel).where(DeliveryVehicleModel.company_id == user.company_id, DeliveryVehicleModel.code == code))
    if existing and (row is None or existing.id != row.id):
        raise HTTPException(409, "El código del vehículo ya está registrado.")
    if row:
        routes = db.scalars(select(DeliveryRouteModel).where(DeliveryRouteModel.company_id == user.company_id, DeliveryRouteModel.vehicle_id == row.id, DeliveryRouteModel.status.in_(ACTIVE))).all()
        for route in routes:
            weight, volume = load_totals(json.loads(route.stops_json))
            if not payload.is_active or weight > payload.max_weight_kg or volume > payload.max_volume_m3:
                raise HTTPException(409, "El vehículo tiene recorridos activos incompatibles con la nueva disponibilidad o capacidad.")
    else:
        row = DeliveryVehicleModel(company_id=user.company_id, version=0)
        db.add(row)
    for name in ("name", "max_weight_kg", "max_volume_m3", "is_active"):
        setattr(row, name, getattr(payload, name))
    row.code, row.version = code, row.version + 1
    db.flush()
    result = vehicle_data(row)
    audit(db, user, row, "SAVE_DELIVERY_VEHICLE", {**result, "reason": payload.reason})
    complete_request(record, result)
    db.commit()
    return result


def validate_route(db, user, payload, exclude_id=None):
    if payload.service_date < business_date(db, user.company_id):
        raise HTTPException(422, "Planifica el recorrido para hoy o una fecha posterior.")
    if not payload.zone.strip():
        raise HTTPException(422, "Identifica la zona de reparto.")
    warehouse(db, user.company_id, payload.warehouse_id)
    vehicle = scoped(db, user, DeliveryVehicleModel, payload.vehicle_id, True)
    responsible = db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == payload.responsible_id, UserModel.is_active.is_(True)))
    if not responsible or not vehicle.is_active:
        raise HTTPException(409, "El responsable y el vehículo deben estar activos en la empresa.")
    routes = db.scalars(select(DeliveryRouteModel).where(DeliveryRouteModel.company_id == user.company_id, DeliveryRouteModel.status.in_(ACTIVE))).all()
    requested = {str(item.delivery_id) for item in payload.stops}
    for route in routes:
        if route.id == exclude_id:
            continue
        if requested.intersection(item["delivery_id"] for item in json.loads(route.stops_json)):
            raise HTTPException(409, f"Una entrega ya está asignada al recorrido {route.code}.")
        if route.service_date == payload.service_date and (route.vehicle_id == payload.vehicle_id or route.responsible_id == payload.responsible_id):
            raise HTTPException(409, f"El vehículo o responsable ya tiene el recorrido {route.code} en esa fecha. Completa o cancela ese recorrido antes de asignarle otro.")
    stops = []
    for index, item in enumerate(payload.stops, 1):
        delivery = document(db, user, "DELIVERY", item.delivery_id)
        shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.company_id == user.company_id, DeliveryShipment.delivery_document_id == item.delivery_id))
        if delivery.status not in DELIVERABLE or delivery.warehouse_id != payload.warehouse_id or shipment is None:
            raise HTTPException(409, "Cada parada debe corresponder a una entrega vigente del mismo almacén con destinatario y dirección.")
        from salesia.modules.inventario.application.ventanas_entrega import reservation_for_delivery, scoped as scoped_window
        from salesia.modules.inventario.infrastructure.models.ventanas_entrega import DeliveryWindowModel
        reservation = reservation_for_delivery(db, user, delivery.id)
        appointment = None
        if reservation:
            reserved_window = scoped_window(db, user, DeliveryWindowModel, reservation.window_id)
            if reserved_window.mode == "pickup":
                raise HTTPException(409, "La entrega tiene un retiro en local. Reprograma su modalidad antes de asignarla a un recorrido de reparto.")
            if reservation.status not in ("booked", "checked_in"):
                raise HTTPException(409, "La entrega tiene una reserva sin atención vigente; reprograma su horario antes de incluirla en el recorrido.")
            if payload.service_date not in (business_date(db, user.company_id, reserved_window.starts_at), business_date(db, user.company_id, reserved_window.ends_at)):
                raise HTTPException(409, "La fecha del recorrido no coincide con la ventana de entrega pactada.")
            appointment = {"starts_at": reserved_window.starts_at.isoformat(), "ends_at": reserved_window.ends_at.isoformat(), "requirements": reservation.requirements_snapshot, "reservation_version": reservation.version}
        products = []
        for line in delivery.lines:
            product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == line.product_id))
            products.append({"product_id": str(line.product_id), "name": product.name if product else "Producto histórico", "sku": product.sku if product else "", "quantity": str(line.quantity)})
        stops.append({"sequence": index, "delivery_id": str(item.delivery_id), "delivery_version": delivery.version, "recipient_name": shipment.recipient_name, "address": shipment.delivery_address, "phone": shipment.recipient_phone, "weight_kg": str(item.weight_kg), "volume_m3": str(item.volume_m3), "notes": item.notes, "products": products, "appointment": appointment})
    weight, volume = load_totals(stops)
    if weight > vehicle.max_weight_kg or volume > vehicle.max_volume_m3:
        raise HTTPException(409, "La carga supera la capacidad de peso o volumen del vehículo.")
    return stops


def save_route(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_route.save:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.service_date)
    row = scoped(db, user, DeliveryRouteModel, identifier, True) if identifier else None
    if row and (row.version != payload.version or row.status not in ("draft", "planned")):
        raise HTTPException(409, "El recorrido cambió o ya está en ejecución.")
    if row is None and payload.version != 0:
        raise HTTPException(409, "Un recorrido nuevo comienza en la versión cero.")
    stops = validate_route(db, user, payload, identifier)
    if row is None:
        row = DeliveryRouteModel(company_id=user.company_id, code=f"REC-{next_number(db, user.company_id, 'REC'):08d}", created_by=user.user_id, status="draft", version=0, history_json="[]")
        db.add(row)
    for name in ("service_date", "zone", "vehicle_id", "responsible_id", "warehouse_id", "notes"):
        setattr(row, name, getattr(payload, name))
    row.stops_json, row.status, row.version = json.dumps(stops), "draft", row.version + 1
    record_history(row, user, "SAVE", payload.reason)
    db.flush()
    result = route_data(db, user, row)
    audit(db, user, row, "SAVE_DELIVERY_ROUTE", {"reason": payload.reason, "manifest": stops, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def route_action(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_route.action:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = scoped(db, user, DeliveryRouteModel, identifier, True)
    if row.version != payload.version:
        raise HTTPException(409, "El recorrido cambió; recarga su manifiesto.")
    allowed = {"plan": (("draft",), "planned"), "start": (("planned",), "in_progress"), "complete": (("in_progress",), "completed"), "cancel": (("draft", "planned", "in_progress"), "cancelled"), "reopen": (("cancelled",), "draft")}
    initial, target = allowed[payload.action]
    if row.status not in initial:
        raise HTTPException(409, "El estado del recorrido no admite esta transición.")
    stops = json.loads(row.stops_json)
    if payload.action in ("plan", "start", "reopen"):
        request = RouteRequest(service_date=row.service_date, zone=row.zone, vehicle_id=row.vehicle_id, responsible_id=row.responsible_id, warehouse_id=row.warehouse_id, stops=[RouteStop(**item) for item in stops], reason=payload.reason)
        fresh = validate_route(db, user, request, row.id)
        if payload.action == "start":
            if row.service_date != business_date(db, user.company_id):
                raise HTTPException(409, "Inicia el recorrido en su fecha de servicio; reprograma la fecha si corresponde.")
            if any(document(db, user, "DELIVERY", UUID(item["delivery_id"]), lock=False).status == "ready" for item in fresh):
                raise HTTPException(409, "Despacha primero cada entrega desde Logística. Iniciar el recorrido no genera movimientos de inventario.")
            if any(item["delivery_version"] != old["delivery_version"] or (item.get("appointment") or {}).get("reservation_version") != (old.get("appointment") or {}).get("reservation_version") for item, old in zip(fresh, stops)):
                raise HTTPException(409, "Las entregas cambiaron desde la planificación. Guarda nuevamente el manifiesto y vuelve a planificarlo.")
        row.stops_json = json.dumps(fresh)
    if payload.action in ("complete", "cancel") and row.status == "in_progress":
        if any(document(db, user, "DELIVERY", UUID(item["delivery_id"]), lock=False).status not in ("delivered", "cancelled", "returned") for item in stops):
            raise HTTPException(409, "Registra primero el resultado y retorno de cada parada antes de cerrar o cancelar el recorrido en ejecución.")
    row.status, row.version = target, row.version + 1
    record_history(row, user, payload.action.upper(), payload.reason)
    result = route_data(db, user, row)
    audit(db, user, row, "CHANGE_DELIVERY_ROUTE", {"action": payload.action, "reason": payload.reason, "status": target, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def list_routes(db, user, status=None, service_date=None, limit=25, offset=0):
    query = select(DeliveryRouteModel).where(DeliveryRouteModel.company_id == user.company_id)
    if status:
        query = query.where(DeliveryRouteModel.status == status)
    if service_date:
        query = query.where(DeliveryRouteModel.service_date == service_date)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(DeliveryRouteModel.service_date.desc(), DeliveryRouteModel.created_at.desc()).offset(offset).limit(limit)).all()
    return {"items": [route_data(db, user, row) for row in rows], "total_count": total, "business_date": business_date(db, user.company_id).isoformat()}


def options(db, user):
    vehicles = db.scalars(select(DeliveryVehicleModel).where(DeliveryVehicleModel.company_id == user.company_id).order_by(DeliveryVehicleModel.code)).all()
    responsible = db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.is_active.is_(True)).order_by(UserModel.full_name, UserModel.email)).all()
    assigned = set()
    for row in db.scalars(select(DeliveryRouteModel).where(DeliveryRouteModel.company_id == user.company_id, DeliveryRouteModel.status.in_(ACTIVE))).all():
        assigned.update(item["delivery_id"] for item in json.loads(row.stops_json))
    rows = db.execute(select(SupplyDocument, DeliveryShipment).join(DeliveryShipment, DeliveryShipment.delivery_document_id == SupplyDocument.id).where(SupplyDocument.company_id == user.company_id, DeliveryShipment.company_id == user.company_id, SupplyDocument.kind == "DELIVERY", SupplyDocument.status.in_(DELIVERABLE)).order_by(SupplyDocument.created_at.desc())).all()
    warehouses = db.scalars(select(WarehouseModel).where(WarehouseModel.company_id == user.company_id, WarehouseModel.is_active.is_(True)).order_by(WarehouseModel.name)).all()
    return {"warehouses": [{"warehouse_id": str(row.id), "name": row.name} for row in warehouses], "vehicles": [vehicle_data(row) for row in vehicles], "responsible": [{"id": str(row.id), "name": row.full_name or row.email} for row in responsible], "deliveries": [{"id": str(row.id), "warehouse_id": str(row.warehouse_id), "recipient_name": shipment.recipient_name, "address": shipment.delivery_address, "status": row.status, "assigned": str(row.id) in assigned} for row, shipment in rows], "business_date": business_date(db, user.company_id).isoformat()}
