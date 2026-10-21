from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class InsightEvaluationRequest(BaseModel):
    data_pipeline_delayed: Optional[bool] = False

    force_new_episode: Optional[bool] = False

    check_cooldown: Optional[bool] = False

    period: Optional[str] = "current"


class InsightRuleSimulateRequest(BaseModel):
    rule_code: str

    candidate_threshold: Decimal
