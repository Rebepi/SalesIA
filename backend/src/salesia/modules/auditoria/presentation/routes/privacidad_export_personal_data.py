from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.privacidad_export_personal_data as service_privacidad_export_personal_data
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/privacy/export-personal-data")
def export_customer_personal_data(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_privacidad_export_personal_data.export_customer_personal_data(
        customer_id=customer_id, current_user=current_user, db=db
    )
