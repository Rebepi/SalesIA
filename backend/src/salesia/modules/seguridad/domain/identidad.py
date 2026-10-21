from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: UUID
    email: str
    company_id: UUID
    role: str
    permissions: list[str]
    session_id: Optional[UUID] = None
    is_support_session: bool = False
    support_grant_id: Optional[UUID] = None
