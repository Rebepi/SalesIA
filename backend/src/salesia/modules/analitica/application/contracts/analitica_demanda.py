from typing import Any

from pydantic import BaseModel


class DemandForecastCensoredRequest(BaseModel):
    records: list[dict[str, Any]]

    horizon: int = 7
