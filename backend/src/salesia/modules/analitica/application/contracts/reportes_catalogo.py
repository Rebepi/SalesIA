from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class ReportCompareRequest(BaseModel):
    run_id_1: UUID = Field(validation_alias=AliasChoices("run_id_1", "run_id_a"))

    run_id_2: UUID = Field(validation_alias=AliasChoices("run_id_2", "run_id_b"))
