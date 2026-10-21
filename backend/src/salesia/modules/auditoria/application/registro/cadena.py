import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from salesia.shared.infrastructure.models import AuditLogModel


def compute_chain_hash(
    previous_hash: str,
    chain_sequence: int,
    log_id: UUID,
    company_id: UUID,
    actor_id: Optional[UUID],
    action: str,
    entity_type: str,
    entity_id: UUID,
    payload_diff: Optional[str],
    created_at: datetime,
) -> str:
    dt = (
        created_at.astimezone(timezone.utc)
        if getattr(created_at, "tzinfo", None) is not None
        else created_at.replace(tzinfo=timezone.utc)
    )
    content = json.dumps(
        {
            "previous": previous_hash,
            "sequence": chain_sequence,
            "id": str(log_id),
            "company_id": str(company_id),
            "actor": str(actor_id) if actor_id else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "payload": payload_diff,
            "created_at": dt.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@event.listens_for(AuditLogModel, "before_insert")
def seal_audit_entry(mapper, connection, target) -> None:
    if target.entry_hash:
        return
    if connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:company))"), {"company": str(target.company_id)}
        )
    previous = connection.execute(
        select(AuditLogModel.entry_hash)
        .where(AuditLogModel.company_id == target.company_id, AuditLogModel.entry_hash.is_not(None))
        .order_by(AuditLogModel.chain_sequence.desc())
        .limit(1)
    ).scalar() or ("0" * 64)
    chain_sequence = connection.execute(
        select(func.coalesce(func.max(AuditLogModel.chain_sequence), 0) + 1).where(
            AuditLogModel.company_id == target.company_id
        )
    ).scalar_one()
    target.id = target.id or uuid4()
    target.created_at = target.created_at or datetime.now(timezone.utc)
    target.trace_id = target.trace_id or uuid4().hex
    target.previous_hash = previous
    target.chain_sequence = target.chain_sequence or chain_sequence
    target.entry_hash = compute_chain_hash(
        previous,
        target.chain_sequence,
        target.id,
        target.company_id,
        target.actor_id,
        target.action,
        target.entity_type,
        target.entity_id,
        target.payload_diff,
        target.created_at,
    )


def verify_audit_chain(db: Session, company_id: UUID) -> dict:
    rows = db.scalars(
        select(AuditLogModel).where(AuditLogModel.company_id == company_id).order_by(AuditLogModel.chain_sequence.asc())
    ).all()

    if not rows:
        return {"is_valid": True, "verified_count": 0, "broken_at_id": None}

    expected_prev = "0" * 64
    verified_count = 0
    legacy_unsealed_count = 0
    for row in rows:
        if not row.entry_hash:
            legacy_unsealed_count += 1
            continue
        expected_sequence = verified_count + legacy_unsealed_count + 1
        if row.chain_sequence != expected_sequence:
            return {
                "is_valid": False,
                "verified_count": verified_count,
                "legacy_unsealed_count": legacy_unsealed_count,
                "broken_at_id": str(row.id),
                "reason": "Secuencia de cadena no consecutiva",
            }
        if row.previous_hash != expected_prev:
            return {
                "is_valid": False,
                "verified_count": verified_count,
                "legacy_unsealed_count": legacy_unsealed_count,
                "broken_at_id": str(row.id),
                "reason": "Hash anterior no coincide",
            }

        computed = compute_chain_hash(
            row.previous_hash or expected_prev,
            row.chain_sequence,
            row.id,
            row.company_id,
            row.actor_id,
            row.action,
            row.entity_type,
            row.entity_id,
            row.payload_diff,
            row.created_at,
        )
        if computed != row.entry_hash:
            return {
                "is_valid": False,
                "verified_count": verified_count,
                "legacy_unsealed_count": legacy_unsealed_count,
                "broken_at_id": str(row.id),
                "reason": "Hash alterado",
            }
        expected_prev = row.entry_hash
        verified_count += 1

    return {
        "is_valid": True,
        "verified_count": verified_count,
        "legacy_unsealed_count": legacy_unsealed_count,
        "broken_at_id": None,
    }


def reseal_audit_chains(db: Session, company_id: Optional[UUID] = None) -> dict:
    """Rebuild legacy/corrupt chains during an explicit maintenance operation."""
    bind = db.get_bind()
    postgres = bind.dialect.name == "postgresql"
    if postgres:
        db.execute(text("ALTER TABLE audit_logs DISABLE TRIGGER audit_logs_append_only"))
    try:
        query = select(AuditLogModel)
        if company_id:
            query = query.where(AuditLogModel.company_id == company_id)
        rows = db.scalars(
            query.order_by(
                AuditLogModel.company_id.asc(),
                AuditLogModel.chain_sequence.asc().nulls_last(),
                AuditLogModel.created_at.asc(),
                AuditLogModel.id.asc(),
            )
        ).all()
        previous_by_company: dict[UUID, str] = {}
        sequence_by_company: dict[UUID, int] = {}
        for row in rows:
            previous = previous_by_company.get(row.company_id, "0" * 64)
            sequence = sequence_by_company.get(row.company_id, 0) + 1
            entry_hash = compute_chain_hash(
                previous,
                sequence,
                row.id,
                row.company_id,
                row.actor_id,
                row.action,
                row.entity_type,
                row.entity_id,
                row.payload_diff,
                row.created_at,
            )
            db.execute(
                text(
                    "UPDATE audit_logs SET previous_hash=:previous, entry_hash=:entry_hash, "
                    "chain_sequence=:sequence WHERE id=:log_id"
                ),
                {"previous": previous, "entry_hash": entry_hash, "sequence": sequence, "log_id": row.id},
            )
            previous_by_company[row.company_id] = entry_hash
            sequence_by_company[row.company_id] = sequence
        db.flush()
        return {"repaired_entries": len(rows), "companies": len(sequence_by_company)}
    finally:
        if postgres:
            db.execute(text("ALTER TABLE audit_logs ENABLE TRIGGER audit_logs_append_only"))
