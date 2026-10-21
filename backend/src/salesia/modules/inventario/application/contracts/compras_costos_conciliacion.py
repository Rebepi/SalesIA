from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import InvoiceMatchLine


class ThreeWayMatchRequest(BaseModel):
    supplier_invoice_number: str = Field(min_length=1, max_length=64)

    invoice_amount: Decimal = Field(gt=0, decimal_places=6, max_digits=20)

    invoice_lines: Optional[list[InvoiceMatchLine]] = Field(default=None, min_length=1, max_length=500)

    notes: Optional[str] = Field(default=None, max_length=500)
