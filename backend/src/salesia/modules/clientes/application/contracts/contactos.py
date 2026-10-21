from typing import Literal, Optional
from datetime import date

from pydantic import BaseModel, Field, model_validator


class ContactValidity(BaseModel):
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_active: bool = True

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("El fin de vigencia debe ser posterior al inicio.")
        return self


class CustomerContactCreateModel(ContactValidity):
    name: str = Field(..., min_length=2, max_length=255)
    role: str = Field(default="Contacto", max_length=128)
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False
    preferences: Optional[dict] = None
    purpose: Literal["general", "purchasing", "billing", "delivery"] = "general"
    can_purchase: bool = True
    can_receive: bool = False


class CustomerAddressCreateModel(ContactValidity):
    address_type: str = Field(default="comercial", pattern="^(comercial|fiscal|entrega)$")
    street: str = Field(..., min_length=3, max_length=255)
    city: str = Field(default="Lima", max_length=128)
    state: Optional[str] = None
    country: str = Field(default="PE", max_length=64)
    postal_code: Optional[str] = None
    is_primary: bool = False


class CustomerContactUpdateModel(CustomerContactCreateModel):
    version: int = Field(ge=1)


class CustomerAddressUpdateModel(CustomerAddressCreateModel):
    version: int = Field(ge=1)
