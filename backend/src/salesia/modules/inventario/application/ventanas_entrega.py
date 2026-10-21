import json
import unicodedata
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.inventario.infrastructure.models.ventanas_entrega import DeliveryWindowModel, DeliveryWindowReservationModel
from salesia.modules.inventario.infrastructure_models import DeliveryShipment, SupplyDocument
from salesia.modules.inventario.service import document
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import BranchModel, WarehouseModel
from salesia.shared.infrastructure.transactions import CompanySettings, claim_request, complete_request

OCCUPIED = ("booked", "checked_in", "completed", "unfulfilled")
DELIVERY_STATES = ("ready", "dispatched", "in_transit", "out_for_delivery", "failed_attempt", "incident", "partially_delivered", "pending_redelivery")


class WindowRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    branch_id: UUID
    mode: Literal["delivery", "pickup"]
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(ge=1, le=10000)
    requirements: str = Field(default="", max_length=4000)
    identity_required: bool = False
    is_active: bool = True
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("La franja requiere inicio y fin con zona horaria.")
        if not self.starts_at < self.ends_at <= self.starts_at + timedelta(days=1):
            raise ValueError("La franja debe tener duración positiva y de hasta 24 horas.")
        return self


class AuthorizedPerson(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    id_document: str = Field(min_length=3, max_length=64)


class ReservationRequest(BaseModel):
    version: int = Field(default=0, ge=0)
    window_id: UUID
    authorized_people: list[AuthorizedPerson] = Field(default_factory=list, max_length=20)
    notes: str = Field(default="", max_length=4000)
    reason: str = Field(min_length=5, max_length=2000)


class ReservationAction(BaseModel):
    version: int = Field(ge=1)
    action: Literal["check_in", "no_show", "cancel"]
    person_name: str = Field(default="", max_length=255)
    id_document: str = Field(default="", max_length=64)
    requirements_confirmed: bool = False
    outside_window_reason: str = Field(default="", max_length=2000)
    reason: str = Field(min_length=5, max_length=2000)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def normalized(value):
    return " ".join("".join(character for character in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(character)).split())


def doc_number(value):
    return "".join(character for character in value.upper() if character.isalnum())


def scoped(db, user, model, identifier, lock=False):
    query = select(model).where(model.company_id == user.company_id, model.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Franja o reserva no encontrada en la empresa activa.")
    return row


def reservation_for_delivery(db, user, identifier, lock=False):
    query = select(DeliveryWindowReservationModel).where(DeliveryWindowReservationModel.company_id == user.company_id, DeliveryWindowReservationModel.delivery_id == identifier)
    return db.scalar(query.with_for_update() if lock else query)


def event(row, user, action, reason, data=None):
    history = json.loads(row.history_json or "[]")
    history.append({"action": action, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "reason": reason, "version": row.version, **(data or {})})
    row.history_json = json.dumps(history)


def audit(db, user, row, action, data):
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type=type(row).__name__, entity_id=row.id, diff=data)


def occupancy(db, user, identifier):
    current = set(db.scalars(select(DeliveryWindowReservationModel.delivery_id).where(DeliveryWindowReservationModel.company_id == user.company_id, DeliveryWindowReservationModel.window_id == identifier, DeliveryWindowReservationModel.status.in_(OCCUPIED))).all())
    previous = db.execute(select(DeliveryWindowReservationModel.delivery_id, DeliveryWindowReservationModel.history_json).where(DeliveryWindowReservationModel.company_id == user.company_id, DeliveryWindowReservationModel.history_json.contains(str(identifier)))).all()
    for delivery_id, values in previous:
        for entry in json.loads(values or "[]"):
            consumed = entry.get("consumed_window_id") == str(identifier)
            moved_after_attendance = entry.get("previous_window_id") == str(identifier) and entry.get("previous_status") in ("checked_in", "completed", "unfulfilled")
            if consumed or moved_after_attendance:
                current.add(delivery_id)
                break
    return len(current)


def window_data(db, user, row):
    branch = db.scalar(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.id == row.branch_id))
    used = occupancy(db, user, row.id)
    return {"id": str(row.id), "branch_id": str(row.branch_id), "branch_name": branch.name if branch else "Sede histórica", "mode": row.mode, "starts_at": aware(row.starts_at).isoformat(), "ends_at": aware(row.ends_at).isoformat(), "capacity": row.capacity, "occupied": used, "available": max(0, row.capacity - used), "requirements": row.requirements, "identity_required": row.identity_required or row.mode == "pickup", "is_active": row.is_active, "version": row.version, "history": json.loads(row.history_json), "calendar_snapshot": json.loads(row.calendar_snapshot_json) if row.calendar_snapshot_json else None}


def reservation_data(db, user, row):
    if row is None:
        return None
    window = scoped(db, user, DeliveryWindowModel, row.window_id)
    shipment = db.scalar(select(DeliveryShipment).where(DeliveryShipment.company_id == user.company_id, DeliveryShipment.delivery_document_id == row.delivery_id))
    return {"id": str(row.id), "delivery_id": str(row.delivery_id), "recipient_name": shipment.recipient_name if shipment else "Destinatario registrado", "address": shipment.delivery_address if shipment else "", "window": window_data(db, user, window), "status": row.status, "version": row.version, "authorized_people": json.loads(row.authorized_people_json), "requirements": row.requirements_snapshot, "identity_required": row.identity_required, "checked_in_at": aware(row.checked_in_at).isoformat() if row.checked_in_at else None, "checked_in_name": row.checked_in_name, "checked_in_doc": row.checked_in_doc, "completed_at": aware(row.completed_at).isoformat() if row.completed_at else None, "notes": row.notes, "is_overdue": row.status == "booked" and datetime.now(timezone.utc) > aware(window.ends_at), "history": json.loads(row.history_json), "calendar_snapshot": json.loads(window.calendar_snapshot_json) if window.calendar_snapshot_json else None}


def save_window(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_window.save:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    branch = db.scalar(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.id == payload.branch_id, BranchModel.is_active.is_(True)))
    if branch is None:
        raise HTTPException(422, "Selecciona una sede activa de la empresa.")
    row = scoped(db, user, DeliveryWindowModel, identifier, True) if identifier else None
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "La franja cambió; recarga antes de modificarla.")
    used = occupancy(db, user, row.id) if row else 0
    if payload.capacity < used:
        raise HTTPException(409, "La capacidad no puede ser menor a los cupos ocupados o ya atendidos.")
    changed_schedule = row and (row.branch_id != payload.branch_id or row.mode != payload.mode or aware(row.starts_at) != payload.starts_at or aware(row.ends_at) != payload.ends_at)
    has_reservations = row and db.scalar(select(DeliveryWindowReservationModel.id).where(DeliveryWindowReservationModel.company_id == user.company_id, DeliveryWindowReservationModel.window_id == row.id).limit(1))
    if changed_schedule and has_reservations:
        raise HTTPException(409, "La franja ya tiene historial de reservas. Crea una nueva franja y reprograma las reservas para conservar los horarios pactados.")
    if not payload.is_active and row and db.scalar(select(DeliveryWindowReservationModel.id).where(DeliveryWindowReservationModel.company_id == user.company_id, DeliveryWindowReservationModel.window_id == row.id, DeliveryWindowReservationModel.status.in_(("booked", "checked_in"))).limit(1)):
        raise HTTPException(409, "Reprograma o cancela las reservas pendientes antes de desactivar la franja.")
    if (row is None or changed_schedule) and payload.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(422, "Crea o reprograma franjas que comiencen en el futuro.")
    overlap = select(DeliveryWindowModel).where(DeliveryWindowModel.company_id == user.company_id, DeliveryWindowModel.branch_id == payload.branch_id, DeliveryWindowModel.mode == payload.mode, DeliveryWindowModel.is_active.is_(True), DeliveryWindowModel.starts_at < payload.ends_at, DeliveryWindowModel.ends_at > payload.starts_at)
    if row:
        overlap = overlap.where(DeliveryWindowModel.id != row.id)
    if payload.is_active and db.scalar(overlap):
        raise HTTPException(409, "Hay una franja activa del mismo tipo que se superpone en esa sede. Ajusta la capacidad de esa franja o elige otro horario.")
    from salesia.modules.organizacion.application.calendario_operativo import validate_delivery_interval
    calendar = validate_delivery_interval(db, user.company_id, payload.branch_id, payload.starts_at, payload.ends_at) if payload.is_active and (row is None or changed_schedule) else None
    if row is None:
        row = DeliveryWindowModel(company_id=user.company_id, created_by=user.user_id, version=0, history_json="[]")
        db.add(row)
    if calendar:
        row.calendar_snapshot_json = json.dumps(calendar)
    for name in ("branch_id", "mode", "capacity", "requirements", "is_active"):
        setattr(row, name, getattr(payload, name))
    row.starts_at, row.ends_at = payload.starts_at.astimezone(timezone.utc), payload.ends_at.astimezone(timezone.utc)
    row.identity_required, row.version = payload.identity_required or payload.mode == "pickup", row.version + 1
    event(row, user, "SAVE", payload.reason, {"starts_at": row.starts_at.isoformat(), "ends_at": row.ends_at.isoformat(), "capacity": row.capacity, "requirements": row.requirements, "identity_required": row.identity_required})
    db.flush()
    result = window_data(db, user, row)
    audit(db, user, row, "SAVE_DELIVERY_WINDOW", {"reason": payload.reason, **result})
    complete_request(record, result)
    db.commit()
    return result


def reserve(db, user, delivery_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_window.reserve:{delivery_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    delivery = document(db, user, "DELIVERY", delivery_id)
    if delivery.status not in DELIVERY_STATES:
        raise HTTPException(409, "La entrega ya fue resuelta o no admite reserva de atención.")
    window = scoped(db, user, DeliveryWindowModel, payload.window_id, True)
    warehouse = db.scalar(select(WarehouseModel).where(WarehouseModel.company_id == user.company_id, WarehouseModel.id == delivery.warehouse_id, WarehouseModel.is_active.is_(True)))
    branch = db.scalar(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.id == window.branch_id, BranchModel.is_active.is_(True)))
    if warehouse is None or branch is None or window.branch_id != warehouse.branch_id or not window.is_active:
        raise HTTPException(409, "La franja debe estar activa y pertenecer a la sede del almacén de salida.")
    if aware(window.ends_at) <= datetime.now(timezone.utc):
        raise HTTPException(409, "La franja terminó; elige un nuevo horario.")
    row = reservation_for_delivery(db, user, delivery_id, True)
    if (row.version if row else 0) != payload.version or (row and row.status == "completed"):
        raise HTTPException(409, "La reserva cambió o ya fue atendida por completo.")
    previous_mode = scoped(db, user, DeliveryWindowModel, row.window_id).mode if row else None
    if window.mode == "pickup" and delivery.status != "ready" and previous_mode != "pickup":
        raise HTTPException(409, "Una entrega que ya salió a reparto no se convierte en retiro en local sin resolver primero su retorno físico.")
    from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel
    routes = db.scalars(select(DeliveryRouteModel).where(DeliveryRouteModel.company_id == user.company_id, DeliveryRouteModel.status.in_(("draft", "planned", "in_progress")))).all()
    for route in routes:
        if not any(item["delivery_id"] == str(delivery_id) for item in json.loads(route.stops_json)):
            continue
        if route.status == "in_progress":
            raise HTTPException(409, "La entrega está en un recorrido en ejecución. Resuelve la parada antes de reprogramar su reserva.")
        if window.mode == "pickup" or route.service_date not in (business_date(db, user.company_id, window.starts_at), business_date(db, user.company_id, window.ends_at)):
            raise HTTPException(409, "La nueva reserva no coincide con el recorrido asignado. Retira primero esa parada del manifiesto.")
    consumed_before = row and any(entry.get("consumed_window_id") == str(window.id) or (entry.get("previous_window_id") == str(window.id) and entry.get("previous_status") in ("checked_in", "completed", "unfulfilled")) for entry in json.loads(row.history_json or "[]"))
    extra = 0 if row and ((row.window_id == window.id and row.status in OCCUPIED) or consumed_before) else 1
    if occupancy(db, user, window.id) + extra > window.capacity:
        raise HTTPException(409, "No quedan cupos disponibles en la franja.")
    people, identifiers = [], set()
    for person in payload.authorized_people:
        identifier = doc_number(person.id_document)
        if len(identifier) < 3 or not normalized(person.name) or identifier in identifiers:
            raise HTTPException(422, "Registra personas autorizadas distintas con nombre y documento válidos.")
        identifiers.add(identifier)
        people.append({"name": person.name.strip(), "id_document": identifier})
    if (window.mode == "pickup" or window.identity_required) and not people:
        raise HTTPException(422, "El retiro o entrega con identificación requiere al menos una persona autorizada.")
    old_window = str(row.window_id) if row else None
    previous_status = row.status if row else None
    if row is None:
        row = DeliveryWindowReservationModel(company_id=user.company_id, delivery_id=delivery_id, created_by=user.user_id, version=0, history_json="[]")
        db.add(row)
    row.window_id, row.status, row.version = window.id, "booked", row.version + 1
    row.authorized_people_json, row.notes = json.dumps(people), payload.notes
    row.requirements_snapshot, row.identity_required = window.requirements, window.identity_required or window.mode == "pickup"
    row.checked_in_at, row.checked_in_name, row.checked_in_doc, row.completed_at = None, None, None, None
    event(row, user, "RESCHEDULE" if old_window else "BOOK", payload.reason, {"previous_window_id": old_window, "previous_status": previous_status, "window_id": str(window.id), "mode": window.mode, "starts_at": aware(window.starts_at).isoformat(), "ends_at": aware(window.ends_at).isoformat(), "authorized_people": people, "requirements": row.requirements_snapshot})
    db.flush()
    result = reservation_data(db, user, row)
    audit(db, user, row, "RESERVE_DELIVERY_WINDOW", {"reason": payload.reason, "delivery_id": str(delivery_id), "window_id": str(window.id), "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def validate_person(row, name, identifier):
    people = json.loads(row.authorized_people_json)
    if not normalized(name):
        raise HTTPException(422, "Identifica a la persona que recibe o retira.")
    if row.identity_required and not doc_number(identifier or ""):
        raise HTTPException(422, "El retiro o entrega requiere el documento de la persona autorizada.")
    if people and not any(normalized(person["name"]) == normalized(name) and doc_number(person["id_document"]) == doc_number(identifier or "") for person in people):
        raise HTTPException(403, "El nombre y documento no corresponden a una persona autorizada para esta reserva.")


def act_on_reservation(db, user, delivery_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"delivery_window.action:{delivery_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    document(db, user, "DELIVERY", delivery_id)
    row = reservation_for_delivery(db, user, delivery_id, True)
    if row is None:
        raise HTTPException(404, "La entrega no tiene reserva.")
    if row.version != payload.version or row.status not in ("booked", "checked_in"):
        raise HTTPException(409, "La reserva cambió o no admite esta transición.")
    window = scoped(db, user, DeliveryWindowModel, row.window_id)
    now = datetime.now(timezone.utc)
    if payload.action == "check_in":
        if row.status != "booked":
            raise HTTPException(409, "La atención de esta reserva ya fue iniciada.")
        validate_person(row, payload.person_name, payload.id_document)
        if not payload.requirements_confirmed:
            raise HTTPException(422, "Confirma los requisitos del destinatario antes de iniciar la atención.")
        outside = not aware(window.starts_at) <= now <= aware(window.ends_at)
        if outside and len(payload.outside_window_reason.strip()) < 5:
            raise HTTPException(422, "Documenta el motivo de atención fuera de la franja acordada.")
        if outside and not ({"approvals:manage", "organization:manage"} & set(user.permissions)):
            raise HTTPException(403, "Atender fuera de horario requiere autorización de aprobaciones o administración.")
        row.status, row.checked_in_at = "checked_in", now
        row.checked_in_name, row.checked_in_doc = payload.person_name.strip(), doc_number(payload.id_document)
        details = {"person_name": row.checked_in_name, "id_document": row.checked_in_doc, "outside_window": outside, "outside_window_reason": payload.outside_window_reason, "late_minutes": max(0, int((now - aware(window.ends_at)).total_seconds() // 60)), "requirements_confirmed": True}
    else:
        if payload.action == "no_show" and (row.status != "booked" or now <= aware(window.ends_at)):
            raise HTTPException(409, "Solo registra ausencia después de finalizar la franja y si la atención no comenzó.")
        consumed = row.status == "checked_in"
        row.status = "no_show" if payload.action == "no_show" else "cancelled"
        details = {"window_id": str(window.id), "consumed_window_id": str(window.id) if consumed else None}
    row.version += 1
    event(row, user, payload.action.upper(), payload.reason, details)
    db.flush()
    result = reservation_data(db, user, row)
    audit(db, user, row, "CHANGE_DELIVERY_RESERVATION", {"action": payload.action, "reason": payload.reason, "status": row.status, **details})
    complete_request(record, result)
    db.commit()
    return result


def validate_acceptance(db, user, delivery, name, identifier=None, outside_window_reason=""):
    reservation = reservation_for_delivery(db, user, delivery.id, True)
    if reservation is None:
        return None
    if reservation.status != "checked_in":
        raise HTTPException(409, "La entrega tiene una reserva: inicia su atención y confirma los requisitos antes de registrar unidades aceptadas.")
    validate_person(reservation, name, identifier)
    if normalized(reservation.checked_in_name or "") != normalized(name) or (reservation.checked_in_doc and reservation.checked_in_doc != doc_number(identifier or "")):
        raise HTTPException(409, "La conformidad debe corresponder a la persona cuya atención fue verificada.")
    window = scoped(db, user, DeliveryWindowModel, reservation.window_id)
    now = datetime.now(timezone.utc)
    outside = not aware(window.starts_at) <= now <= aware(window.ends_at)
    attendance = next((entry for entry in reversed(json.loads(reservation.history_json or "[]")) if entry["action"] == "CHECK_IN"), None)
    authorized = bool(attendance and attendance.get("outside_window") and attendance.get("outside_window_reason"))
    if outside and not authorized:
        if not ({"approvals:manage", "organization:manage"} & set(user.permissions)):
            raise HTTPException(403, "La aceptación ocurre fuera de la franja: requiere autorización de administración o aprobaciones.")
        if len(outside_window_reason.strip()) < 5:
            raise HTTPException(422, "Documenta el motivo de aceptación fuera de horario.")
    reason = (outside_window_reason.strip() or (attendance or {}).get("outside_window_reason", "")) if outside else "Aceptación dentro del horario pactado."
    reservation.version += 1
    event(reservation, user, "ACCEPTANCE", reason, {"outside_window": outside, "outside_window_reason": reason if outside else "", "late_minutes": max(0, int((now - aware(window.ends_at)).total_seconds() // 60))})
    audit(db, user, reservation, "ACCEPT_DELIVERY_WINDOW", {"delivery_id": str(delivery.id), "outside_window": outside, "reason": reason})
    return reservation


def complete_reservation(db, user, reservation, delivery):
    if reservation is None:
        return
    if delivery.status in ("delivered", "rejected", "partially_rejected"):
        reservation.status, reservation.completed_at = ("completed" if delivery.status == "delivered" else "unfulfilled"), datetime.now(timezone.utc)
        reservation.version += 1
        event(reservation, user, "COMPLETED" if delivery.status == "delivered" else "UNFULFILLED", "Resultado final de la atención registrado por producto.", {"delivery_status": delivery.status})
        audit(db, user, reservation, "COMPLETE_DELIVERY_RESERVATION", {"delivery_id": str(delivery.id), "status": reservation.status})


def cancel_for_delivery(db, user, delivery):
    reservation = reservation_for_delivery(db, user, delivery.id, True)
    if reservation and reservation.status in ("booked", "checked_in"):
        consumed = reservation.status == "checked_in"
        reservation.status, reservation.version = "cancelled", reservation.version + 1
        event(reservation, user, "CANCEL", "La entrega fue cancelada antes de su salida física.", {"consumed_window_id": str(reservation.window_id) if consumed else None})
        audit(db, user, reservation, "CANCEL_DELIVERY_RESERVATION", {"delivery_id": str(delivery.id), "status": reservation.status})


def list_windows(db, user, branch_id=None, mode=None, on_date=None, limit=25, offset=0):
    query = select(DeliveryWindowModel).where(DeliveryWindowModel.company_id == user.company_id)
    if branch_id:
        query = query.where(DeliveryWindowModel.branch_id == branch_id)
    if mode:
        query = query.where(DeliveryWindowModel.mode == mode)
    if on_date:
        settings = db.get(CompanySettings, user.company_id)
        zone = ZoneInfo(json.loads(settings.values_json or "{}").get("timezone", "America/Lima")) if settings else ZoneInfo("America/Lima")
        start = datetime(on_date.year, on_date.month, on_date.day, tzinfo=zone)
        end = start + timedelta(days=1)
        query = query.where(DeliveryWindowModel.starts_at >= start.astimezone(timezone.utc), DeliveryWindowModel.starts_at < end.astimezone(timezone.utc))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(DeliveryWindowModel.starts_at.desc(), DeliveryWindowModel.id).offset(offset).limit(limit)).all()
    return {"items": [window_data(db, user, row) for row in rows], "total_count": total, "business_date": business_date(db, user.company_id).isoformat()}


def options(db, user):
    branches = db.scalars(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.is_active.is_(True)).order_by(BranchModel.name)).all()
    rows = db.execute(select(SupplyDocument, DeliveryShipment, WarehouseModel).join(DeliveryShipment, DeliveryShipment.delivery_document_id == SupplyDocument.id).join(WarehouseModel, WarehouseModel.id == SupplyDocument.warehouse_id).where(SupplyDocument.company_id == user.company_id, DeliveryShipment.company_id == user.company_id, WarehouseModel.company_id == user.company_id, SupplyDocument.kind == "DELIVERY", SupplyDocument.status.in_(DELIVERY_STATES)).order_by(SupplyDocument.created_at.desc())).all()
    settings = db.get(CompanySettings, user.company_id)
    return {"branches": [{"id": str(row.id), "name": row.name} for row in branches], "deliveries": [{"id": str(row.id), "branch_id": str(warehouse.branch_id), "recipient_name": shipment.recipient_name, "address": shipment.delivery_address, "status": row.status} for row, shipment, warehouse in rows], "timezone": json.loads(settings.values_json or "{}").get("timezone", "America/Lima") if settings else "America/Lima", "business_date": business_date(db, user.company_id).isoformat()}
