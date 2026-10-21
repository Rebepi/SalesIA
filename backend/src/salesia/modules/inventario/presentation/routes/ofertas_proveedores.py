from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import ofertas_proveedores as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Ofertas y selección de proveedores"])


@router.get("/purchase-requisitions/{requisition_id}/supplier-offers")
def compare_supplier_offers(requisition_id: UUID, user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return service.compare_offers(db, user, requisition_id)


@router.post("/purchase-requisitions/{requisition_id}/supplier-offers", status_code=201)
def create_supplier_offer(requisition_id: UUID, payload: service.SupplierOfferRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_offer(db, user, requisition_id, payload, key)


@router.post("/supplier-offers/{offer_id}/select", status_code=201)
def select_supplier_offer(offer_id: UUID, payload: service.SelectSupplierOfferRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.select_offer(db, user, offer_id, payload, key)
