from typing import Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.insights_evaluacion as service_insights_evaluacion
from salesia.modules.analitica.application.contracts.insights_evaluacion import (
    InsightEvaluationRequest,
    InsightRuleSimulateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/insights/rules")
def list_insight_rules(current_user: AuthenticatedUser = Depends(get_current_user)):

    return service_insights_evaluacion.list_insight_rules(current_user=current_user)


@router.post("/insights/rules/simulate")
def post_simulate_insight_rule(
    payload: InsightRuleSimulateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_evaluacion.post_simulate_insight_rule(payload=payload, current_user=current_user, db=db)


@router.post("/insights/evaluate")
def evaluate_insights(
    payload: Optional[InsightEvaluationRequest] = Body(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_evaluacion.evaluate_insights(payload=payload, current_user=current_user, db=db)
