from pydantic import BaseModel, Field


class SettingRequest(BaseModel):
    key: str = Field(pattern="^[a-z][a-z0-9_.-]{1,63}$")

    value: bool | str | int | list[str]

    version: int = Field(ge=0)
