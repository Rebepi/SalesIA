from pydantic import BaseModel, Field


class UrlValidationRequest(BaseModel):
    url: str = Field(..., min_length=4)
