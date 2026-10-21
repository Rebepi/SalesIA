from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from salesia.shared.infrastructure.database import Base, TimestampMixin


class BusinessFieldDefinitionModel(Base, TimestampMixin):
    __tablename__ = "business_field_definitions"
    __table_args__ = (UniqueConstraint("company_id", "resource_type", "key", name="uq_business_field_key"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    key: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(128))
    field_type: Mapped[str] = mapped_column(String(32))
    options_json: Mapped[str] = mapped_column(Text, default="[]")
    required_states_json: Mapped[str] = mapped_column(Text, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class BusinessFieldValuesModel(Base, TimestampMixin):
    __tablename__ = "business_field_values"
    __table_args__ = (UniqueConstraint("company_id", "resource_type", "resource_id", name="uq_business_field_values_entity"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[UUID] = mapped_column(index=True)
    values_json: Mapped[str] = mapped_column(Text, default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1)
