from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import BigInteger as BigInteger
from sqlalchemy import Boolean as Boolean
from sqlalchemy import CheckConstraint as CheckConstraint
from sqlalchemy import DateTime as DateTime
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import ForeignKeyConstraint as ForeignKeyConstraint
from sqlalchemy import Index as Index
from sqlalchemy import Integer as Integer
from sqlalchemy import Numeric as Numeric
from sqlalchemy import String as String
from sqlalchemy import Text as Text
from sqlalchemy import UniqueConstraint as UniqueConstraint
from sqlalchemy import text as text
from sqlalchemy.orm import Mapped as Mapped
from sqlalchemy.orm import mapped_column as mapped_column
from sqlalchemy.orm import relationship as relationship

from salesia.modules.auditoria.infrastructure.models.registros import AuditLogModel as AuditLogModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductModel as ProductModel
from salesia.modules.clientes.infrastructure.models import CustomerActivityModel as CustomerActivityModel
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel as CustomerAddressModel
from salesia.modules.clientes.infrastructure.models import CustomerContactModel as CustomerContactModel
from salesia.modules.clientes.infrastructure.models import CustomerImportBatchModel as CustomerImportBatchModel
from salesia.modules.clientes.infrastructure.models import CustomerLoyaltyLedgerModel as CustomerLoyaltyLedgerModel
from salesia.modules.clientes.infrastructure.models import CustomerModel as CustomerModel
from salesia.modules.clientes.infrastructure.models import CustomerNoteModel as CustomerNoteModel
from salesia.modules.clientes.infrastructure.models import CustomerOpportunityModel as CustomerOpportunityModel
from salesia.modules.clientes.infrastructure.models import CustomerProfileModel as CustomerProfileModel
from salesia.modules.clientes.infrastructure.models import CustomerSegmentModel as CustomerSegmentModel
from salesia.modules.finanzas.infrastructure.models.caja import CashSessionModel as CashSessionModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentModel as PaymentModel
from salesia.modules.inventario.infrastructure.models.existencias import InventoryStockModel as InventoryStockModel
from salesia.modules.inventario.infrastructure.models.existencias import KardexMovementModel as KardexMovementModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import AttachmentModel as AttachmentModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import BackupSnapshotModel as BackupSnapshotModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import DeadLetterJobModel as DeadLetterJobModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    ExternalEntityMappingModel as ExternalEntityMappingModel,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    ExternalNotificationIntentModel as ExternalNotificationIntentModel,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    ExternalSyncCursorModel as ExternalSyncCursorModel,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import InboxEventModel as InboxEventModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import JobModel as JobModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import OutboxEventModel as OutboxEventModel
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    ScheduleExecutionModel as ScheduleExecutionModel,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    WebhookDeliveryModel as WebhookDeliveryModel,
)
from salesia.modules.operaciones.infrastructure.models.infraestructura import (
    WebhookSubscriptionModel as WebhookSubscriptionModel,
)
from salesia.modules.organizacion.infrastructure.models.empresa import CompanyModel as CompanyModel
from salesia.modules.organizacion.infrastructure.models.ubicaciones import BranchModel as BranchModel
from salesia.modules.organizacion.infrastructure.models.ubicaciones import WarehouseModel as WarehouseModel
from salesia.modules.pedidos.infrastructure.models.documentos import OrderModel as OrderModel
from salesia.modules.pedidos.infrastructure.models.documentos import QuotationModel as QuotationModel
from salesia.modules.seguridad.infrastructure.models.identidad import UserModel as UserModel
from salesia.modules.seguridad.infrastructure.models.sesiones import RevokedTokenModel as RevokedTokenModel
from salesia.modules.ventas.infrastructure.models.documentos import SaleLineModel as SaleLineModel
from salesia.modules.ventas.infrastructure.models.documentos import SaleModel as SaleModel
from salesia.shared.infrastructure.database import Base as Base
from salesia.shared.infrastructure.database import TimestampMixin as TimestampMixin
