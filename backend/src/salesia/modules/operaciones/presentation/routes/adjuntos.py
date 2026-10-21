from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.adjuntos as service_adjuntos
from salesia.modules.operaciones.application.contracts.adjuntos import CompleteAttachmentRequest, UploadIntentRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/attachments/upload-intents", status_code=201)
def create_upload_intent(
    payload: UploadIntentRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_adjuntos.create_upload_intent(payload=payload, current_user=current_user, db=db)


@router.put("/attachments/{attachment_id}/content")
async def upload_attachment_content(
    attachment_id: UUID,
    request: Request,
    upload_token: str = Header(..., alias="X-Upload-Token"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return await service_adjuntos.upload_attachment_content(
        attachment_id=attachment_id, request=request, upload_token=upload_token, current_user=current_user, db=db
    )


@router.post("/attachments/{attachment_id}/complete")
def complete_attachment_upload(
    attachment_id: UUID,
    payload: Optional[CompleteAttachmentRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_adjuntos.complete_attachment_upload(
        attachment_id=attachment_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_adjuntos.download_attachment(attachment_id=attachment_id, current_user=current_user, db=db)


@router.get("/attachments/{attachment_id}/preview")
def preview_attachment(
    attachment_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_adjuntos.preview_attachment(attachment_id=attachment_id, current_user=current_user, db=db)
