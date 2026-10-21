import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.models import AuditLogModel, BranchModel, ProductModel, WarehouseModel


def make_aware(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def warehouse(db, company_id, warehouse_id, lock=False):
    query = select(WarehouseModel).where(
        WarehouseModel.id == warehouse_id, WarehouseModel.company_id == company_id, WarehouseModel.is_active.is_(True)
    )
    row = db.scalar(query.with_for_update() if lock else query)
    if not row or not db.scalar(
        select(BranchModel.id).where(
            BranchModel.id == row.branch_id, BranchModel.company_id == company_id, BranchModel.is_active.is_(True)
        )
    ):
        raise HTTPException(422, "Almacén o sucursal inexistente, inactivo o de otra empresa.")
    return row


def product(db, company_id, product_id):
    row = db.scalar(
        select(ProductModel).where(
            ProductModel.id == product_id, ProductModel.company_id == company_id, ProductModel.is_active.is_(True)
        )
    )
    if not row:
        raise HTTPException(422, "Producto inexistente, inactivo o de otra empresa.")
    return row


def record_audit(db, user, entity_id, action, details):
    db.add(
        AuditLogModel(
            company_id=user.company_id,
            actor_id=user.user_id,
            actor_email=user.email,
            action=action,
            entity_type="SupplyDocument",
            entity_id=entity_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps(details, default=str),
            created_at=datetime.now(timezone.utc),
        )
    )
