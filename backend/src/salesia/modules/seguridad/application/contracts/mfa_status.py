from pydantic import BaseModel, EmailStr


class PasswordResetRequestModel(BaseModel):
    email: EmailStr
