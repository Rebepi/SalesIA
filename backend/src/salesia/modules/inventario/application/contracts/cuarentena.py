from typing import Literal, Optional

from pydantic import BaseModel, Field


class QuarantineClassifyRequest(BaseModel):
    action: Literal["RESTOCK", "SCRAP"]

    notes: Optional[str] = Field(default=None, max_length=255)
