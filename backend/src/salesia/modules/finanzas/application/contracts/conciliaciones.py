from datetime import datetime

from pydantic import BaseModel, Field

from salesia.modules.finanzas.application.contracts.comunes import ReconciliationLine


class ReconciliationCreateRequest(BaseModel):
    period_start: datetime

    period_end: datetime

    external_lines: list[ReconciliationLine]


class ReconciliationResolveRequest(BaseModel):
    resolution_action: str = Field(..., min_length=3, max_length=255)
