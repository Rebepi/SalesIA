from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application.contracts.almacenes import WarehouseCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import BranchModel, WarehouseModel


def list_warehouses(branch_id: Optional[UUID], is_active: Optional[bool], current_user: AuthenticatedUser, db: Session):
    query = select(WarehouseModel).where(WarehouseModel.company_id == current_user.company_id)
    if branch_id is not None:
        query = query.where(WarehouseModel.branch_id == branch_id)
    if is_active is not None:
        query = query.where(WarehouseModel.is_active == is_active)
    rows = db.scalars(query.order_by(WarehouseModel.code))
    return [
        {
            "warehouse_id": row.id,
            "branch_id": row.branch_id,
            "company_id": row.company_id,
            "code": row.code,
            "name": row.name,
            "is_active": row.is_active,
        }
        for row in rows
    ]


def create_warehouse(req: WarehouseCreateModel, current_user: AuthenticatedUser, db: Session):
    if not db.scalar(
        select(BranchModel.id).where(
            BranchModel.id == req.branch_id,
            BranchModel.company_id == current_user.company_id,
            BranchModel.is_active.is_(True),
        )
    ):
        raise HTTPException(422, "Sucursal inválida.")
    if db.scalar(
        select(WarehouseModel.id).where(
            WarehouseModel.company_id == current_user.company_id, WarehouseModel.code == req.code
        )
    ):
        raise HTTPException(409, "El código de almacén ya existe.")
    warehouse = WarehouseModel(company_id=current_user.company_id, **req.model_dump())
    db.add(warehouse)
    db.commit()
    return {"warehouse_id": warehouse.id, **req.model_dump(), "is_active": warehouse.is_active}
