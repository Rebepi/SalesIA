from typing import Any, Optional

from pydantic import BaseModel


class StructuredConditionModel(BaseModel):
    field: str

    operator: str = "eq"

    value: Any = None


class EventDefinitionModel(BaseModel):
    name: str = "Evento"

    description: str = ""

    condition: Optional[StructuredConditionModel] = None


class UniverseDefinitionModel(BaseModel):
    entity: str = "sales"

    period: Optional[str] = "30d"

    start_date: Optional[str] = None

    end_date: Optional[str] = None

    filters: Optional[dict[str, Any]] = None

    eligibility_criteria: Optional[str] = "confirmadas_activas"
