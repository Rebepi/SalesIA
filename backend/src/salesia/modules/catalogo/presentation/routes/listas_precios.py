from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.listas_precios as service_listas_precios
from salesia.modules.catalogo.application.contracts.listas_precios import (
    PriceListCreateModel,
    PriceListItemCreateModel,
    PriceListItemUpdateModel,
    PriceListUpdateModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/price-lists", status_code=status.HTTP_201_CREATED)
def create_price_list(
    req: PriceListCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.create_price_list(req=req, current_user=current_user, db=db)


@router.get("/price-lists")
def list_price_lists(
    current_user: AuthenticatedUser = Depends(require_permission("products:read")), db: Session = Depends(get_db)
):

    return service_listas_precios.list_price_lists(current_user=current_user, db=db)


@router.patch("/price-lists/{price_list_id}")
def update_price_list(
    price_list_id: UUID,
    req: PriceListUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.update_price_list(
        price_list_id=price_list_id, req=req, current_user=current_user, db=db
    )


@router.delete("/price-lists/{price_list_id}")
def delete_price_list(
    price_list_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.delete_price_list(price_list_id=price_list_id, current_user=current_user, db=db)


@router.post("/price-lists/{price_list_id}/items", status_code=status.HTTP_201_CREATED)
def add_price_list_item(
    price_list_id: UUID,
    req: PriceListItemCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.add_price_list_item(
        price_list_id=price_list_id, req=req, current_user=current_user, db=db
    )


@router.get("/price-lists/{price_list_id}/items")
def list_price_list_items(
    price_list_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:read")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.list_price_list_items(price_list_id=price_list_id, current_user=current_user, db=db)


@router.patch("/price-lists/{price_list_id}/items/{item_id}")
def update_price_list_item(
    price_list_id: UUID,
    item_id: UUID,
    req: PriceListItemUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.update_price_list_item(
        price_list_id=price_list_id, item_id=item_id, req=req, current_user=current_user, db=db
    )


@router.delete("/price-lists/{price_list_id}/items/{item_id}")
def delete_price_list_item(
    price_list_id: UUID,
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_listas_precios.delete_price_list_item(
        price_list_id=price_list_id, item_id=item_id, current_user=current_user, db=db
    )
