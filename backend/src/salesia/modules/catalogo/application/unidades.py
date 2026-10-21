from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.unidades import (
    UnitConversionCreateModel,
    UnitConvertRequest,
    UnitCreateModel,
)
from salesia.modules.catalogo.infrastructure_models import UnitConversionModel, UnitOfMeasureModel
from salesia.modules.catalogo.service import convert_units
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException
from salesia.shared.infrastructure.models import ProductModel


def list_units(current_user: AuthenticatedUser, db: Session):
    units = (
        db.execute(select(UnitOfMeasureModel).where(UnitOfMeasureModel.company_id == current_user.company_id))
        .scalars()
        .all()
    )

    if not units:
        defaults = [
            ("NIU", "Unidad", False, 0),
            ("KGM", "Kilogramo", True, 3),
            ("LTR", "Litro", True, 2),
            ("MTR", "Metro", True, 2),
            ("BX", "Caja", False, 0),
        ]

        created = []

        for code, name, allow_frac, prec in defaults:
            u = UnitOfMeasureModel(
                id=uuid4(),
                company_id=current_user.company_id,
                code=code,
                name=name,
                allow_fractions=allow_frac,
                precision_digits=prec,
                is_active=True,
            )

            db.add(u)

            created.append(u)

        db.commit()

        units = created

    return [
        {
            "id": str(u.id),
            "code": u.code,
            "name": u.name,
            "allow_fractions": u.allow_fractions,
            "precision_digits": u.precision_digits,
        }
        for u in units
    ]


def create_unit(req: UnitCreateModel, current_user: AuthenticatedUser, db: Session):
    existing = db.execute(
        select(UnitOfMeasureModel).where(
            UnitOfMeasureModel.company_id == current_user.company_id, UnitOfMeasureModel.code == req.code.upper()
        )
    ).scalar_one_or_none()

    if existing:
        raise DomainConflictException(f"La unidad '{req.code}' ya existe.")

    u = UnitOfMeasureModel(
        id=uuid4(),
        company_id=current_user.company_id,
        code=req.code.upper(),
        name=req.name,
        allow_fractions=req.allow_fractions,
        precision_digits=req.precision_digits,
        is_active=True,
    )

    db.add(u)

    db.commit()

    return {
        "id": str(u.id),
        "code": u.code,
        "name": u.name,
        "allow_fractions": u.allow_fractions,
        "precision_digits": u.precision_digits,
    }


def create_unit_conversion(req: UnitConversionCreateModel, current_user: AuthenticatedUser, db: Session):
    from_unit = req.from_unit.upper()

    to_unit = req.to_unit.upper()

    if from_unit == to_unit:
        raise HTTPException(422, "La unidad de origen y la unidad de destino deben ser diferentes.")

    available_units = db.scalars(
        select(UnitOfMeasureModel.code).where(
            UnitOfMeasureModel.company_id == current_user.company_id,
            UnitOfMeasureModel.code.in_((from_unit, to_unit)),
            UnitOfMeasureModel.is_active.is_(True),
        )
    ).all()

    if len(set(available_units)) != 2:
        raise HTTPException(422, "Ambas unidades deben existir y estar activas en la empresa.")

    if req.product_id:
        product = db.scalar(
            select(ProductModel.id).where(
                ProductModel.id == req.product_id, ProductModel.company_id == current_user.company_id
            )
        )

        if not product:
            raise HTTPException(404, "Producto no encontrado.")

    duplicate_query = select(UnitConversionModel.id).where(
        UnitConversionModel.company_id == current_user.company_id,
        UnitConversionModel.from_unit == from_unit,
        UnitConversionModel.to_unit == to_unit,
    )

    duplicate_query = (
        duplicate_query.where(UnitConversionModel.product_id == req.product_id)
        if req.product_id
        else duplicate_query.where(UnitConversionModel.product_id.is_(None))
    )

    if db.scalar(duplicate_query):
        raise HTTPException(409, "Ya existe una conversión para las unidades y el alcance indicados.")

    conv = UnitConversionModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=req.product_id,
        from_unit=from_unit,
        to_unit=to_unit,
        factor=req.factor,
    )

    db.add(conv)

    db.commit()

    return {
        "id": str(conv.id),
        "from_unit": conv.from_unit,
        "to_unit": conv.to_unit,
        "factor": str(conv.factor),
        "product_id": str(conv.product_id) if conv.product_id else None,
    }


def list_unit_conversions(current_user: AuthenticatedUser, db: Session):
    conversions = db.scalars(
        select(UnitConversionModel)
        .where(UnitConversionModel.company_id == current_user.company_id)
        .order_by(UnitConversionModel.created_at.desc())
    ).all()

    return [
        {
            "id": str(conversion.id),
            "from_unit": conversion.from_unit,
            "to_unit": conversion.to_unit,
            "factor": str(conversion.factor),
            "product_id": str(conversion.product_id) if conversion.product_id else None,
        }
        for conversion in conversions
    ]


def convert_unit_endpoint(req: UnitConvertRequest, current_user: AuthenticatedUser, db: Session):
    converted = convert_units(db, current_user.company_id, req.from_unit, req.to_unit, req.quantity, req.product_id)

    return {
        "from_unit": req.from_unit,
        "to_unit": req.to_unit,
        "original_quantity": str(req.quantity),
        "converted_quantity": str(converted),
    }
