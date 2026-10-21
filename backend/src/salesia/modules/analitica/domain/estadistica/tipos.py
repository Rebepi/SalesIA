from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class VariableScale(str, Enum):
    QUALITATIVE_NOMINAL = "qualitative_nominal"
    QUALITATIVE_ORDINAL = "qualitative_ordinal"
    QUANTITATIVE_DISCRETE = "quantitative_discrete"
    QUANTITATIVE_CONTINUOUS = "quantitative_continuous"


class CommercialUniverse(str, Enum):
    VENTA_ELEGIBLE = "venta_elegible"
    CLIENTE_ACTIVO = "cliente_activo"
    DIA_COMERCIAL = "dia_comercial"


@dataclass(frozen=True)
class StatisticalSummary:
    count: int
    mean: Decimal
    median: Decimal
    minimum: Decimal
    maximum: Decimal
    sum_total: Decimal
    skewness_direction: str
    null_count: int = 0
    distinct_values: int = 0
    explanation: str = ""
    outliers_count: int = 0
    variance: Optional[Decimal] = None
    stdev: Optional[Decimal] = None
    q1: Optional[Decimal] = None
    q3: Optional[Decimal] = None
    iqr: Optional[Decimal] = None
    algorithm_version: str = "v1.2.0"
    tolerance: str = "0.000001"


@dataclass(frozen=True)
class BayesResult:
    prior_a: Decimal
    likelihood_b_given_a: Decimal
    likelihood_b_given_not_a: Decimal
    evidence_b: Decimal
    posterior_a_given_b: Decimal
    interpretation: str
