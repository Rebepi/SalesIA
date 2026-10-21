import html
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.quotation_pdf import quotation_pdf
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response
from salesia.modules.pedidos.application.contracts.cotizaciones_documentos import QuotationSendRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthMail
from salesia.modules.seguridad.infrastructure.sessions import cipher, utcnow
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import CustomerModel, QuotationModel


def preview_quotation(quotation_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(QuotationModel)
        .where(QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Cotización no encontrada.")

    return quotation_response(row)


def download_quotation_pdf(quotation_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(QuotationModel).where(
            QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id
        )
    )

    if not row:
        raise HTTPException(404, "Cotización no encontrada.")

    return StreamingResponse(
        quotation_pdf(db, row),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{row.quotation_number}-v{row.version}.pdf"'},
    )


def send_quotation(quotation_id: UUID, req: QuotationSendRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(QuotationModel)
        .where(QuotationModel.id == quotation_id, QuotationModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Cotización no encontrada.")

    if row.status != "pending":
        raise HTTPException(409, "Solo se pueden enviar propuestas pendientes y vigentes.")

    expiration = (
        datetime.fromisoformat(row.valid_until).astimezone(timezone.utc)
        if row.valid_until
        else now() + timedelta(days=30)
    )

    if expiration <= now():
        raise HTTPException(409, "La propuesta ha vencido. Crea una versión actualizada antes de enviarla.")

    customer = db.scalar(
        select(CustomerModel).where(
            CustomerModel.id == row.customer_id, CustomerModel.company_id == current_user.company_id
        )
    )

    recipient = (req.recipient or (customer.email if req.channel == "EMAIL" else customer.phone) or "").strip()

    if not recipient:
        raise HTTPException(422, "El cliente no tiene un destinatario configurado para este canal.")

    token = jwt.encode(
        {
            "sub": str(row.id),
            "company_id": str(row.company_id),
            "version": row.version,
            "purpose": "quotation_share",
            "aud": "quotation_portal",
            "exp": expiration,
            "iat": now(),
        },
        settings.secret_key,
        algorithm="HS256",
    )

    url = f"{settings.frontend_url.rstrip('/')}/?quotation={row.id}#quotation-token={token}"

    if req.channel == "EMAIL":
        try:
            from pydantic import TypeAdapter

            TypeAdapter(EmailStr).validate_python(recipient)

        except ValueError:
            raise HTTPException(422, "Ingresa un correo válido para enviar la propuesta.")

    elif len("".join(char for char in recipient if char.isdigit())) < 8:
        raise HTTPException(422, "Ingresa el teléfono con código de país.")

    message = (
        req.message
        or f"Cotización {row.quotation_number} por {row.currency} {row.total_amount}. Válida hasta {row.valid_until or 'confirmación comercial'}."
    )

    result = {"channel": req.channel, "recipient": recipient, "status": "queued", "url": url}

    if req.channel == "EMAIL":
        payload = {
            "text": f"{message}\n\nVer cotización: {url}",
            "html": f'<div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;padding:32px;border:1px solid #dbe4ea;border-radius:20px"><div style="color:#0f766e;font-size:22px;font-weight:700">SalesIA Enterprise</div><h1 style="font-size:24px;color:#0f172a">{html.escape(row.quotation_number)}</h1><p style="color:#475569">{html.escape(message)}</p><div style="font-size:28px;font-weight:700;color:#0f172a;margin:24px 0">{row.currency} {row.total_amount}</div><a href="{html.escape(url)}" style="display:inline-block;background:#0f766e;color:white;text-decoration:none;padding:12px 20px;border-radius:10px">Ver cotización</a></div>',
        }

        db.add(
            AuthMail(
                recipient=recipient,
                encrypted_body=cipher().encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode(),
                subject=f"Cotización {row.quotation_number}",
                created_at=utcnow(),
            )
        )

    else:
        result["integration_url"] = (
            f"https://wa.me/{''.join(char for char in recipient if char.isdigit())}?text={urllib.parse.quote(message + ' ' + url)}"
        )

        result["status"] = "ready"

    row.sent_at = now()

    row.delivery_channel = req.channel

    row.delivery_recipient = recipient

    log = json.loads(row.communication_log_json or "[]")

    log.append(
        {
            "event": "SENT",
            "channel": req.channel,
            "recipient": recipient,
            "at": row.sent_at.isoformat(),
            "actor": current_user.email,
        }
    )

    row.communication_log_json = json.dumps(log)

    audit(
        db,
        current_user,
        "SEND",
        "Quotation",
        row.id,
        {"channel": req.channel, "recipient": recipient, "status": result["status"]},
    )

    db.commit()

    return result
