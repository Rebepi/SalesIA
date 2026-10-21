from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import Boolean as Boolean
from sqlalchemy import DateTime as DateTime
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import Integer as Integer
from sqlalchemy import Numeric as Numeric
from sqlalchemy import String as String
from sqlalchemy import Text as Text
from sqlalchemy import UniqueConstraint as UniqueConstraint
from sqlalchemy.orm import Mapped as Mapped
from sqlalchemy.orm import mapped_column as mapped_column

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact as AnalyticsArtifact
from salesia.modules.auditoria.infrastructure.models.registros import LegalHold as LegalHold
from salesia.modules.operaciones.infrastructure.models.colaboracion import (
    CollaborationApproval as CollaborationApproval,
)
from salesia.modules.operaciones.infrastructure.models.colaboracion import CollaborationComment as CollaborationComment
from salesia.modules.operaciones.infrastructure.models.colaboracion import CollaborationTask as CollaborationTask
from salesia.modules.operaciones.infrastructure.models.colaboracion import (
    ContextualHelpArticle as ContextualHelpArticle,
)
from salesia.modules.operaciones.infrastructure.models.colaboracion import SavedView as SavedView
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    IntegrationConnection as IntegrationConnection,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import Notification as Notification
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    NotificationPreference as NotificationPreference,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import OperationSetting as OperationSetting
from salesia.modules.operaciones.infrastructure.models.infraestructura import UploadGrant as UploadGrant
from salesia.modules.operaciones.infrastructure.models.infraestructura import WebhookReceipt as WebhookReceipt
from salesia.modules.seguridad.infrastructure.models.identidad import ApiCredential as ApiCredential
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionSettlement as CommissionSettlement
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesRepresentative as SalesRepresentative
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesTarget as SalesTarget
from salesia.shared.infrastructure.database import Base as Base
