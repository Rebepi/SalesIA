import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    IntegrationCreateRequest,
    PaymentIntentConfirmRequest,
    PaymentIntentCreateRequest,
    PaymentIntentSyncRequest,
)
from salesia.modules.finanzas.infrastructure_models import PaymentIntentModel
from salesia.modules.operaciones.infrastructure_models import IntegrationConnection, WebhookReceipt
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.sessions import cipher
from salesia.shared.infrastructure.models import PaymentModel, SaleModel
from salesia.shared.infrastructure.tenant_scope import bind_company
from salesia.shared.infrastructure.workers import verify_webhook_signature


def create_payment_connection(payload: IntegrationCreateRequest, current_user: AuthenticatedUser, db: Session):
    secret = f"whsec_{secrets.token_urlsafe(36)}"

    row = IntegrationConnection(
        company_id=current_user.company_id,
        provider=payload.provider,
        encrypted_secret=cipher().encrypt(secret.encode()).decode(),
        active=True,
    )

    db.add(row)

    db.commit()

    return {
        "connection_id": str(row.id),
        "provider": row.provider,
        "webhook_secret": secret,
        "active": True,
        "created_at": row.created_at.isoformat(),
    }


def rotate_payment_connection_secret(connection_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.id == connection_id, IntegrationConnection.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Conexión de pago no encontrada.")

    secret = f"whsec_{secrets.token_urlsafe(36)}"

    row.previous_encrypted_secret = row.encrypted_secret

    row.previous_valid_until = datetime.now(timezone.utc) + timedelta(minutes=15)

    row.encrypted_secret = cipher().encrypt(secret.encode()).decode()

    db.commit()

    return {
        "connection_id": str(row.id),
        "webhook_secret": secret,
        "previous_secret_valid_until": row.previous_valid_until.isoformat(),
    }


async def payment_webhook(
    connection_id: UUID,
    request: Request,
    x_webhook_signature: Optional[str],
    x_webhook_timestamp: Optional[int],
    x_webhook_event_id: Optional[str],
    db: Session,
):
    body = await request.body()
    return await run_in_threadpool(process_payment_webhook, connection_id, body, x_webhook_signature, x_webhook_timestamp, x_webhook_event_id, db)


def process_payment_webhook(connection_id: UUID, body: bytes, x_webhook_signature: Optional[str], x_webhook_timestamp: Optional[int], x_webhook_event_id: Optional[str], db: Session):
    connection = db.get(IntegrationConnection, connection_id)

    if not connection or not connection.active:
        raise HTTPException(404, "Conexión de pago no encontrada.")

    bind_company(db, connection.company_id)

    if not x_webhook_signature or not x_webhook_timestamp or not x_webhook_event_id:
        raise HTTPException(401, "Firma, timestamp e identificador de evento son obligatorios.")

    if len(x_webhook_event_id) > 255:
        raise HTTPException(422, "El identificador del evento supera 255 caracteres.")

    received_at = datetime.now(timezone.utc)

    if abs(int(received_at.timestamp()) - x_webhook_timestamp) > 300:
        raise HTTPException(401, "El webhook está fuera de la ventana temporal.")

    try:
        json.loads(body)

    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(422, "El payload no es JSON válido.")

    signed = str(x_webhook_timestamp).encode() + b"." + body

    secrets_to_try = [cipher().decrypt(connection.encrypted_secret.encode()).decode()]

    valid_until = connection.previous_valid_until

    if (
        connection.previous_encrypted_secret
        and valid_until
        and (valid_until.replace(tzinfo=timezone.utc) if valid_until.tzinfo is None else valid_until) >= received_at
    ):
        secrets_to_try.append(cipher().decrypt(connection.previous_encrypted_secret.encode()).decode())

    if not any(verify_webhook_signature(signed, value, x_webhook_signature) for value in secrets_to_try):
        raise HTTPException(401, "Firma de webhook inválida.")

    existing = db.scalar(
        select(WebhookReceipt).where(
            WebhookReceipt.company_id == connection.company_id,
            WebhookReceipt.connection_id == str(connection.id),
            WebhookReceipt.event_id == x_webhook_event_id,
        )
    )

    if existing:
        return {
            "received": True,
            "connection_id": str(connection.id),
            "event_id": x_webhook_event_id,
            "status": "duplicate",
        }

    receipt = WebhookReceipt(
        company_id=connection.company_id,
        connection_id=str(connection.id),
        event_id=x_webhook_event_id,
        payload_hash=hashlib.sha256(body).hexdigest(),
    )

    db.add(receipt)

    db.commit()

    return {
        "received": True,
        "connection_id": str(connection.id),
        "event_id": x_webhook_event_id,
        "status": "processed",
        "timestamp": received_at.isoformat(),
    }


def create_payment_intent(
    payload: PaymentIntentCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    sale = db.scalar(
        select(SaleModel).where(SaleModel.id == payload.sale_id, SaleModel.company_id == current_user.company_id)
    )

    if not sale:
        raise HTTPException(404, "Venta no encontrada.")

    intent = PaymentIntentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=sale.id,
        provider=payload.provider,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
        client_secret=f"pi_sec_{uuid4().hex}",
        idempotency_key=idempotency_key,
    )

    db.add(intent)

    db.commit()

    return {
        "intent_id": str(intent.id),
        "sale_id": str(intent.sale_id),
        "provider": intent.provider,
        "amount": str(intent.amount),
        "currency": intent.currency,
        "status": intent.status,
        "client_secret": intent.client_secret,
    }


def get_payment_intent(intent_id: UUID, current_user: AuthenticatedUser, db: Session):
    intent = db.scalar(
        select(PaymentIntentModel).where(
            PaymentIntentModel.id == intent_id, PaymentIntentModel.company_id == current_user.company_id
        )
    )

    if not intent:
        raise HTTPException(404, "Intento de pago no encontrado.")

    return {
        "intent_id": str(intent.id),
        "sale_id": str(intent.sale_id),
        "status": intent.status,
        "amount": str(intent.amount),
        "currency": intent.currency,
    }


def confirm_payment_intent(
    intent_id: UUID, payload: PaymentIntentConfirmRequest, current_user: AuthenticatedUser, db: Session
):
    intent = db.scalar(
        select(PaymentIntentModel)
        .where(PaymentIntentModel.id == intent_id, PaymentIntentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not intent:
        raise HTTPException(404, "Intento de pago no encontrado.")

    if intent.status == "succeeded":
        return {"intent_id": str(intent.id), "status": intent.status}

    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == intent.sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not sale:
        raise HTTPException(404, "Venta no encontrada.")

    if not payload.gateway_token.startswith("tok_"):
        raise HTTPException(422, "Token de pasarela inválido.")

    sale.paid_amount = (sale.paid_amount + intent.amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if sale.paid_amount >= sale.total_amount:
        sale.status = "paid"

    payment = PaymentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=sale.id,
        payment_method="CARD",
        amount=intent.amount,
        currency=intent.currency,
        reference_code=payload.gateway_token,
        status="confirmed",
    )

    db.add(payment)

    intent.status = "succeeded"

    db.commit()

    return {"intent_id": str(intent.id), "payment_id": str(payment.id), "status": intent.status}


def sync_payment_intent_status(
    intent_id: UUID, payload: PaymentIntentSyncRequest, current_user: AuthenticatedUser, db: Session
):
    intent = db.scalar(
        select(PaymentIntentModel)
        .where(PaymentIntentModel.id == intent_id, PaymentIntentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not intent:
        raise HTTPException(404, "Intento de pago no encontrado.")

    if "timeout" in payload.gateway_response.lower() or "unknown" in payload.gateway_response.lower():
        intent.status = "pending_reconciliation"

    else:
        intent.status = "failed"

    db.commit()

    return {"intent_id": str(intent.id), "status": intent.status}
