from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from typing import Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso_utc(date_str: str) -> datetime:
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_commercial_date(instant: datetime, tz_name: str = "UTC") -> date:
    tz = ZoneInfo(tz_name)
    local_dt = instant.astimezone(tz)
    return local_dt.date()


def format_iso_utc(dt: datetime) -> str:
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat()


def is_within_period(
    instant: datetime,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None
) -> bool:
    target = instant.astimezone(timezone.utc)
    if start_utc and target < start_utc.astimezone(timezone.utc):
        return False
    if end_utc and target > end_utc.astimezone(timezone.utc):
        return False
    return True
