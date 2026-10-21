from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import LandedChargeItem


class LandedCostRequest(BaseModel):
    charges: list[LandedChargeItem] = Field(min_length=1, max_length=50)
