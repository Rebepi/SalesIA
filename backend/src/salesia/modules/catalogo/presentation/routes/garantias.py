from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.garantias as service_garantias
from salesia.modules.catalogo.application.contracts.garantias import WarrantyClaimCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/warranty/claims", status_code=status.HTTP_201_CREATED)
def create_warranty_claim(
    req: WarrantyClaimCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_garantias.create_warranty_claim(req=req, current_user=current_user, db=db, idempotency_key=idempotency_key)


@router.get("/products/{product_id}/eligible-warranty-sales")
def eligible_warranty_sales(
    product_id: UUID,
    search: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_garantias.eligible_warranty_sales(
        product_id=product_id, search=search, current_user=current_user, db=db
    )
