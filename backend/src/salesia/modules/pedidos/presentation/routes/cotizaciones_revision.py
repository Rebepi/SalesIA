from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application import cotizaciones_revision as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter()


@router.get("/quotations/{quotation_id}/versions")
def list_quotation_versions(quotation_id: UUID, user: AuthenticatedUser = Depends(require_permission("quotations:read")), db: Session = Depends(get_db)):
    return service.list_versions(db, user, quotation_id)


@router.get("/quotations/{quotation_id}/compare/{other_id}")
def compare_quotation_versions(quotation_id: UUID, other_id: UUID, user: AuthenticatedUser = Depends(require_permission("quotations:read")), db: Session = Depends(get_db)):
    return service.compare_versions(db, user, quotation_id, other_id)


@router.post("/quotations/{quotation_id}/review")
def review_quotation(quotation_id: UUID, payload: service.QuotationReviewRequest, user: AuthenticatedUser = Depends(require_permission("quotations:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.review_quotation(db, user, quotation_id, payload, key)
