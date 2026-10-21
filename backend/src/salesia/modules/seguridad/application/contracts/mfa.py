from typing import Optional

from pydantic import BaseModel, Field


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=1, max_length=128)


class SudoVerifyRequest(BaseModel):
    password: str = Field(min_length=1, max_length=1024)
    mfa_code: Optional[str] = None
