from pydantic import BaseModel, Field


class OutgoingFetchRequest(BaseModel):
    url: str = Field(..., min_length=4)
    method: str = Field(default="GET", pattern="^(GET|POST|HEAD)$")
