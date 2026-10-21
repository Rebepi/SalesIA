from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from salesia.shared.domain.datetime_utils import (
    now_utc,
    parse_iso_utc,
    to_commercial_date,
    format_iso_utc,
    is_within_period
)


def test_now_utc_is_aware():
    dt = now_utc()
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc


def test_parse_iso_utc_naive_becomes_utc():
    raw = "2026-10-09T14:30:00"
    dt = parse_iso_utc(raw)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026
    assert dt.hour == 14


def test_to_commercial_date_timezone_handling():
    dt = datetime(2026, 10, 9, 23, 30, tzinfo=timezone.utc)
    comm_date_utc = to_commercial_date(dt, "UTC")
    assert comm_date_utc == date(2026, 10, 9)

    comm_date_lima = to_commercial_date(dt, "America/Lima")
    assert comm_date_lima == date(2026, 10, 9)


def test_format_iso_utc():
    dt = datetime(2026, 10, 9, 12, 0, 0, tzinfo=ZoneInfo("America/Lima"))
    res = format_iso_utc(dt)
    assert res == "2026-10-09T17:00:00+00:00"


def test_is_within_period():
    dt = datetime(2026, 10, 9, 15, 0, tzinfo=timezone.utc)
    start = datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 9, 23, 59, tzinfo=timezone.utc)

    assert is_within_period(dt, start, end)
    assert not is_within_period(datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc), start, end)
    assert not is_within_period(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc), start, end)
