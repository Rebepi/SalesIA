from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import entregas_parciales as service
from salesia.modules.inventario.service import document
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Resultados parciales de entrega"])


@router.get("/deliveries/{delivery_id}/results")
def delivery_results(delivery_id: UUID, user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.result_data(db, user, document(db, user, "DELIVERY", delivery_id, lock=False))


@router.post("/deliveries/{delivery_id}/results", status_code=201)
def record_delivery_result(delivery_id: UUID, payload: service.DeliveryResultRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.record_result(db, user, delivery_id, payload, key)
