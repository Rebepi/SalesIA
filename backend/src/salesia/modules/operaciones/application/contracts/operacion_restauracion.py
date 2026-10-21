from pydantic import BaseModel, Field


class RestoreVerifyRequest(BaseModel):
    snapshot_id: str = Field(min_length=1, max_length=64)

    checksum: str = Field(pattern="^[a-f0-9]{64}$")
