from pydantic import BaseModel, Field


class PasswordResetConfirmModel(BaseModel):
    reset_token: str = Field(min_length=16, max_length=256)
    new_password: str = Field(min_length=12, max_length=1024)
