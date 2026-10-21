from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import UnitConversionModel, UnitOfMeasureModel
from salesia.shared.infrastructure.errors import DomainConflictException


def convert_units(
    db: Session, company_id: UUID, from_unit: str, to_unit: str, quantity: Decimal, product_id: Optional[UUID] = None
) -> Decimal:
    if from_unit.upper() == to_unit.upper():
        return quantity

    query = select(UnitConversionModel).where(
        UnitConversionModel.company_id == company_id,
        UnitConversionModel.from_unit == from_unit.upper(),
        UnitConversionModel.to_unit == to_unit.upper(),
    )
    if product_id:
        conv = db.execute(query.where(UnitConversionModel.product_id == product_id)).scalars().first()
        if not conv:
            conv = db.execute(query.where(UnitConversionModel.product_id.is_(None))).scalars().first()
    else:
        conv = db.execute(query.where(UnitConversionModel.product_id.is_(None))).scalars().first()

    if conv:
        return (quantity * conv.factor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    rev_query = select(UnitConversionModel).where(
        UnitConversionModel.company_id == company_id,
        UnitConversionModel.from_unit == to_unit.upper(),
        UnitConversionModel.to_unit == from_unit.upper(),
    )
    if product_id:
        rev_conv = db.execute(rev_query.where(UnitConversionModel.product_id == product_id)).scalars().first()
        if not rev_conv:
            rev_conv = db.execute(rev_query.where(UnitConversionModel.product_id.is_(None))).scalars().first()
    else:
        rev_conv = db.execute(rev_query.where(UnitConversionModel.product_id.is_(None))).scalars().first()

    if rev_conv:
        return (quantity / rev_conv.factor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    raise DomainConflictException(f"No existe factor de conversión registrado entre {from_unit} y {to_unit}.")


def validate_unit_fraction(db: Session, company_id: UUID, unit_code: str, quantity: Decimal) -> None:
    unit = db.execute(
        select(UnitOfMeasureModel).where(
            UnitOfMeasureModel.company_id == company_id, UnitOfMeasureModel.code == unit_code.upper()
        )
    ).scalar_one_or_none()

    if unit and not unit.allow_fractions:
        if quantity % Decimal("1") != Decimal("0"):
            raise DomainConflictException(
                f"La unidad '{unit_code}' no permite cantidades fraccionarias. Cantidad debe ser entera."
            )
    elif not unit:
        if unit_code.upper() in ["NIU", "UNIT", "UNIDAD", "PIECE", "SERIAL"]:
            if quantity % Decimal("1") != Decimal("0"):
                raise DomainConflictException(
                    f"La unidad '{unit_code}' no permite cantidades fraccionarias. Cantidad debe ser entera."
                )
