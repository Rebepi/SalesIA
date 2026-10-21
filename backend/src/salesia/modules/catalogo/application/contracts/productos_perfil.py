from pydantic import BaseModel, Field


class ProductCommercialProfileUpdate(BaseModel):
    product_type: str = Field(default="product", pattern="^(product|service)$")

    track_inventory: bool = True

    default_warranty_months: int = Field(default=0, ge=0)

    allow_fractional: bool = False
