from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.credito_tienda as service_credito_tienda
from salesia.modules.finanzas.application import reservas_credito_cliente as reservations
from salesia.modules.finanzas.application import conversiones_credito_cliente as conversions
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/customers/{customer_id}/store-credit")
def get_customer_store_credit(
    customer_id: UUID,
    currency: str | None = Query(None, pattern=r"^[A-Z]{3}$"),
    current_user: AuthenticatedUser = Depends(require_permission("customers:read")),
    db: Session = Depends(get_db),
):
    return service_credito_tienda.get_customer_store_credit(customer_id, current_user, db, currency)


@router.get("/customers/{customer_id}/store-credit/sales")
def eligible_credit_sales(
    customer_id: UUID,
    currency: str = Query(..., pattern=r"^[A-Z]{3}$"),
    search: str | None = Query(None, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):
    return service_credito_tienda.eligible_credit_sales(db, current_user, customer_id, currency, search, limit, offset)


@router.post("/customers/{customer_id}/store-credit/{movement_id}/identify-currency")
def identify_credit_currency(
    customer_id: UUID,
    movement_id: UUID,
    payload: service_credito_tienda.CreditCurrencyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage", "approvals:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):
    return service_credito_tienda.identify_credit_currency(db, current_user, customer_id, movement_id, payload, idempotency_key)


@router.post("/sales/{sale_id}/reserve-store-credit")
def reserve_credit(
    sale_id: UUID,
    payload: reservations.ReserveCreditRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write", "payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):
    return reservations.reserve_credit(db, current_user, sale_id, payload, idempotency_key)


@router.post("/customer-credit-reservations/{reservation_id}/release")
def release_credit(
    reservation_id: UUID,
    payload: reservations.ReleaseCreditRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write", "payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):
    return reservations.release_credit(db, current_user, reservation_id, payload, idempotency_key)


@router.get("/customers/{customer_id}/credit-conversions")
def list_credit_conversions(
    customer_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("customers:read")),
    db: Session = Depends(get_db),
):
    return conversions.list_conversions(db, current_user, customer_id, limit, offset)


@router.post("/customers/{customer_id}/credit-conversions")
def propose_credit_conversion(
    customer_id: UUID,
    payload: conversions.CreditConversionRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):
    return conversions.propose_conversion(db, current_user, customer_id, payload, idempotency_key)


@router.post("/customer-credit-conversions/{conversion_id}/review")
def review_credit_conversion(
    conversion_id: UUID,
    payload: conversions.CreditConversionReview,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):
    return conversions.review_conversion(db, current_user, conversion_id, payload, idempotency_key)
