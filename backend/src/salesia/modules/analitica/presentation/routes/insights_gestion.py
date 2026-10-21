from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.insights_gestion as service_insights_gestion
from salesia.modules.analitica.application.contracts.insights_gestion import (
    InsightBulkActionRequest,
    InsightFeedbackRequest,
    InsightStatusUpdateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/insights")
def list_insights(
    status_filter: Optional[str] = Query(None),
    severity_filter: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_gestion.list_insights(
        status_filter=status_filter,
        severity_filter=severity_filter,
        rule_id=rule_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/insights/{insight_id}")
def get_insight_detail(
    insight_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_insights_gestion.get_insight_detail(insight_id=insight_id, current_user=current_user, db=db)


@router.get("/insights/{insight_id}/evidence")
def get_insight_evidence(
    insight_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_insights_gestion.get_insight_evidence(insight_id=insight_id, current_user=current_user, db=db)


@router.patch("/insights/{insight_id}/status")
def update_insight_status(
    insight_id: UUID,
    payload: InsightStatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_gestion.update_insight_status(
        insight_id=insight_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/insights/{insight_id}/feedback")
def add_insight_feedback(
    insight_id: UUID,
    payload: InsightFeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_gestion.add_insight_feedback(
        insight_id=insight_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/insights/{insight_id}/actions/{action_id}/prepare")
def prepare_insight_action(
    insight_id: UUID,
    action_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_gestion.prepare_insight_action(
        insight_id=insight_id, action_id=action_id, current_user=current_user, db=db
    )


@router.post("/insights/bulk-actions")
def bulk_insight_actions(
    payload: InsightBulkActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_insights_gestion.bulk_insight_actions(payload=payload, current_user=current_user, db=db)


@router.post("/insights/bulk-read")
def bulk_read_insights(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_insights_gestion.bulk_read_insights(current_user=current_user, db=db)
