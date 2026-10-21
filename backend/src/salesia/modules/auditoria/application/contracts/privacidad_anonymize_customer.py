from uuid import UUID

from pydantic import BaseModel, Field


class AnonymizeCustomerRequest(BaseModel):
    customer_id: UUID
    reason: str = Field(default="Solicitud de derecho al olvido ARCO/GDPR")
