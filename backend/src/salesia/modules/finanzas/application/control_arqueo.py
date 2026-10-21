import hashlib
import json
from decimal import Decimal

from fastapi import HTTPException


def ledger_fingerprint(row):
    value = {
        "session_id": str(row.id),
        "currency": row.currency,
        "expected_cash": format(Decimal(row.expected_cash).quantize(Decimal("0.000001")), "f"),
        "movements": json.loads(row.movements_json or "[]"),
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def count_control(row):
    value = json.loads(row.count_control_json or "{}")
    if value:
        value["is_current"] = value["ledger_fingerprint"] == ledger_fingerprint(row)
    return value


def require_current_count(row):
    value = count_control(row)
    if not value or not value["is_current"]:
        raise HTTPException(409, "Registre un arqueo actualizado de los movimientos antes de continuar.")
    return value
