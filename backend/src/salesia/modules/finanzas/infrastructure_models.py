from datetime import datetime as datetime
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import Boolean as Boolean
from sqlalchemy import DateTime as DateTime
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import Numeric as Numeric
from sqlalchemy import String as String
from sqlalchemy import Text as Text
from sqlalchemy import UniqueConstraint as UniqueConstraint
from sqlalchemy.orm import Mapped as Mapped
from sqlalchemy.orm import mapped_column as mapped_column
from sqlalchemy.orm import relationship as relationship

from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import (
    CreditNoteLineModel as CreditNoteLineModel,
)
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CreditNoteModel as CreditNoteModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import (
    CustomerCreditMovementModel as CustomerCreditMovementModel,
)
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnLineModel as ReturnLineModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnModel as ReturnModel
from salesia.modules.finanzas.infrastructure.models.pagos import (
    FinanceReconciliationItemModel as FinanceReconciliationItemModel,
)
from salesia.modules.finanzas.infrastructure.models.pagos import (
    FinanceReconciliationModel as FinanceReconciliationModel,
)
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel as PaymentAllocationModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentDisputeModel as PaymentDisputeModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentIntentModel as PaymentIntentModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentMethodConfigModel as PaymentMethodConfigModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentReversalModel as PaymentReversalModel
from salesia.modules.finanzas.infrastructure.models.pagos import TransferProofModel as TransferProofModel
from salesia.shared.infrastructure.database import Base as Base
from salesia.shared.infrastructure.database import TimestampMixin as TimestampMixin
