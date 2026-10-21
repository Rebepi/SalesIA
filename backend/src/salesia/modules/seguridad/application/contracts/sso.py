from typing import Optional

from pydantic import BaseModel


class SsoLoginRequest(BaseModel):
    id_token: str
    state: str
    nonce: Optional[str] = None
