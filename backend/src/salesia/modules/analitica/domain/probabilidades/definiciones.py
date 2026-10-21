from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class UniverseEntity(str, Enum):
    SALES = "sales"
    CUSTOMERS = "customers"


@dataclass(frozen=True)
class StructuredCondition:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class EventDefinition:
    name: str
    description: str
    condition: Optional[StructuredCondition] = None


@dataclass(frozen=True)
class UniverseDefinition:
    entity: str
    period: Optional[str] = "30d"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    filters: Optional[dict[str, Any]] = None
    eligibility_criteria: Optional[str] = "confirmadas_activas"
