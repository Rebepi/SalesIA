from enum import Enum


class DatasetGrain(str, Enum):
    TICKET = "ticket"
    LINES = "lines"
    CUSTOMER_DAILY = "customer_daily"
    PAYMENTS = "payments"
    MOVEMENTS = "movements"


class DatasetScopeType(str, Enum):
    SAMPLE = "sample"
    POPULATION = "population"
    AGGREGATE = "aggregate"


class DatasetStatus(str, Enum):
    ACTIVE = "active"
    IMMUTABLE = "immutable"
    ARCHIVED = "archived"
    EXPIRED = "expired"
