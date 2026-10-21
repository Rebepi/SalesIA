from typing import Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field

from salesia.modules.analitica.schedules import VisualSchedule


class ReportScheduleCreateRequest(BaseModel):
    report_type: str = Field(..., min_length=2, validation_alias=AliasChoices("report_type", "template_code"))

    cron_expression: str = Field(default="0 8 * * *")

    format: str = Field(default="csv", pattern="^(csv|json|pdf|xlsx)$")

    recipients: list[EmailStr] = Field(
        default_factory=list, validation_alias=AliasChoices("recipients", "recipient_emails"), max_length=100
    )

    timezone: str = Field(default="America/Lima")

    schedule: Optional[VisualSchedule] = None


class ReportScheduleUpdateRequest(BaseModel):
    version: int = Field(ge=1)
    schedule: Optional[VisualSchedule] = None
    timezone: Optional[str] = None
    format: Optional[str] = Field(default=None, pattern="^(csv|json|pdf|xlsx)$")
    recipients: Optional[list[EmailStr]] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
