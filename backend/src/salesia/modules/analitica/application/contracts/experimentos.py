from typing import Any

from pydantic import BaseModel


class ABExperimentRequest(BaseModel):
    events: list[dict[str, Any]]

    is_randomized: bool = True
