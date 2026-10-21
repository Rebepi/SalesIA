from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class CategoryModel(Base, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_categories_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UnitOfMeasureModel(Base, TimestampMixin):
    __tablename__ = "units_of_measure"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_units_of_measure_company_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    allow_fractions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    precision_digits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UnitConversionModel(Base, TimestampMixin):
    __tablename__ = "unit_conversions"
    __table_args__ = (
        CheckConstraint("factor > 0", name="ck_unit_conversion_factor_positive"),
        UniqueConstraint("company_id", "from_unit", "to_unit", "product_id", name="uq_unit_conversions_scope"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    from_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    to_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    factor: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
