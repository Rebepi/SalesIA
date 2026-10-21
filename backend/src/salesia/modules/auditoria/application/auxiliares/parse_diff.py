import json
from typing import Any, Optional


def _parse_diff(val: Optional[str]) -> Any:
    if not val:
        return {}
    try:
        return json.loads(val)
    except Exception:
        return val
