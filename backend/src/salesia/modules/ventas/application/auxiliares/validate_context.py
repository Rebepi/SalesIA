from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.models import BranchModel, CompanyModel, CustomerModel, WarehouseModel


def validate_context(db, payload, company_id):

    if payload.company_id and payload.company_id != company_id:
        raise HTTPException(403, "Empresa no permitida.")

    branch = db.scalar(
        select(BranchModel).where(
            BranchModel.id == payload.branch_id, BranchModel.company_id == company_id, BranchModel.is_active.is_(True)
        )
    )

    customer = db.scalar(
        select(CustomerModel).where(
            CustomerModel.id == payload.customer_id,
            CustomerModel.company_id == company_id,
            CustomerModel.is_active.is_(True),
        )
    )

    if not branch or not customer:
        raise HTTPException(422, "Seleccione sucursal y cliente activos de su empresa.")

    if payload.document_type == "INVOICE" and customer.doc_type.upper() not in ("RUC", "NIT"):
        raise HTTPException(422, "Una factura requiere un cliente identificado con documento fiscal empresarial.")

    warehouses = select(WarehouseModel).where(
        WarehouseModel.company_id == company_id,
        WarehouseModel.branch_id == branch.id,
        WarehouseModel.is_active.is_(True),
    )

    if payload.warehouse_id:
        warehouses = warehouses.where(WarehouseModel.id == payload.warehouse_id)

    rows = db.scalars(warehouses).all()

    if len(rows) != 1:
        raise HTTPException(422, "Seleccione un almacén activo de la sucursal.")

    company = db.get(CompanyModel, company_id)

    if payload.currency.upper() != company.base_currency:
        raise HTTPException(422, "La venta debe usar la moneda base hasta configurar listas de precios por moneda.")

    return rows[0]
