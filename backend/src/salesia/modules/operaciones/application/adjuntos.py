import hashlib
import io
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from salesia.modules.operaciones.application.auxiliares.aware import aware
from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.auxiliares.private_root import private_root
from salesia.modules.operaciones.application.auxiliares.purchase_attachment_access import purchase_attachment_access
from salesia.modules.operaciones.application.auxiliares.related_exists import related_exists
from salesia.modules.operaciones.application.auxiliares.safe_path import safe_path
from salesia.modules.operaciones.application.auxiliares.sanitize_html import sanitize_html
from salesia.modules.operaciones.application.auxiliares.scan_uploaded_file import scan_uploaded_file
from salesia.modules.operaciones.application.contracts.adjuntos import CompleteAttachmentRequest, UploadIntentRequest
from salesia.modules.operaciones.infrastructure_models import UploadGrant
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import AttachmentModel


def create_upload_intent(payload: UploadIntentRequest, current_user: AuthenticatedUser, db: Session):
    if payload.file_size_bytes > settings.attachment_max_bytes:
        raise HTTPException(413, "El archivo supera el límite permitido.")

    if not related_exists(db, current_user, payload.related_entity_type, payload.related_entity_id):
        raise HTTPException(422, "La entidad relacionada no existe en esta empresa.")

    attachment = AttachmentModel(
        company_id=current_user.company_id,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        size_bytes=0,
        uploaded=False,
        verified=False,
        related_entity_type=payload.related_entity_type,
        related_entity_id=payload.related_entity_id,
        scan_status="pending",
        classification="internal",
        owner_id=current_user.user_id,
    )

    db.add(attachment)

    db.flush()

    token = secrets.token_urlsafe(32)

    path = safe_path("attachments", f"{attachment.id}.bin")

    db.add(
        UploadGrant(
            attachment_id=attachment.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expected_size=payload.file_size_bytes,
            storage_path=str(path),
            expires_at=now() + timedelta(hours=1),
        )
    )

    db.commit()

    return {
        "attachment_id": str(attachment.id),
        "upload_url": f"/api/v1/attachments/{attachment.id}/content",
        "upload_token": token,
        "expires_at": (now() + timedelta(hours=1)).isoformat(),
    }


async def upload_attachment_content(
    attachment_id: UUID, request: Request, upload_token: str, current_user: AuthenticatedUser, db: Session
):
    content = await request.body()
    return await run_in_threadpool(store_attachment_content, attachment_id, content, upload_token, current_user, db)


def store_attachment_content(attachment_id: UUID, content: bytes, upload_token: str, current_user: AuthenticatedUser, db: Session):
    attachment = db.scalar(
        select(AttachmentModel)
        .where(AttachmentModel.id == attachment_id, AttachmentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    purchase_attachment_access(attachment, current_user, write=True)

    grant = db.get(UploadGrant, attachment_id)

    if not attachment or not grant:
        other = db.scalar(select(AttachmentModel.id).where(AttachmentModel.id == attachment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Intención de carga no encontrada.")

    if (
        grant.consumed_at
        or aware(grant.expires_at) <= now()
        or not secrets.compare_digest(grant.token_hash, hashlib.sha256(upload_token.encode()).hexdigest())
    ):
        raise HTTPException(401, "La autorización de carga es inválida, usada o expirada.")

    if len(content) != grant.expected_size or len(content) > settings.attachment_max_bytes:
        raise HTTPException(422, "El tamaño recibido no coincide con el declarado.")

    path = Path(grant.storage_path)

    temporary = path.with_suffix(".tmp")

    temporary.write_bytes(content)

    os.replace(temporary, path)

    attachment.size_bytes = len(content)

    attachment.sha256_checksum = hashlib.sha256(content).hexdigest()

    attachment.uploaded = True

    grant.consumed_at = now()

    db.commit()

    return {
        "attachment_id": str(attachment.id),
        "size_bytes": attachment.size_bytes,
        "sha256_checksum": attachment.sha256_checksum,
        "status": "uploaded",
    }


def complete_attachment_upload(
    attachment_id: UUID, payload: Optional[CompleteAttachmentRequest], current_user: AuthenticatedUser, db: Session
):
    attachment = db.scalar(
        select(AttachmentModel)
        .where(AttachmentModel.id == attachment_id, AttachmentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    purchase_attachment_access(attachment, current_user, write=True)

    grant = db.get(UploadGrant, attachment_id)

    if not attachment or not grant:
        other = db.scalar(select(AttachmentModel.id).where(AttachmentModel.id == attachment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Adjunto no encontrado.")

    path = Path(grant.storage_path)

    if not attachment.uploaded or not grant.consumed_at or not path.is_file():
        raise HTTPException(409, "El contenido todavía no fue cargado.")

    actual = hashlib.sha256(path.read_bytes()).hexdigest()

    if actual != attachment.sha256_checksum or path.stat().st_size != attachment.size_bytes:
        raise HTTPException(409, "La integridad del adjunto no coincide.")

    if payload and payload.sha256_checksum and payload.sha256_checksum != actual:
        raise HTTPException(409, "El hash proporcionado no coincide con el archivo.")

    try:
        scan_uploaded_file(path, attachment.mime_type, attachment.file_name)

    except HTTPException as err:
        attachment.scan_status = "quarantined"

        attachment.verified = False

        db.commit()

        raise err

    attachment.scan_status = "clean"

    attachment.verified = True

    db.commit()

    return {
        "attachment_id": str(attachment.id),
        "status": "verified",
        "scan_status": "clean",
        "size_bytes": attachment.size_bytes,
        "sha256_checksum": actual,
    }


def download_attachment(attachment_id: UUID, current_user: AuthenticatedUser, db: Session):
    attachment = db.scalar(
        select(AttachmentModel).where(
            AttachmentModel.id == attachment_id,
            AttachmentModel.company_id == current_user.company_id,
            AttachmentModel.verified.is_(True),
        )
    )

    purchase_attachment_access(attachment, current_user, write=False)

    grant = db.get(UploadGrant, attachment_id)

    if not attachment or not grant:
        other = db.scalar(select(AttachmentModel.id).where(AttachmentModel.id == attachment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Adjunto verificado no encontrado.")

    if grant.expires_at and attachment.related_entity_type != "purchase_order":
        now_dt = datetime.now(timezone.utc)

        exp_dt = grant.expires_at if grant.expires_at.tzinfo else grant.expires_at.replace(tzinfo=timezone.utc)

        if exp_dt < now_dt:
            raise HTTPException(410, "El enlace de acceso al archivo ha expirado.")

    if attachment.scan_status == "quarantined":
        raise HTTPException(403, "El archivo está en cuarentena y no puede descargarse.")

    path = Path(grant.storage_path).resolve()

    if private_root() not in path.parents or not path.is_file():
        raise HTTPException(404, "El contenido del adjunto no está disponible.")

    return FileResponse(
        path,
        media_type=attachment.mime_type,
        filename=attachment.file_name,
        headers={"X-Content-Type-Options": "nosniff"},
    )


def preview_attachment(attachment_id: UUID, current_user: AuthenticatedUser, db: Session):
    attachment = db.scalar(
        select(AttachmentModel).where(
            AttachmentModel.id == attachment_id,
            AttachmentModel.company_id == current_user.company_id,
            AttachmentModel.verified.is_(True),
        )
    )

    purchase_attachment_access(attachment, current_user, write=False)

    grant = db.get(UploadGrant, attachment_id)

    if not attachment or not grant:
        other = db.scalar(select(AttachmentModel.id).where(AttachmentModel.id == attachment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Adjunto verificado no encontrado.")

    if grant.expires_at and attachment.related_entity_type != "purchase_order":
        now_dt = datetime.now(timezone.utc)

        exp_dt = grant.expires_at if grant.expires_at.tzinfo else grant.expires_at.replace(tzinfo=timezone.utc)

        if exp_dt < now_dt:
            raise HTTPException(410, "El enlace de acceso al archivo ha expirado.")

    if attachment.scan_status == "quarantined":
        raise HTTPException(403, "El archivo está en cuarentena y no puede previsualizarse.")

    path = Path(grant.storage_path).resolve()

    if private_root() not in path.parents or not path.is_file():
        raise HTTPException(404, "El contenido no está disponible.")

    raw = path.read_bytes()

    headers = {"Content-Security-Policy": "default-src 'none'; sandbox", "X-Content-Type-Options": "nosniff"}

    if attachment.mime_type in ("image/svg+xml", "text/html"):
        sanitized = sanitize_html(raw.decode("utf-8", errors="ignore"))

        return StreamingResponse(
            io.BytesIO(sanitized.encode("utf-8")), media_type=attachment.mime_type, headers=headers
        )

    return FileResponse(path, media_type=attachment.mime_type, headers=headers)
