from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.models import BranchModel, CustomerModel, WarehouseModel


def validate_references(db, company_id, customer_id, branch_id=None, warehouse_id=None):

    if (
        db.scalar(
            select(CustomerModel.id).where(CustomerModel.id == customer_id, CustomerModel.company_id == company_id)
        )
        is None
    ):
        raise HTTPException(422, "El cliente no existe en esta empresa.")

    if (
        branch_id
        and db.scalar(select(BranchModel.id).where(BranchModel.id == branch_id, BranchModel.company_id == company_id, BranchModel.is_active.is_(True)))
        is None
    ):
        raise HTTPException(422, "La sucursal no existe en esta empresa.")

    if (
        warehouse_id
        and db.scalar(
            select(WarehouseModel.id).where(
                WarehouseModel.id == warehouse_id,
                WarehouseModel.company_id == company_id,
                WarehouseModel.branch_id == branch_id,
                WarehouseModel.is_active.is_(True),
            )
        )
        is None
    ):
        raise HTTPException(422, "El almacén no pertenece a la sucursal indicada.")
