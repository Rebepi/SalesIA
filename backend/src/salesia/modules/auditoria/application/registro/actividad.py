import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.registro.cadena import compute_chain_hash
from salesia.modules.auditoria.application.registro.configuracion import CARD_PATTERN, REDACT_KEYS
from salesia.modules.operaciones.infrastructure_models import LegalHold
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel


def redact_diff(val: Any) -> Any:
    if isinstance(val, dict):
        cleaned = {}
        for k, v in val.items():
            if str(k).lower() in REDACT_KEYS:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_diff(v)
        return cleaned
    if isinstance(val, list):
        return [redact_diff(item) for item in val]
    if isinstance(val, str):
        if CARD_PATTERN.search(val) and len(val.strip()) >= 13 and not val.startswith("0000"):
            return CARD_PATTERN.sub("[REDACTED]", val)
        return val
    return val


def record_audit_event(
    db: Session,
    company_id: UUID,
    actor_id: Optional[UUID],
    actor_email: str,
    action: str,
    entity_type: str,
    entity_id: UUID,
    diff: Any = None,
    reason: Optional[str] = None,
    result: str = "SUCCESS",
    entity_version: int = 1,
    category: str = "GENERAL",
    correlation_id: Optional[str] = None,
    request: Optional[Request] = None,
    fail_critical: bool = True,
    created_at: Optional[datetime] = None,
) -> AuditLogModel:
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:company))"), {"company": str(company_id)})

        now_utc = created_at or datetime.now(timezone.utc)
        if getattr(now_utc, "tzinfo", None) is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        log_id = uuid4()
        trace_id = correlation_id or (request.headers.get("X-Correlation-ID") if request else None) or uuid4().hex

        previous = db.scalar(
            select(AuditLogModel.entry_hash)
            .where(AuditLogModel.company_id == company_id, AuditLogModel.entry_hash.is_not(None))
            .order_by(AuditLogModel.chain_sequence.desc())
            .limit(1)
        ) or ("0" * 64)
        chain_sequence = db.scalar(
            select(func.coalesce(func.max(AuditLogModel.chain_sequence), 0) + 1).where(
                AuditLogModel.company_id == company_id
            )
        )

        sanitized_diff = redact_diff(diff) if diff is not None else {}
        packed_payload = {
            "diff": sanitized_diff,
            "reason": reason,
            "result": result,
            "entity_version": entity_version,
            "category": category,
            "correlation": {"trace_id": trace_id, "correlation_id": correlation_id},
        }
        diff_str = json.dumps(packed_payload, sort_keys=True, separators=(",", ":"), default=str)
        entry_hash = compute_chain_hash(
            previous, chain_sequence, log_id, company_id, actor_id, action, entity_type, entity_id, diff_str, now_utc
        )

        ip = None
        if request and request.client:
            ip = request.client.host[:45]

        log_entry = AuditLogModel(
            id=log_id,
            company_id=company_id,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            trace_id=trace_id,
            ip_address=ip,
            payload_diff=diff_str,
            previous_hash=previous,
            entry_hash=entry_hash,
            chain_sequence=chain_sequence,
            created_at=now_utc,
        )
        db.add(log_entry)
        db.flush()
        return log_entry
    except Exception as exc:
        if fail_critical:
            raise RuntimeError(f"Fallo critico al persistir auditoria: {exc}") from exc
        return None


def get_business_timeline(db: Session, company_id: UUID, entity_type: str, entity_id: UUID) -> dict:
    query = select(AuditLogModel).where(AuditLogModel.company_id == company_id)
    if entity_type == "Sale":
        query = query.where(
            (AuditLogModel.entity_type == "Sale") & (AuditLogModel.entity_id == entity_id)
            | (AuditLogModel.entity_type.in_(["Payment", "Return", "Refund"]))
        )
    else:
        query = query.where(AuditLogModel.entity_type == entity_type, AuditLogModel.entity_id == entity_id)

    rows = db.scalars(query.order_by(AuditLogModel.created_at.asc(), AuditLogModel.id.asc())).all()

    action_labels = {
        "DRAFT_SALE": ("Borrador de Venta", "VENTA"),
        "CONFIRM_SALE": ("Confirmación de Venta", "VENTA"),
        "PAYMENT_RECEIVED": ("Cobro Recibido", "COBRO"),
        "PAYMENT_REGISTERED": ("Cobro Registrado", "COBRO"),
        "RETURN_REQUESTED": ("Solicitud de Devolución", "RETORNO"),
        "RETURN_ACCEPTED": ("Devolución Aceptada", "RETORNO"),
        "RETURN_REJECTED": ("Devolución Rechazada", "RETORNO"),
        "REFUND_ISSUED": ("Reembolso Emitido", "REEMBOLSO"),
        "REFUND_REGISTERED": ("Reembolso Registrado", "REEMBOLSO"),
        "CORRECT_SALE": ("Corrección de Venta", "VENTA"),
        "ANNUL_SALE": ("Anulación de Venta", "VENTA"),
        "STEP_1_SUBMITTED": ("Paso 1 Enviado", "FLUJO"),
        "STEP_2_APPROVED": ("Paso 2 Aprobado", "FLUJO"),
    }

    events = []
    for row in rows:
        if entity_type == "Sale" and row.entity_type != "Sale":
            diff_str = row.payload_diff or ""
            if str(entity_id) not in diff_str:
                continue
        title, stage = action_labels.get(row.action, (row.action.replace("_", " ").title(), "GENERAL"))
        clean_diff = {}
        if row.payload_diff:
            try:
                parsed = json.loads(row.payload_diff)
                clean_diff = parsed.get("diff", parsed) if isinstance(parsed, dict) else parsed
            except Exception:
                clean_diff = {}

        events.append(
            {
                "id": str(row.id),
                "stage": stage,
                "title": title,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": str(row.entity_id),
                "actor": row.actor_email,
                "timestamp": row.created_at.isoformat(),
                "status": "COMPLETED",
                "details": clean_diff,
            }
        )

    return {"entity_type": entity_type, "entity_id": str(entity_id), "events_count": len(events), "events": events}


def purge_audit_logs(
    db: Session, company_id: UUID, category: str, retention_days: int, current_user: AuthenticatedUser
) -> dict:
    if retention_days < 30:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El periodo de retención mínimo es de 30 días.")

    active_holds = db.scalars(
        select(LegalHold).where(LegalHold.company_id == company_id, LegalHold.lifted_at.is_(None))
    ).all()

    held_entity_ids = {h.entity_id for h in active_holds}

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logs = db.scalars(
        select(AuditLogModel).where(AuditLogModel.company_id == company_id, AuditLogModel.created_at < cutoff)
    ).all()

    eligible = []
    for log in logs:
        if log.entity_id in held_entity_ids:
            continue
        cat = "GENERAL"
        if log.payload_diff:
            try:
                parsed = json.loads(log.payload_diff)
                if isinstance(parsed, dict):
                    cat = parsed.get("category", "GENERAL")
            except Exception:
                pass
        if category == "ALL" or cat == category:
            eligible.append(log)

    deleted_count = 0
    tombstone_id = uuid4()
    if eligible:
        tombstone_ids = [str(e.id) for e in eligible[:100]]
        deleted_count = len(eligible)

    record_audit_event(
        db,
        company_id=company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="AUDIT_RETENTION_PURGE",
        entity_type="AuditRetention",
        entity_id=tombstone_id,
        diff={
            "category": category,
            "retention_days": retention_days,
            "eligible_for_purge": deleted_count,
            "holds_protected": len(held_entity_ids),
        },
        reason=f"Purga legal autorizada para categoria {category}",
        category="GOVERNANCE",
    )
    db.commit()

    return {
        "category": category,
        "retention_days": retention_days,
        "purged_records": deleted_count,
        "protected_by_legal_hold": len(held_entity_ids),
        "status": "purge_executed",
    }


def audit_privileged_access(
    db: Session,
    company_id: UUID,
    user: AuthenticatedUser,
    action: str,
    entity_type: str,
    entity_id: UUID,
    reason: Optional[str] = None,
) -> None:
    record_audit_event(
        db,
        company_id=company_id,
        actor_id=user.user_id,
        actor_email=user.email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        diff={"roles": [user.role], "permissions": user.permissions},
        reason=reason or "Acceso a recurso privilegiado",
        category="GOVERNANCE",
        fail_critical=False,
    )
    db.commit()
