from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerOpportunityCreateModel(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    stage: str = Field(default="lead", pattern="^(lead|qualified|proposal|negotiation|won|lost)$")
    estimated_amount: Decimal = Field(default=Decimal("0.000000"), ge=0)
    probability: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    assigned_to_id: Optional[UUID] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class CustomerOpportunityUpdateModel(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = Field(default=None, pattern="^(lead|qualified|proposal|negotiation|won|lost)$")
    estimated_amount: Optional[Decimal] = Field(default=None, ge=0)
    probability: Optional[Decimal] = Field(default=None, ge=0, le=100)
    assigned_to_id: Optional[UUID] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    loss_reason: Optional[str] = None


class CustomerActivityCreateModel(BaseModel):
    activity_type: str = Field(default="call", pattern="^(call|meeting|followup|email)$")
    subject: str = Field(..., min_length=2, max_length=255)
    due_date: datetime
    reminder_minutes: Optional[int] = Field(default=15, ge=0)
    assigned_to_id: Optional[UUID] = None


class CustomerActivityUpdateModel(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|completed|cancelled)$")
    outcome: Optional[str] = None
    update_customer_status: Optional[str] = None
