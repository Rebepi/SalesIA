import hashlib
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.auxiliares.private_root import private_root
from salesia.modules.operaciones.application.contracts.operacion_restauracion import RestoreVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import BackupSnapshotModel


def verify_restore_readiness(payload: RestoreVerifyRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(BackupSnapshotModel).where(
            BackupSnapshotModel.company_id == current_user.company_id,
            BackupSnapshotModel.snapshot_id == payload.snapshot_id,
            BackupSnapshotModel.status == "completed",
        )
    )

    if not row or not settings.backup_encryption_key:
        raise HTTPException(404, "Snapshot verificable no encontrado.")

    path = Path(row.artifact_path).resolve()

    if private_root() not in path.parents or not path.is_file():
        raise HTTPException(409, "El artefacto de respaldo no está disponible.")

    encrypted = path.read_bytes()

    actual = hashlib.sha256(encrypted).hexdigest()

    if actual != payload.checksum or actual != row.checksum:
        raise HTTPException(409, "El checksum no coincide.")

    try:
        key = hashlib.sha256(settings.backup_encryption_key.encode()).digest()

        clear = AESGCM(key).decrypt(bytes.fromhex(row.nonce), encrypted, row.snapshot_id.encode())

    except Exception:
        raise HTTPException(409, "No se pudo autenticar o descifrar el respaldo.")

    if not clear.startswith((b"PGDMP", b"SQLite format 3")):
        raise HTTPException(409, "El formato descifrado no es un respaldo compatible.")

    return {
        "snapshot_id": row.snapshot_id,
        "integrity_check": "passed",
        "encrypted": True,
        "source_revision": row.source_revision,
        "size_bytes": len(clear),
        "verified_at": now().isoformat(),
    }
