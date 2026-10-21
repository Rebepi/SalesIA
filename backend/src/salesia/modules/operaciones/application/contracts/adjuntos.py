from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UploadIntentRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255, pattern=r"^[^/\\]+$")

    mime_type: str = Field(pattern=r"^(text/csv|application/pdf|image/png|image/jpeg|image/svg\+xml|application/zip)$")

    file_size_bytes: int = Field(gt=0)

    related_entity_type: str = Field(pattern="^(customer|product|sale|import|purchase_order)$")

    related_entity_id: Optional[UUID] = None


class CompleteAttachmentRequest(BaseModel):
    sha256_checksum: Optional[str] = None

    metadata: Optional[dict] = None
