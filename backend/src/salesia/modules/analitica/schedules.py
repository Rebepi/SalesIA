from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field


class VisualSchedule(BaseModel):
    frequency: Literal["daily", "weekly", "monthly"] = "weekly"
    hour: int = Field(default=8, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    weekday: int = Field(default=1, ge=0, le=6)
    day: int = Field(default=1, ge=1, le=28)
    start_date: date

    def cron(self):
        return f"{self.minute} {self.hour} {self.day if self.frequency == 'monthly' else '*'} * {self.weekday if self.frequency == 'weekly' else '*'}"


def validate_schedule_zone(name):
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Selecciona una zona horaria válida, por ejemplo America/Lima.")


def next_schedule_time(schedule, timezone_name, after):
    config = VisualSchedule.model_validate(schedule)
    zone = validate_schedule_zone(timezone_name)
    current = after.astimezone(zone)
    start = max(current.date(), config.start_date)
    for offset in range(370):
        day = start + timedelta(days=offset)
        if config.frequency == "weekly" and (day.weekday() + 1) % 7 != config.weekday:
            continue
        if config.frequency == "monthly" and day.day != config.day:
            continue
        candidate = datetime.combine(day, time(config.hour, config.minute), tzinfo=zone)
        normalized = candidate.astimezone(timezone.utc).astimezone(zone)
        if normalized.hour != config.hour or normalized.minute != config.minute:
            continue
        if candidate > current:
            return candidate.astimezone(timezone.utc)
    raise ValueError("No se pudo calcular la próxima ejecución de la programación.")
