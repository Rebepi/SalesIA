from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import Boolean as Boolean
from sqlalchemy import DateTime as DateTime
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import ForeignKeyConstraint as ForeignKeyConstraint
from sqlalchemy import Integer as Integer
from sqlalchemy import Numeric as Numeric
from sqlalchemy import String as String
from sqlalchemy import Text as Text
from sqlalchemy import UniqueConstraint as UniqueConstraint
from sqlalchemy.orm import Mapped as Mapped
from sqlalchemy.orm import mapped_column as mapped_column
from sqlalchemy.orm import relationship as relationship

from salesia.modules.inventario.infrastructure.models.compras import LandedCostAdjustment as LandedCostAdjustment
from salesia.modules.inventario.infrastructure.models.compras import PurchaseInvoiceMatch as PurchaseInvoiceMatch
from salesia.modules.inventario.infrastructure.models.compras import Supplier as Supplier
from salesia.modules.inventario.infrastructure.models.compras import SupplyDocument as SupplyDocument
from salesia.modules.inventario.infrastructure.models.compras import SupplyLine as SupplyLine
from salesia.modules.inventario.infrastructure.models.conteos_preparacion import (
    InventoryPickingLine as InventoryPickingLine,
)
from salesia.modules.inventario.infrastructure.models.conteos_preparacion import (
    InventoryPickingList as InventoryPickingList,
)
from salesia.modules.inventario.infrastructure.models.conteos_preparacion import PhysicalCountLine as PhysicalCountLine
from salesia.modules.inventario.infrastructure.models.conteos_preparacion import (
    PhysicalCountSession as PhysicalCountSession,
)
from salesia.modules.inventario.infrastructure.models.entregas import DeliveryIncident as DeliveryIncident
from salesia.modules.inventario.infrastructure.models.entregas import DeliveryShipment as DeliveryShipment
from salesia.modules.inventario.infrastructure.models.entregas import DeliveryTrackingEvent as DeliveryTrackingEvent
from salesia.modules.inventario.infrastructure.models.entregas import ProofOfDelivery as ProofOfDelivery
from salesia.modules.inventario.infrastructure.models.existencias import InventoryAlert as InventoryAlert
from salesia.modules.inventario.infrastructure.models.existencias import (
    InventoryReconciliation as InventoryReconciliation,
)
from salesia.modules.inventario.infrastructure.models.existencias import InventoryReservation as InventoryReservation
from salesia.modules.inventario.infrastructure.models.existencias import (
    InventoryValuationSetting as InventoryValuationSetting,
)
from salesia.modules.inventario.infrastructure.models.existencias import LocationStock as LocationStock
from salesia.modules.inventario.infrastructure.models.existencias import StockRule as StockRule
from salesia.modules.inventario.infrastructure.models.existencias import WarehouseLocation as WarehouseLocation
from salesia.modules.inventario.infrastructure.models.seguimiento import InventoryLot as InventoryLot
from salesia.modules.inventario.infrastructure.models.seguimiento import InventoryQuarantine as InventoryQuarantine
from salesia.modules.inventario.infrastructure.models.seguimiento import InventorySerial as InventorySerial
from salesia.shared.infrastructure.database import Base as Base
from salesia.shared.infrastructure.database import TimestampMixin as TimestampMixin
