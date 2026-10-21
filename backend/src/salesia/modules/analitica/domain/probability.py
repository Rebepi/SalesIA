import math as math
from dataclasses import dataclass as dataclass
from decimal import ROUND_HALF_EVEN as ROUND_HALF_EVEN
from decimal import Decimal as Decimal
from enum import Enum as Enum
from typing import Any as Any
from typing import Optional as Optional

from salesia.modules.analitica.domain.probabilidades.bayes import (
    calculate_empirical_bayes_full as calculate_empirical_bayes_full,
)
from salesia.modules.analitica.domain.probabilidades.bayes import (
    validate_manual_bayes_inputs as validate_manual_bayes_inputs,
)
from salesia.modules.analitica.domain.probabilidades.configuracion import ALLOWED_EVENT_FIELDS as ALLOWED_EVENT_FIELDS
from salesia.modules.analitica.domain.probabilidades.configuracion import ALLOWED_OPERATORS as ALLOWED_OPERATORS
from salesia.modules.analitica.domain.probabilidades.configuracion import (
    DISALLOWED_PREDICTOR_FIELDS as DISALLOWED_PREDICTOR_FIELDS,
)
from salesia.modules.analitica.domain.probabilidades.configuracion import (
    DISALLOWED_SQL_PATTERNS as DISALLOWED_SQL_PATTERNS,
)
from salesia.modules.analitica.domain.probabilidades.definiciones import EventDefinition as EventDefinition
from salesia.modules.analitica.domain.probabilidades.definiciones import StructuredCondition as StructuredCondition
from salesia.modules.analitica.domain.probabilidades.definiciones import UniverseDefinition as UniverseDefinition
from salesia.modules.analitica.domain.probabilidades.definiciones import UniverseEntity as UniverseEntity
from salesia.modules.analitica.domain.probabilidades.eventos import (
    calculate_empirical_probability as calculate_empirical_probability,
)
from salesia.modules.analitica.domain.probabilidades.eventos import (
    validate_structured_condition as validate_structured_condition,
)
from salesia.modules.analitica.domain.probabilidades.eventos import (
    validate_temporal_leakage as validate_temporal_leakage,
)
from salesia.modules.analitica.domain.probabilidades.hipotesis import (
    run_two_proportions_hypothesis_test as run_two_proportions_hypothesis_test,
)
from salesia.shared.domain.exceptions import EmptySampleException as EmptySampleException
from salesia.shared.domain.exceptions import InvariantViolationException as InvariantViolationException
from salesia.shared.domain.exceptions import ZeroEvidenceException as ZeroEvidenceException
