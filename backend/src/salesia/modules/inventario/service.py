import hashlib as hashlib
import json as json
from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import ROUND_HALF_EVEN as ROUND_HALF_EVEN
from decimal import Decimal as Decimal
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from fastapi import HTTPException as HTTPException
from sqlalchemy import func as func
from sqlalchemy import select as select
from sqlalchemy import update as update

from salesia.modules.inventario.application.gestion_stock.conciliacion import recalculate_alerts as recalculate_alerts
from salesia.modules.inventario.application.gestion_stock.conciliacion import reconcile_stock as reconcile_stock
from salesia.modules.inventario.application.gestion_stock.conciliacion import (
    repair_stock_discrepancy as repair_stock_discrepancy,
)
from salesia.modules.inventario.application.gestion_stock.consulta import make_aware as make_aware
from salesia.modules.inventario.application.gestion_stock.consulta import product as product
from salesia.modules.inventario.application.gestion_stock.consulta import record_audit as record_audit
from salesia.modules.inventario.application.gestion_stock.consulta import warehouse as warehouse
from salesia.modules.inventario.application.gestion_stock.conteos import (
    approve_physical_count_session as approve_physical_count_session,
)
from salesia.modules.inventario.application.gestion_stock.conteos import (
    create_physical_count_session as create_physical_count_session,
)
from salesia.modules.inventario.application.gestion_stock.documentos import create_document as create_document
from salesia.modules.inventario.application.gestion_stock.documentos import document as document
from salesia.modules.inventario.application.gestion_stock.documentos import response as response
from salesia.modules.inventario.application.gestion_stock.documentos import transition as transition
from salesia.modules.inventario.application.gestion_stock.movimientos import (
    move_between_locations as move_between_locations,
)
from salesia.modules.inventario.application.gestion_stock.movimientos import move_stock as move_stock
from salesia.modules.inventario.application.gestion_stock.reservas import consume_reservation as consume_reservation
from salesia.modules.inventario.application.gestion_stock.reservas import release_reservation as release_reservation
from salesia.modules.inventario.application.gestion_stock.reservas import reserve_stock as reserve_stock
from salesia.modules.inventario.infrastructure_models import InventoryAlert as InventoryAlert
from salesia.modules.inventario.infrastructure_models import InventoryLot as InventoryLot
from salesia.modules.inventario.infrastructure_models import InventoryReconciliation as InventoryReconciliation
from salesia.modules.inventario.infrastructure_models import InventoryReservation as InventoryReservation
from salesia.modules.inventario.infrastructure_models import LocationStock as LocationStock
from salesia.modules.inventario.infrastructure_models import PhysicalCountLine as PhysicalCountLine
from salesia.modules.inventario.infrastructure_models import PhysicalCountSession as PhysicalCountSession
from salesia.modules.inventario.infrastructure_models import StockRule as StockRule
from salesia.modules.inventario.infrastructure_models import SupplyDocument as SupplyDocument
from salesia.modules.inventario.infrastructure_models import SupplyLine as SupplyLine
from salesia.modules.inventario.infrastructure_models import WarehouseLocation as WarehouseLocation
from salesia.shared.infrastructure.models import AuditLogModel as AuditLogModel
from salesia.shared.infrastructure.models import BranchModel as BranchModel
from salesia.shared.infrastructure.models import InventoryStockModel as InventoryStockModel
from salesia.shared.infrastructure.models import KardexMovementModel as KardexMovementModel
from salesia.shared.infrastructure.models import ProductModel as ProductModel
from salesia.shared.infrastructure.models import WarehouseModel as WarehouseModel
