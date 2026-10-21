from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    scope: str = Field(default="read_only", pattern="^(read_only|sales_write|integration)$")
