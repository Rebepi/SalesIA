from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CustomerMergeModel(BaseModel):
    primary_customer_id: UUID
    duplicate_customer_id: UUID
    version: Optional[int] = None


class DuplicateCheckRequest(BaseModel):
    doc_type: str
    doc_number: str
    email: Optional[str] = None
    phone: Optional[str] = None
    legal_name: Optional[str] = None


class FiscalValidationRequest(BaseModel):
    doc_type: str
    doc_number: str
