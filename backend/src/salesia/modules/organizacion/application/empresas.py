from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application.auxiliares.company_dict import company_dict
from salesia.modules.organizacion.application.contracts.empresas import CompanyUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, SaleModel


def get_current_company(current_user: AuthenticatedUser, db: Session):
    company = db.get(CompanyModel, current_user.company_id)
    if not company:
        raise HTTPException(404, "Empresa no encontrada.")
    return company_dict(company)


def update_current_company(req: CompanyUpdateModel, current_user: AuthenticatedUser, db: Session):
    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    if not company:
        raise HTTPException(404, "Empresa no encontrada.")
    if req.base_currency and req.base_currency != company.base_currency:
        count = db.scalar(select(func.count()).select_from(SaleModel).where(SaleModel.company_id == company.id))
        if count:
            raise HTTPException(409, "No se puede cambiar la moneda base después de registrar ventas.")
    for name, value in req.model_dump(exclude_none=True).items():
        setattr(company, name, value)
    db.commit()
    return company_dict(company)
