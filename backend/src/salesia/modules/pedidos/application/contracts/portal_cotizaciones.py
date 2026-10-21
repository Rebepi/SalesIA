from pydantic import BaseModel, Field


class PublicQuotationAcceptance(BaseModel):
    accepted_by: str = Field(min_length=2, max_length=200)

    conditions_accepted: bool
