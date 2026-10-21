from datetime import datetime, timezone


def quotation_status(row):
    if row.status in ("pending", "negotiating") and row.valid_until:
        expiration = datetime.fromisoformat(row.valid_until)
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)
        if expiration < datetime.now(timezone.utc):
            return "expired"
    return row.status
