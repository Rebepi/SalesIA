import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.shared.infrastructure.models import BranchModel, CompanyModel
from salesia.shared.infrastructure.transactions import CompanySettings, claim_request, complete_request

DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


class Hours(BaseModel):
    start: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    @model_validator(mode="after")
    def positive(self):
        if self.end <= self.start:
            raise ValueError("El horario debe terminar después del inicio dentro del mismo día. Divida las jornadas nocturnas por fecha.")
        return self


class Holiday(BaseModel):
    day: date
    name: str = Field(min_length=3, max_length=128)
    annual: bool = False


class SpecialDay(BaseModel):
    day: date
    name: str = Field(min_length=3, max_length=128)
    hours: list[Hours] = Field(default_factory=list, max_length=8)


class CalendarRules(BaseModel):
    weekly: dict[Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"], list[Hours]] = Field(default_factory=lambda: {day: [Hours(start="08:00", end="18:00")] if day != "SUN" else [] for day in DAYS})
    cutoff_time: str = Field(default="18:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    holidays: list[Holiday] = Field(default_factory=list, max_length=1000)
    special_days: list[SpecialDay] = Field(default_factory=list, max_length=1000)
    payment_day_basis: Literal["calendar", "business"] = "calendar"
    payment_roll: Literal["none", "next", "previous", "modified_next"] = "none"
    payment_due_time: str = Field(default="23:59", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    delivery_roll: Literal["none", "next", "previous", "modified_next"] = "next"
    reminder_roll: Literal["none", "next", "previous", "modified_next"] = "next"
    enforce_delivery_hours: bool = False

    @model_validator(mode="after")
    def valid_schedule(self):
        if set(self.weekly) != set(DAYS) or not any(self.weekly.values()):
            raise ValueError("Declare los siete días y al menos una jornada de atención por semana.")
        for periods in [*self.weekly.values(), *(row.hours for row in self.special_days)]:
            if len(periods) > 8:
                raise ValueError("Cada día admite hasta ocho tramos de atención.")
            ordered = sorted(periods, key=lambda row: row.start)
            if any(ordered[index].end > ordered[index + 1].start for index in range(len(ordered) - 1)):
                raise ValueError("Los tramos de una jornada no deben superponerse.")
        if len({row.day for row in self.special_days}) != len(self.special_days):
            raise ValueError("No repita fechas de jornadas especiales.")
        holiday_keys = {(row.day.month, row.day.day, None if row.annual else row.day.year) for row in self.holidays}
        if len(holiday_keys) != len(self.holidays):
            raise ValueError("No repita feriados del mismo alcance anual o puntual.")
        return self


class CalendarSave(BaseModel):
    branch_id: UUID | None = None
    expected_version: int = Field(default=0, ge=0)
    expected_company_version: int = Field(default=0, ge=0)
    overrides: dict = Field(default_factory=dict)
    reason: str = Field(min_length=5, max_length=2000)


class DateRequest(BaseModel):
    branch_id: UUID | None = None
    start_at: datetime
    days: int = Field(default=0, ge=0, le=3650)
    purpose: Literal["payment", "delivery", "reminder"] = "delivery"
    basis: Literal["calendar", "business"] | None = None
    roll: Literal["none", "next", "previous", "modified_next"] | None = None
    respect_cutoff: bool = True

    @field_validator("start_at")
    @classmethod
    def zone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("La fecha debe indicar una zona horaria o desfase UTC.")
        if not 1900 <= value.year <= 9900:
            raise ValueError("La fecha debe estar dentro del rango de planificación entre 1900 y 9900.")
        return value


def scope_branch(db, company_id, branch_id):
    if branch_id is None:
        return None
    row = db.scalar(select(BranchModel).where(BranchModel.company_id == company_id, BranchModel.id == branch_id))
    if row is None:
        raise HTTPException(404, "Sede no encontrada en la empresa activa.")
    return row


def latest(db, company_id, branch_id=None):
    return db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "operating_calendar", AnalyticsArtifact.artifact_key == (str(branch_id) if branch_id else "company")).order_by(AnalyticsArtifact.version.desc()).limit(1))


def effective_calendar(db, company_id, branch_id=None):
    branch = scope_branch(db, company_id, branch_id)
    settings = db.get(CompanySettings, company_id)
    saved = json.loads(settings.values_json or "{}") if settings else {}
    company_zone = saved.get("timezone", "America/Lima")
    old = saved.get("business_hours", {})
    defaults = CalendarRules().model_dump(mode="json")
    if old.get("working_days"):
        defaults["weekly"] = {day: [{"start": "08:00", "end": "18:00"}] if day in old["working_days"] else [] for day in DAYS}
    defaults["cutoff_time"] = old.get("cutoff_time", defaults["cutoff_time"])
    company = latest(db, company_id)
    company_values = json.loads(company.data_json)["overrides"] if company else {}
    branch_row = latest(db, company_id, branch_id) if branch_id else None
    branch_values = json.loads(branch_row.data_json)["overrides"] if branch_row else {}
    values = CalendarRules.model_validate({**defaults, **company_values, **branch_values}).model_dump(mode="json")
    zone = branch.timezone if branch else company_zone
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, "La zona horaria de la empresa o sede no es válida.")
    return {"branch_id": str(branch_id) if branch_id else None, "branch_name": branch.name if branch else "Empresa", "timezone": zone, "version": branch_row.version if branch_row else company.version if company and not branch_id else 0, "company_version": company.version if company else 0, "rules": values, "overrides": branch_values if branch_id else company_values, "origins": {key: "branch" if key in branch_values else "company" if key in company_values else "default" for key in values}, "configured": company is not None or branch_row is not None}


def save_calendar(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, f"calendar.save:{payload.branch_id or 'company'}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    current = effective_calendar(db, user.company_id, payload.branch_id)
    if current["version"] != payload.expected_version or current["company_version"] != payload.expected_company_version:
        raise HTTPException(409, "El calendario de la sede o de la empresa cambió. Consulte las reglas vigentes antes de guardar.")
    unknown = set(payload.overrides) - set(CalendarRules.model_fields)
    if unknown:
        raise HTTPException(422, "Solo puede configurar los campos funcionales del calendario.")
    base = effective_calendar(db, user.company_id)["rules"] if payload.branch_id else CalendarRules().model_dump(mode="json")
    try:
        parsed = CalendarRules.model_validate({**base, **payload.overrides}).model_dump(mode="json")
        if payload.branch_id is None:
            branches = db.scalars(select(BranchModel).where(BranchModel.company_id == user.company_id)).all()
            for branch in branches:
                local = latest(db, user.company_id, branch.id)
                if local:
                    CalendarRules.model_validate({**parsed, **json.loads(local.data_json)["overrides"]})
    except ValidationError as error:
        raise HTTPException(422, "; ".join(item["msg"] for item in error.errors()))
    overrides = {key: parsed[key] for key in payload.overrides}
    row = AnalyticsArtifact(company_id=user.company_id, kind="operating_calendar", artifact_key=str(payload.branch_id) if payload.branch_id else "company", version=current["version"] + 1, status="active", data_json=json.dumps({"overrides": overrides, "reason": payload.reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()}), created_by=user.user_id)
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_OPERATING_CALENDAR", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"branch_id": str(payload.branch_id) if payload.branch_id else None, "version": row.version, "overrides": overrides, "reason": payload.reason})
    result = effective_calendar(db, user.company_id, payload.branch_id)
    complete_request(record, result)
    db.commit()
    return result


def day_data(calendar, day):
    rules = calendar["rules"]
    special = next((row for row in rules["special_days"] if row["day"] == day.isoformat()), None)
    if special:
        hours, reason = special["hours"], special["name"]
        source = "special_day"
    else:
        holiday = next((row for row in rules["holidays"] if date.fromisoformat(row["day"]) == day or row["annual"] and date.fromisoformat(row["day"]).month == day.month and date.fromisoformat(row["day"]).day == day.day), None)
        hours = [] if holiday else rules["weekly"][DAYS[day.weekday()]]
        reason = holiday["name"] if holiday else "Horario semanal"
        source = "holiday" if holiday else "weekly"
    return {"date": day.isoformat(), "weekday": DAYS[day.weekday()], "is_working_day": bool(hours), "hours": sorted(hours, key=lambda row: row["start"]), "reason": reason, "source": source}


def nearest_day(calendar, day, direction):
    candidate = day
    for _ in range(3661):
        if day_data(calendar, candidate)["is_working_day"]:
            return candidate
        try:
            candidate += timedelta(days=direction)
        except OverflowError:
            raise HTTPException(422, "El traslado supera el rango de fechas admitido por el calendario.")
    raise HTTPException(409, "El calendario no tiene una fecha hábil dentro del límite de búsqueda de diez años.")


def roll_day(calendar, day, mode):
    if mode == "none" or day_data(calendar, day)["is_working_day"]:
        return day
    shifted = nearest_day(calendar, day, -1 if mode == "previous" else 1)
    if mode == "modified_next" and (shifted.year, shifted.month) != (day.year, day.month):
        shifted = nearest_day(calendar, day, -1)
    return shifted


def local_instant(calendar, day, clock):
    zone = ZoneInfo(calendar["timezone"])
    candidate = datetime.combine(day, time.fromisoformat(clock), tzinfo=zone)
    if candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != candidate.replace(tzinfo=None):
        raise HTTPException(409, "La hora calculada no existe por el cambio horario local. Ajuste el horario configurado.")
    return candidate


def calculate_date(calendar, payload):
    local = payload.start_at.astimezone(ZoneInfo(calendar["timezone"]))
    anchor = local.date()
    cutoff_shift = payload.purpose != "payment" and payload.respect_cutoff and local.strftime("%H:%M") >= calendar["rules"]["cutoff_time"]
    if cutoff_shift:
        anchor = nearest_day(calendar, anchor + timedelta(days=1), 1)
    basis = payload.basis or (calendar["rules"]["payment_day_basis"] if payload.purpose == "payment" else "business")
    if basis == "calendar":
        target = anchor + timedelta(days=payload.days)
    else:
        target = anchor
        remaining = payload.days
        while remaining > 0:
            target += timedelta(days=1)
            if day_data(calendar, target)["is_working_day"]:
                remaining -= 1
            if (target - anchor).days > 20000:
                raise HTTPException(409, "El calendario no permite completar el plazo dentro del límite de búsqueda.")
    before_roll = target
    mode = payload.roll or calendar["rules"][f"{payload.purpose}_roll"]
    target = roll_day(calendar, target, mode)
    hours = day_data(calendar, target)["hours"]
    clock = calendar["rules"]["payment_due_time"] if payload.purpose == "payment" else hours[0]["start"] if hours else local.strftime("%H:%M")
    if payload.days == 0 and not cutoff_shift and target == local.date() and payload.purpose != "payment":
        clock = next((max(period["start"], local.strftime("%H:%M")) for period in hours if period["end"] > local.strftime("%H:%M")), clock)
        if hours and clock < local.strftime("%H:%M"):
            target = nearest_day(calendar, target + timedelta(days=1), 1)
            clock = day_data(calendar, target)["hours"][0]["start"]
    instant = local_instant(calendar, target, clock)
    return {"requested_at": payload.start_at.isoformat(), "local_start": local.isoformat(), "date": target.isoformat(), "at": instant.isoformat(), "utc_at": instant.astimezone(timezone.utc).isoformat(), "basis": basis, "days": payload.days, "roll": mode, "before_roll": before_roll.isoformat(), "after_cutoff": cutoff_shift, "day": day_data(calendar, target), "calendar": calendar, "definition": "Los días se cuentan después de la fecha de inicio. Las jornadas especiales prevalecen sobre feriados y semana. Después del corte, entregas y recordatorios parten del siguiente día hábil. Los vencimientos conservan su base de días y regla de traslado específicas."}


def validate_delivery_interval(db, company_id, branch_id, start, end):
    calendar = effective_calendar(db, company_id, branch_id)
    if not calendar["rules"]["enforce_delivery_hours"]:
        return calendar
    zone = ZoneInfo(calendar["timezone"])
    local_start, local_end = start.astimezone(zone), end.astimezone(zone)
    if local_start.date() != local_end.date():
        raise HTTPException(422, "La franja debe estar dentro de una jornada del calendario de la sede.")
    periods = day_data(calendar, local_start.date())["hours"]
    if not any(local_instant(calendar, local_start.date(), period["start"]) <= local_start < local_end <= local_instant(calendar, local_start.date(), period["end"]) for period in periods):
        raise HTTPException(409, "La franja está fuera de la atención del calendario de la sede. Configure una jornada especial o elija un horario hábil.")
    return calendar
