from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.privacidad_anonymize_customer as service_privacidad_anonymize_customer
from salesia.modules.auditoria.application.contracts.privacidad_anonymize_customer import AnonymizeCustomerRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/privacy/anonymize-customer")
def anonymize_customer(
    payload: AnonymizeCustomerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_privacidad_anonymize_customer.anonymize_customer(payload=payload, current_user=current_user, db=db)
