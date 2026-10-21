import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def serialize_canonical(val: Any) -> Any:
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, (UUID,)):
        return str(val)
    if isinstance(val, (Decimal,)):
        return str(val)
    if isinstance(val, (dict,)):
        return {k: serialize_canonical(v) for k, v in sorted(val.items())}
    if isinstance(val, (list, tuple)):
        return [serialize_canonical(v) for v in val]
    return val


def compute_deterministic_hash(rows: list[dict[str, Any]]) -> str:
    canonical = [
        serialize_canonical(r)
        for r in sorted(
            rows,
            key=lambda x: str(
                x.get("id") or x.get("sale_id") or x.get("line_id") or x.get("movement_id") or x.get("payment_id") or ""
            ),
        )
    ]
    encoded = json.dumps(canonical, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return f"sha256-{hashlib.sha256(encoded).hexdigest()}"
