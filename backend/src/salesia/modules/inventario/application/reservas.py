from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.reservas import (
    ReservationCreateRequest,
    ReservationReleaseRequest,
)
from salesia.modules.inventario.service import release_reservation, reserve_stock
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_reservation_endpoint(payload: ReservationCreateRequest, current_user: AuthenticatedUser, db: Session):
    res = reserve_stock(
        db,
        current_user.company_id,
        payload.warehouse_id,
        payload.product_id,
        payload.quantity,
        payload.document_type,
        payload.document_id,
        payload.allow_backorder,
    )

    db.commit()

    return {
        "id": str(res.id),
        "document_id": str(res.document_id),
        "reserved_quantity": str(res.reserved_quantity),
        "status": res.status,
    }


def release_reservation_endpoint(payload: ReservationReleaseRequest, current_user: AuthenticatedUser, db: Session):
    count = release_reservation(
        db, current_user.company_id, payload.document_type, payload.document_id, payload.product_id
    )

    db.commit()

    return {"released_count": count}
