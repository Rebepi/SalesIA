from typing import Any

from pydantic import BaseModel


class TimeSeriesSplitRequest(BaseModel):
    records: list[dict[str, Any]]

    date_column: str = "date"

    value_column: str = "value"

    train_ratio: float = 0.8
