from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application import garantias
from salesia.modules.catalogo.application.contracts.garantias import WarrantyActionRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.models import UserModel

router = APIRouter()


@router.get("/warranty-cases")
def list_warranty_claims(status: Optional[str] = None, product_id: Optional[UUID] = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("sales:read")), db: Session = Depends(get_db)):
    return garantias.list_claims(db, user, status, product_id, limit, offset)


@router.get("/warranty-case-options")
def warranty_case_options(user: AuthenticatedUser = Depends(require_permission("sales:read")), db: Session = Depends(get_db)):
    return [{"id": str(row.id), "name": row.email} for row in db.scalars(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.is_active.is_(True)).order_by(UserModel.email)).all()]


@router.post("/warranty-cases/{claim_id}/actions")
def update_warranty_claim(claim_id: UUID, payload: WarrantyActionRequest, user: AuthenticatedUser = Depends(require_permission("sales:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return garantias.update_claim(db, user, claim_id, payload, key)
