from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.reglas as service_reglas
from salesia.modules.inventario.application.contracts.reglas import StockRuleRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/rules", status_code=201)
def configure_stock_rule(
    payload: StockRuleRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_reglas.configure_stock_rule(payload=payload, current_user=current_user, db=db)


@router.get("/inventory/rules")
def list_stock_rules(
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")), db: Session = Depends(get_db)
):

    return service_reglas.list_stock_rules(current_user=current_user, db=db)


@router.post("/inventory/rules/{rule_id}/deactivate")
def deactivate_stock_rule(
    rule_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_reglas.deactivate_stock_rule(rule_id=rule_id, current_user=current_user, db=db)
