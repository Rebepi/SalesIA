import math as math
from dataclasses import dataclass as dataclass
from decimal import ROUND_HALF_EVEN as ROUND_HALF_EVEN
from decimal import Decimal as Decimal
from decimal import InvalidOperation as InvalidOperation
from enum import Enum as Enum
from typing import Any as Any
from typing import Optional as Optional
from typing import Sequence as Sequence

from salesia.modules.analitica.domain.estadistica.bayes import calculate_bayes as calculate_bayes
from salesia.modules.analitica.domain.estadistica.bayes import calculate_bayes_full as calculate_bayes_full
from salesia.modules.analitica.domain.estadistica.bayes import calculate_smoothed_bayes as calculate_smoothed_bayes
from salesia.modules.analitica.domain.estadistica.configuracion import ALGORITHM_VERSION as ALGORITHM_VERSION
from salesia.modules.analitica.domain.estadistica.configuracion import (
    DEFAULT_DECIMAL_PRECISION as DEFAULT_DECIMAL_PRECISION,
)
from salesia.modules.analitica.domain.estadistica.configuracion import (
    MAX_SYNC_CALCULATION_SIZE as MAX_SYNC_CALCULATION_SIZE,
)
from salesia.modules.analitica.domain.estadistica.configuracion import ROUNDING_MODE as ROUNDING_MODE
from salesia.modules.analitica.domain.estadistica.dispersion import analyze_extreme_values as analyze_extreme_values
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_mean as calculate_mean
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_median as calculate_median
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_median_exact as calculate_median_exact
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_quantiles as calculate_quantiles
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_stdev as calculate_stdev
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_variance as calculate_variance
from salesia.modules.analitica.domain.estadistica.dispersion import calculate_weighted_mean as calculate_weighted_mean
from salesia.modules.analitica.domain.estadistica.dispersion import compare_mean_median as compare_mean_median
from salesia.modules.analitica.domain.estadistica.dispersion import (
    compute_descriptive_summary as compute_descriptive_summary,
)
from salesia.modules.analitica.domain.estadistica.dispersion import (
    compute_statistical_summary as compute_statistical_summary,
)
from salesia.modules.analitica.domain.estadistica.distribuciones import calculate_distribution as calculate_distribution
from salesia.modules.analitica.domain.estadistica.distribuciones import calculate_frequencies as calculate_frequencies
from salesia.modules.analitica.domain.estadistica.tipos import BayesResult as BayesResult
from salesia.modules.analitica.domain.estadistica.tipos import CommercialUniverse as CommercialUniverse
from salesia.modules.analitica.domain.estadistica.tipos import StatisticalSummary as StatisticalSummary
from salesia.modules.analitica.domain.estadistica.tipos import VariableScale as VariableScale
from salesia.modules.analitica.domain.estadistica.validacion import classify_variable as classify_variable
from salesia.modules.analitica.domain.estadistica.validacion import sanitize_numeric_values as sanitize_numeric_values
from salesia.modules.analitica.domain.estadistica.validacion import (
    validate_universe_consistency as validate_universe_consistency,
)
from salesia.modules.analitica.domain.estadistica.validacion import (
    validate_variable_scale_for_mean as validate_variable_scale_for_mean,
)
from salesia.modules.analitica.domain.estadistica.variables_aleatorias import (
    analyze_continuous_random_variable as analyze_continuous_random_variable,
)
from salesia.modules.analitica.domain.estadistica.variables_aleatorias import (
    analyze_discrete_random_variable as analyze_discrete_random_variable,
)
from salesia.shared.domain.exceptions import EmptySampleException as EmptySampleException
from salesia.shared.domain.exceptions import IncompatibleVariableScaleException as IncompatibleVariableScaleException
from salesia.shared.domain.exceptions import InvariantViolationException as InvariantViolationException
from salesia.shared.domain.exceptions import ZeroEvidenceException as ZeroEvidenceException
