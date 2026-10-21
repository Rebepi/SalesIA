from decimal import Decimal

from pydantic import BaseModel


class EffectSizeRequest(BaseModel):
    group_a: list[Decimal]

    group_b: list[Decimal]
