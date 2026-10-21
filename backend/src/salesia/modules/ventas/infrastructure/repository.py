import json as json
from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import select as select
from sqlalchemy.orm import Session as Session

from salesia.modules.ventas.domain.entities import Sale as Sale
from salesia.modules.ventas.domain.entities import SaleLine as SaleLine
from salesia.modules.ventas.domain.entities import SaleStatus as SaleStatus
from salesia.modules.ventas.domain.ports import IAuditPort as IAuditPort
from salesia.modules.ventas.domain.ports import ICustomerCreditPort as ICustomerCreditPort
from salesia.modules.ventas.domain.ports import IInventoryStockPort as IInventoryStockPort
from salesia.modules.ventas.domain.ports import IOutboxPort as IOutboxPort
from salesia.modules.ventas.domain.ports import ISaleRepository as ISaleRepository
from salesia.modules.ventas.domain.ports import ISalesUnitOfWork as ISalesUnitOfWork
from salesia.modules.ventas.infrastructure.repositorios.auditoria import SqlAuditPort as SqlAuditPort
from salesia.modules.ventas.infrastructure.repositorios.credito import SqlCustomerCreditPort as SqlCustomerCreditPort
from salesia.modules.ventas.infrastructure.repositorios.eventos import SqlOutboxAdapter as SqlOutboxAdapter
from salesia.modules.ventas.infrastructure.repositorios.inventario import SqlInventoryPort as SqlInventoryPort
from salesia.modules.ventas.infrastructure.repositorios.transacciones import SqlSalesUnitOfWork as SqlSalesUnitOfWork
from salesia.modules.ventas.infrastructure.repositorios.ventas import SqlSaleRepository as SqlSaleRepository
from salesia.shared.domain.money import Money as Money
from salesia.shared.infrastructure.models import AuditLogModel as AuditLogModel
from salesia.shared.infrastructure.models import CustomerModel as CustomerModel
from salesia.shared.infrastructure.models import InventoryStockModel as InventoryStockModel
from salesia.shared.infrastructure.models import KardexMovementModel as KardexMovementModel
from salesia.shared.infrastructure.models import OutboxEventModel as OutboxEventModel
from salesia.shared.infrastructure.models import ProductModel as ProductModel
from salesia.shared.infrastructure.models import SaleLineModel as SaleLineModel
from salesia.shared.infrastructure.models import SaleModel as SaleModel
from salesia.shared.infrastructure.outbox import OutboxRecord as OutboxRecord
