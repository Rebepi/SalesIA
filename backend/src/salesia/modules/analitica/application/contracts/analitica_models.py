from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ModelRegisterRequest(BaseModel):
    name: str

    algorithm: str

    hyperparameters: dict[str, Any]

    feature_names: list[str]

    dataset_id: str

    dataset_version: int

    dataset_hash: str

    seed: int

    evaluation_metrics: dict[str, Any]

    previous_version_id: Optional[UUID] = None


class ModelMonitorRequest(BaseModel):
    training_distribution: list[float]

    current_distribution: list[float]

    error_metric_baseline: float

    current_error_metric: float

    error_threshold_ratio: float = 1.5
