from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TrackingEventCreateRequest(BaseModel):
    event_code: str = Field(min_length=1, max_length=64)

    event_status: Literal["ready", "dispatched", "in_transit", "out_for_delivery", "delivered"]

    description: str = Field(min_length=2, max_length=255)

    location: Optional[str] = Field(default=None, max_length=128)

    occurred_at: Optional[datetime] = None


class ProofOfDeliveryRequest(BaseModel):
    outside_window_reason: str = Field(default="", max_length=2000)

    received_by_name: str = Field(min_length=2, max_length=255)

    received_by_id_doc: Optional[str] = Field(default=None, max_length=64)

    delivered_at: Optional[datetime] = None

    signature_data: Optional[str] = Field(default=None, max_length=10000)

    photo_url: Optional[str] = Field(default=None, max_length=500)

    notes: Optional[str] = Field(default=None, max_length=1000)


class DeliveryIncidentCreateRequest(BaseModel):
    incident_type: Literal["FAILED_ATTEMPT", "LOST", "DAMAGED", "RESCHEDULED", "RESCHEDULE", "RETURN_REQUESTED"]

    description: str = Field(min_length=3, max_length=1000)

    rescheduled_date: Optional[datetime] = None
