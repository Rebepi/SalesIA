from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.contracts.privacidad_bloqueo_legal import LegalHoldRequest
from salesia.modules.operaciones.infrastructure_models import LegalHold
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def manage_legal_hold(payload: LegalHoldRequest, current_user: AuthenticatedUser, db: Session):
    entity_type = payload.entity_type.lower()
    hold = db.scalar(
        select(LegalHold)
        .where(
            LegalHold.company_id == current_user.company_id,
            LegalHold.entity_type == entity_type,
            LegalHold.entity_id == payload.entity_id,
        )
        .with_for_update()
    )
    if payload.action == "place":
        if hold and hold.lifted_at is None:
            raise HTTPException(409, "La entidad ya tiene una retención legal activa.")
        if hold:
            hold.reason = payload.hold_reason
            hold.placed_by = current_user.user_id
            hold.placed_at = datetime.now(timezone.utc)
            hold.lifted_by = None
            hold.lifted_at = None
        else:
            db.add(
                LegalHold(
                    company_id=current_user.company_id,
                    entity_type=entity_type,
                    entity_id=payload.entity_id,
                    reason=payload.hold_reason,
                    placed_by=current_user.user_id,
                )
            )
        db.commit()
        return {"entity_id": str(payload.entity_id), "status": "hold_placed", "reason": payload.hold_reason}
    if payload.action == "lift":
        if current_user.role not in ("company_admin", "admin", "compliance_officer") and not getattr(
            current_user, "is_superuser", False
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permiso insuficiente para levantar retención legal. Se requiere rol de cumplimiento o administración.",
            )
        if not hold or hold.lifted_at is not None:
            raise HTTPException(404, "Retención legal activa no encontrada.")
        hold.lifted_by = current_user.user_id
        hold.lifted_at = datetime.now(timezone.utc)
        db.commit()
        return {"entity_id": str(payload.entity_id), "status": "hold_lifted"}
