from pydantic import BaseModel


class MaskDataRequest(BaseModel):
    data: dict[str, str]
