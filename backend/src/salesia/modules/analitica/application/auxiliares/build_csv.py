from typing import Any

from salesia.modules.analitica.application.auxiliares.sanitize_csv_cell import _sanitize_csv_cell


def _build_csv(columns: list[str], rows: list[dict[str, Any]]) -> str:

    header = ",".join(_sanitize_csv_cell(c) for c in columns)

    lines = [header]

    for r in rows:
        lines.append(",".join(_sanitize_csv_cell(r.get(c, "")) for c in columns))

    return "\ufeff" + "\r\n".join(lines)
