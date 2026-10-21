from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.analitica.domain.statistics import VariableScale


class VariableAnalyzeRequest(BaseModel):
    name: str = Field(..., min_length=1)

    scale: VariableScale

    observations: Optional[list[Decimal]] = None

    dataset_id: Optional[UUID] = None

    dataset_version: Optional[int] = None

    variable_name: Optional[str] = None

    support: Optional[list[Decimal]] = None
