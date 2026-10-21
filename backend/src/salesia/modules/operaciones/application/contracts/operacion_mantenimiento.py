from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OperationalModeRequest(BaseModel):
    active: bool

    reason: Optional[str] = Field(default=None, max_length=500)

    estimated_end: Optional[datetime] = None
