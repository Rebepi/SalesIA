from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class InstallmentInput(BaseModel):
    due_date: date
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class PayableCreate(BaseModel):
    supplier_id: UUID
    invoice_match_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    document_number: str = Field(min_length=1, max_length=128)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    issue_date: date
    due_date: date
    notes: str = Field(default="", max_length=4000)
    installments: list[InstallmentInput] = Field(default_factory=list, max_length=120)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.due_date < self.issue_date:
            raise ValueError("El vencimiento no puede ser anterior a la emisión.")
        if self.installments:
            if sum(item.amount for item in self.installments) != self.amount:
                raise ValueError("La suma de cuotas debe ser igual al importe de la obligación.")
            if any(item.due_date < self.issue_date for item in self.installments):
                raise ValueError("Una cuota vence antes de la emisión.")
        return self


class VersionReason(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=2000)


class PayablePaymentCreate(BaseModel):
    version: int = Field(ge=1)
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    payment_date: date
    method: Literal["CASH", "MANUAL_TRANSFER", "OTHER", "SUPPLIER_CREDIT"]
    reference: str = Field(min_length=1, max_length=128)


class CostCenterCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=255)


class SupplierBalanceCreate(BaseModel):
    source_document_id: Optional[UUID] = None
    supplier_id: UUID
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    movement_date: date
    kind: Literal["advance", "credit", "refund"]
    reference: str = Field(min_length=1, max_length=128)
    notes: str = Field(min_length=3, max_length=2000)


class ExpenseAllocationInput(BaseModel):
    cost_center_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    category: str = Field(min_length=2, max_length=128)
    document_number: Optional[str] = Field(default=None, max_length=128)
    expense_date: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    notes: str = Field(default="", max_length=4000)
    allocations: list[ExpenseAllocationInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_allocations(self):
        if len({item.cost_center_id for item in self.allocations}) != len(self.allocations):
            raise ValueError("No repitas centros de costo en una distribución.")
        if sum(item.amount for item in self.allocations) != self.amount:
            raise ValueError("La distribución debe sumar exactamente el importe del gasto.")
        return self


class BudgetSave(BaseModel):
    cost_center_id: UUID
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    version: int = Field(default=0, ge=0)
