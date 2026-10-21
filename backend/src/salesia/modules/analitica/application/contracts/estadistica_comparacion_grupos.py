from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class GroupsTestRequest(BaseModel):
    group_a: list[Decimal]

    group_b: list[Decimal]

    paired: bool = False

    alternative: str = "two-sided"

    equal_var: Optional[bool] = None

    preregistered: bool = True
