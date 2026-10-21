from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.listas_precios import (
    PriceListCreateModel,
    PriceListItemCreateModel,
    PriceListItemUpdateModel,
    PriceListUpdateModel,
)
from salesia.modules.catalogo.infrastructure_models import PriceListItemModel, PriceListModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def create_price_list(req: PriceListCreateModel, current_user: AuthenticatedUser, db: Session):
    dup = db.execute(
        select(PriceListModel).where(
            PriceListModel.company_id == current_user.company_id, PriceListModel.code == req.code
        )
    ).scalar_one_or_none()

    if dup:
        raise DomainConflictException(f"Ya existe una lista de precios con el código '{req.code}'.")

    pl = PriceListModel(
        id=uuid4(),
        company_id=current_user.company_id,
        code=req.code,
        name=req.name,
        currency=req.currency.upper(),
        priority=req.priority,
        valid_from=req.valid_from,
        valid_to=req.valid_to,
        target_type=req.target_type,
        target_id=req.target_id,
        is_active=True,
    )

    db.add(pl)

    db.commit()

    return {"id": str(pl.id), "code": pl.code, "name": pl.name, "currency": pl.currency, "priority": pl.priority}


def list_price_lists(current_user: AuthenticatedUser, db: Session):
    query = (
        select(PriceListModel)
        .where(PriceListModel.company_id == current_user.company_id)
        .order_by(PriceListModel.priority.desc())
    )

    rows = db.scalars(query).all()

    return [
        {
            "id": str(pl.id),
            "code": pl.code,
            "name": pl.name,
            "currency": pl.currency,
            "priority": pl.priority,
            "valid_from": pl.valid_from.isoformat()
            if hasattr(pl.valid_from, "isoformat")
            else (str(pl.valid_from) if pl.valid_from else None),
            "valid_to": pl.valid_to.isoformat()
            if hasattr(pl.valid_to, "isoformat")
            else (str(pl.valid_to) if pl.valid_to else None),
            "target_type": pl.target_type,
            "target_id": pl.target_id,
            "is_active": pl.is_active,
        }
        for pl in rows
    ]


def update_price_list(price_list_id: UUID, req: PriceListUpdateModel, current_user: AuthenticatedUser, db: Session):
    pl = db.execute(
        select(PriceListModel).where(
            PriceListModel.id == price_list_id, PriceListModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()

    if not pl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista de precios no encontrada")

    if req.is_active is not None:
        pl.is_active = req.is_active

    if req.name is not None:
        pl.name = req.name

    if req.priority is not None:
        pl.priority = req.priority

    if req.valid_from is not None:
        pl.valid_from = req.valid_from

    if req.valid_to is not None:
        pl.valid_to = req.valid_to

    if req.currency is not None:
        pl.currency = req.currency.upper()

    if req.target_type is not None:
        pl.target_type = req.target_type

    if req.target_id is not None or "target_id" in req.model_fields_set:
        pl.target_id = req.target_id

    db.commit()

    db.refresh(pl)

    return {
        "id": str(pl.id),
        "code": pl.code,
        "name": pl.name,
        "currency": pl.currency,
        "priority": pl.priority,
        "is_active": pl.is_active,
        "valid_from": pl.valid_from.isoformat() if pl.valid_from else None,
        "valid_to": pl.valid_to.isoformat() if pl.valid_to else None,
        "target_type": pl.target_type,
        "target_id": pl.target_id,
    }


def delete_price_list(price_list_id: UUID, current_user: AuthenticatedUser, db: Session):
    pl = db.execute(
        select(PriceListModel).where(
            PriceListModel.id == price_list_id, PriceListModel.company_id == current_user.company_id
        )
    ).scalar_one_or_none()

    if not pl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista de precios no encontrada")

    from salesia.modules.clientes.infrastructure.models import CustomerProfileModel

    assigned_cust = db.execute(
        select(CustomerProfileModel).where(CustomerProfileModel.price_list_id == str(price_list_id))
    ).first()

    if assigned_cust:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar la lista '{pl.name}' porque está asignada a uno o más clientes. Desactívela en su lugar.",
        )

    db.delete(pl)

    db.commit()

    return {"message": f"Lista de precios '{pl.code}' eliminada exitosamente", "id": str(price_list_id)}


def add_price_list_item(
    price_list_id: UUID, req: PriceListItemCreateModel, current_user: AuthenticatedUser, db: Session
):
    price_list = db.scalar(
        select(PriceListModel).where(
            PriceListModel.id == price_list_id, PriceListModel.company_id == current_user.company_id
        )
    )

    product = db.scalar(
        select(ProductModel).where(
            ProductModel.id == req.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if not price_list or not product:
        raise DomainNotFoundException("Lista de precios o producto no encontrado.")

    if req.fixed_price is None and req.discount_percentage is None:
        raise HTTPException(422, "Indique un precio fijo o un descuento.")

    duplicate = db.scalar(
        select(PriceListItemModel.id).where(
            PriceListItemModel.company_id == current_user.company_id,
            PriceListItemModel.price_list_id == price_list_id,
            PriceListItemModel.product_id == req.product_id,
            PriceListItemModel.variant_id == req.variant_id,
        )
    )

    if duplicate:
        raise DomainConflictException("El producto ya pertenece a esta lista de precios.")

    item = PriceListItemModel(
        id=uuid4(),
        company_id=current_user.company_id,
        price_list_id=price_list_id,
        product_id=req.product_id,
        variant_id=req.variant_id,
        fixed_price=req.fixed_price,
        discount_percentage=req.discount_percentage,
    )

    db.add(item)

    db.commit()

    return {
        "id": str(item.id),
        "price_list_id": str(item.price_list_id),
        "product_id": str(item.product_id),
        "fixed_price": str(item.fixed_price) if item.fixed_price is not None else None,
        "discount_percentage": str(item.discount_percentage) if item.discount_percentage is not None else None,
    }


def list_price_list_items(price_list_id: UUID, current_user: AuthenticatedUser, db: Session):
    price_list = db.scalar(
        select(PriceListModel).where(
            PriceListModel.id == price_list_id, PriceListModel.company_id == current_user.company_id
        )
    )

    if not price_list:
        raise DomainNotFoundException("Lista de precios no encontrada.")

    rows = db.execute(
        select(PriceListItemModel, ProductModel)
        .join(ProductModel, ProductModel.id == PriceListItemModel.product_id)
        .where(
            PriceListItemModel.company_id == current_user.company_id, PriceListItemModel.price_list_id == price_list_id
        )
        .order_by(ProductModel.name)
    ).all()

    return [
        {
            "id": str(item.id),
            "product_id": str(product.id),
            "sku": product.sku,
            "product_name": product.name,
            "base_price": str(product.unit_price),
            "fixed_price": str(item.fixed_price) if item.fixed_price is not None else None,
            "discount_percentage": str(item.discount_percentage) if item.discount_percentage is not None else None,
            "variant_id": str(item.variant_id) if item.variant_id else None,
        }
        for item, product in rows
    ]


def update_price_list_item(
    price_list_id: UUID, item_id: UUID, req: PriceListItemUpdateModel, current_user: AuthenticatedUser, db: Session
):
    item = db.scalar(
        select(PriceListItemModel).where(
            PriceListItemModel.id == item_id,
            PriceListItemModel.price_list_id == price_list_id,
            PriceListItemModel.company_id == current_user.company_id,
        )
    )

    if not item:
        raise DomainNotFoundException("Producto de la lista no encontrado.")

    if req.fixed_price is None and req.discount_percentage is None:
        raise HTTPException(422, "Indique un precio fijo o un descuento.")

    item.fixed_price = req.fixed_price

    item.discount_percentage = req.discount_percentage

    db.commit()

    return {
        "id": str(item.id),
        "fixed_price": str(item.fixed_price) if item.fixed_price is not None else None,
        "discount_percentage": str(item.discount_percentage) if item.discount_percentage is not None else None,
    }


def delete_price_list_item(price_list_id: UUID, item_id: UUID, current_user: AuthenticatedUser, db: Session):
    item = db.scalar(
        select(PriceListItemModel).where(
            PriceListItemModel.id == item_id,
            PriceListItemModel.price_list_id == price_list_id,
            PriceListItemModel.company_id == current_user.company_id,
        )
    )

    if not item:
        raise DomainNotFoundException("Producto de la lista no encontrado.")

    db.delete(item)

    db.commit()

    return {"id": str(item_id), "deleted": True}
