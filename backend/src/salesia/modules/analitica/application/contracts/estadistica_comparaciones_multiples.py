from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class MultipleComparisonsRequest(BaseModel):
    p_values: list[dict[str, Any]]

    method: str = "bonferroni"

    alpha: Decimal = Decimal("0.05")
