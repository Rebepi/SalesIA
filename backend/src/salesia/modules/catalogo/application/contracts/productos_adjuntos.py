from pydantic import BaseModel, Field


class AttachmentCreateModel(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)

    file_url: str = Field(..., min_length=4, max_length=512)

    content_type: str = Field(..., min_length=3, max_length=64)

    file_size_bytes: int = Field(..., gt=0, le=5242880)

    is_primary: bool = False

    is_private: bool = False
