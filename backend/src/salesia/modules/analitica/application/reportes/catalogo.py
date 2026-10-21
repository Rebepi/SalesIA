from typing import Any, Optional

from salesia.modules.analitica.application.reportes.configuracion import REPORT_CATALOG


def get_report_catalog(area: Optional[str] = None, format_type: Optional[str] = None) -> list[dict[str, Any]]:
    items = []
    for rep in REPORT_CATALOG:
        if area and rep["area"].lower() != area.lower():
            continue
        if format_type and format_type.lower() not in rep["formats"]:
            continue
        items.append(rep)
    return items
