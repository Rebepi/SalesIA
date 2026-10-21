from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application import cuotas_cobranza as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Cronogramas de cuentas por cobrar"])


@router.get("/receivables/{sale_id}/installment-schedule")
def receivable_installment_schedule(sale_id: UUID, user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    sale = service.scoped_sale(db, user, sale_id)
    return service.schedule_data(db, user, sale)


@router.post("/receivables/{sale_id}/installment-schedule")
def save_receivable_schedule(sale_id: UUID, payload: service.ScheduleRequest, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_schedule(db, user, sale_id, payload, key)
