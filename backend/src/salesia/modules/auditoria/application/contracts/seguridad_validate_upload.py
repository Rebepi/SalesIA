from pydantic import BaseModel, Field


class FileUploadValidationRequest(BaseModel):
    filename: str = Field(..., min_length=3)
    content_base64: str = Field(..., min_length=1)
    max_size_bytes: int = Field(default=10485760, ge=1024)
