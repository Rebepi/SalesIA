import hashlib as hashlib
import json as json
from datetime import datetime as datetime
from datetime import timedelta as timedelta
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from enum import Enum as Enum
from typing import Any as Any
from typing import Optional as Optional
from uuid import UUID as UUID

from sqlalchemy import func as func
from sqlalchemy import select as select
from sqlalchemy.orm import Session as Session

from salesia.modules.analitica.domain.datasets.calidad_privacidad import (
    build_data_quality_report as build_data_quality_report,
)
from salesia.modules.analitica.domain.datasets.calidad_privacidad import mask_sensitive_row as mask_sensitive_row
from salesia.modules.analitica.domain.datasets.definiciones import DatasetGrain as DatasetGrain
from salesia.modules.analitica.domain.datasets.definiciones import DatasetScopeType as DatasetScopeType
from salesia.modules.analitica.domain.datasets.definiciones import DatasetStatus as DatasetStatus
from salesia.modules.analitica.domain.datasets.extraccion import (
    extract_operational_dataset_rows as extract_operational_dataset_rows,
)
from salesia.modules.analitica.domain.datasets.huellas import compute_deterministic_hash as compute_deterministic_hash
from salesia.modules.analitica.domain.datasets.huellas import serialize_canonical as serialize_canonical
from salesia.modules.analitica.domain.datasets.transformaciones import (
    apply_variable_transformations as apply_variable_transformations,
)
from salesia.shared.infrastructure.models import KardexMovementModel as KardexMovementModel
from salesia.shared.infrastructure.models import PaymentModel as PaymentModel
from salesia.shared.infrastructure.models import ProductModel as ProductModel
from salesia.shared.infrastructure.models import SaleLineModel as SaleLineModel
from salesia.shared.infrastructure.models import SaleModel as SaleModel
