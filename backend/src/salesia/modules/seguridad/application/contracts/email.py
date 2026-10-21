from pydantic import BaseModel, EmailStr


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
