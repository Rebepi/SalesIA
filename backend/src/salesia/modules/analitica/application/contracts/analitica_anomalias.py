from typing import Any

from pydantic import BaseModel


class AnomalyDetectionRequest(BaseModel):
    records: list[dict[str, Any]]

    feature_columns: list[str]

    method: str = "iqr"

    expected_alert_rate: float = 0.05
