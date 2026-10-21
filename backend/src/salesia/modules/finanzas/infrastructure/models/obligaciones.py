from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class PayableModel(Base, TimestampMixin):
    __tablename__ = "supplier_payables"
    __table_args__ = (
        UniqueConstraint("company_id", "supplier_id", "document_number", name="uq_payable_supplier_document"),
        UniqueConstraint("invoice_match_id", name="uq_payable_invoice_match"),
        CheckConstraint("amount > 0 AND paid_amount >= 0 AND paid_amount <= amount", name="payable_balances"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    invoice_match_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("purchase_invoice_matches.id", ondelete="RESTRICT"), nullable=True)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supply_documents.id"), nullable=True)
    document_number: Mapped[str] = mapped_column(String(128))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str] = mapped_column(Text, default="")


class PayableInstallmentModel(Base):
    __tablename__ = "supplier_payable_installments"
    __table_args__ = (
        UniqueConstraint("payable_id", "sequence", name="uq_payable_installment_sequence"),
        CheckConstraint("amount > 0 AND paid_amount >= 0 AND paid_amount <= amount", name="payable_installment_balances"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    payable_id: Mapped[UUID] = mapped_column(ForeignKey("supplier_payables.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=Decimal("0"))


class PayablePaymentModel(Base, TimestampMixin):
    __tablename__ = "supplier_payable_payments"
    __table_args__ = (CheckConstraint("amount > 0", name="payable_payment_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    payable_id: Mapped[UUID] = mapped_column(ForeignKey("supplier_payables.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    payment_date: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(String(32))
    reference: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="posted")
    allocations_json: Mapped[str] = mapped_column(Text, default="[]")
    reversal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))


class CostCenterModel(Base, TimestampMixin):
    __tablename__ = "cost_centers"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_cost_center_code"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))


class SupplierBalanceMovementModel(Base, TimestampMixin):
    __tablename__ = "supplier_balance_movements"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id"), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    amount_delta: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    movement_date: Mapped[date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(32))
    reference: Mapped[str] = mapped_column(String(128))
    payment_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supplier_payable_payments.id"), nullable=True)
    source_claim_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supplier_claims.id"), nullable=True, index=True)
    source_document_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supply_documents.id"), nullable=True, index=True)
    reversal_of_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("supplier_balance_movements.id"), nullable=True)
    allocations_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]", nullable=False)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str] = mapped_column(Text, default="")


class ExpenseModel(Base, TimestampMixin):
    __tablename__ = "operating_expenses"
    petty_cash_advance_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("petty_cash_advances.id"), nullable=True, index=True)
    __table_args__ = (CheckConstraint("amount > 0", name="expense_positive"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(128))
    document_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    expense_date: Mapped[date] = mapped_column(Date, index=True)
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class ExpenseAllocationModel(Base):
    __tablename__ = "expense_allocations"
    __table_args__ = (
        UniqueConstraint("expense_id", "cost_center_id", name="uq_expense_center"),
        CheckConstraint("amount > 0", name="expense_allocation_positive"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    expense_id: Mapped[UUID] = mapped_column(ForeignKey("operating_expenses.id"), index=True)
    cost_center_id: Mapped[UUID] = mapped_column(ForeignKey("cost_centers.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))


class CostBudgetModel(Base, TimestampMixin):
    __tablename__ = "cost_budgets"
    __table_args__ = (
        UniqueConstraint("company_id", "cost_center_id", "period", "currency", name="uq_cost_budget_period"),
        CheckConstraint("amount >= 0", name="cost_budget_nonnegative"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    cost_center_id: Mapped[UUID] = mapped_column(ForeignKey("cost_centers.id"), index=True)
    period: Mapped[str] = mapped_column(String(7))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    version: Mapped[int] = mapped_column(Integer, default=1)
