from typing import Optional

from pydantic import BaseModel, Field


class QuotationSendRequest(BaseModel):
    channel: str = Field(pattern="^(EMAIL|WHATSAPP)$")

    recipient: Optional[str] = None

    message: Optional[str] = None
