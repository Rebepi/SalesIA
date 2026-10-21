from pydantic import BaseModel


class SanitizeInputRequest(BaseModel):
    raw_text: str
