from datetime import datetime, timezone

from fastapi import HTTPException


def period_bounds(period):

    year, month = (int(value) for value in period.split("-"))

    if month < 1 or month > 12:
        raise HTTPException(422, "Mes inválido.")

    start = datetime(year, month, 1, tzinfo=timezone.utc)

    end = (
        datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    )

    return start, end
