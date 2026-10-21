from uuid import UUID

from pydantic import BaseModel, Field


class ReconcileRequest(BaseModel):
    warehouse_id: UUID

    product_id: UUID


class ReconcileRepairRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)

    evidence: str = Field(min_length=3, max_length=255)
