from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application.auxiliares.branch_dict import branch_dict
from salesia.modules.organizacion.application.contracts.sedes import BranchCreateModel, BranchUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import (
    BranchModel,
    CompanyModel,
)


def list_branches(is_active: Optional[bool], current_user: AuthenticatedUser, db: Session):
    query = select(BranchModel).where(BranchModel.company_id == current_user.company_id)
    if is_active is not None:
        query = query.where(BranchModel.is_active == is_active)
    return [branch_dict(row) for row in db.scalars(query.order_by(BranchModel.code))]


def create_branch(req: BranchCreateModel, current_user: AuthenticatedUser, db: Session):
    if db.scalar(
        select(BranchModel.id).where(BranchModel.company_id == current_user.company_id, BranchModel.code == req.code)
    ):
        raise HTTPException(409, "El código de sucursal ya existe.")
    branch = BranchModel(company_id=current_user.company_id, **req.model_dump())
    db.add(branch)
    db.commit()
    return branch_dict(branch)


def update_branch(branch_id: UUID, req: BranchUpdateModel, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    branch = db.scalar(
        select(BranchModel)
        .where(BranchModel.company_id == current_user.company_id, BranchModel.id == branch_id)
        .with_for_update()
    )
    if not branch:
        raise HTTPException(404, "Sucursal no encontrada.")
    if req.timezone:
        BranchCreateModel.valid_timezone(req.timezone)
    if req.is_active is False and branch.is_active:
        from salesia.modules.organizacion.application.cierre_ubicaciones import apply_retirement
        if not req.reason or len(req.reason.strip()) < 5:
            raise HTTPException(422, "Indique el motivo del retiro desde la revisión asistida de la sede.")
        apply_retirement(db, current_user, "branch", branch, req.reason)
    for name, value in req.model_dump(exclude_none=True).items():
        if name != "reason":
            setattr(branch, name, value)
    db.commit()
    return branch_dict(branch)
