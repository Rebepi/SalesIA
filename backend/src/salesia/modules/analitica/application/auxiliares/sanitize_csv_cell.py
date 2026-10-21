from typing import Any


def _sanitize_csv_cell(val: Any) -> str:

    if val is None:
        return ""

    s = str(val)

    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s

    if any(c in s for c in (",", '"', "\n", "\r")):
        s = '"' + s.replace('"', '""') + '"'

    return s
