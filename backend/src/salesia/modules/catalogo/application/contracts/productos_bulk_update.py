from typing import Any, Dict

from pydantic import BaseModel

from salesia.modules.catalogo.application.contracts.comunes import BulkUpdateOperation


class BulkUpdateRequest(BaseModel):
    filters: Dict[str, Any] = {}

    operation: BulkUpdateOperation

    preview: bool = True
