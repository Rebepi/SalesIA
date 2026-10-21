from uuid import UUID

import jwt
from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import CompanyModel, QuotationModel
from salesia.shared.infrastructure.tenant_scope import bind_company


def public_quotation(db, quotation_id, authorization, lock=False):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "El enlace de cotización es inválido o ha vencido.")

    try:
        payload = jwt.decode(
            authorization[7:],
            settings.secret_key,
            algorithms=["HS256"],
            audience="quotation_portal",
            options={"require": ["exp", "sub", "company_id", "version"]},
        )

        if payload.get("purpose") != "quotation_share" or payload["sub"] != str(quotation_id):
            raise ValueError("scope")

        company_id = UUID(payload["company_id"])

        bind_company(db, company_id)

    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "El enlace de cotización es inválido o ha vencido.")

    query = select(QuotationModel).where(
        QuotationModel.id == quotation_id,
        QuotationModel.company_id == company_id,
        QuotationModel.version == payload["version"],
    )

    row = db.scalar(query.with_for_update() if lock else query)

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == company_id, CompanyModel.is_active.is_(True)))

    if not row or not company or row.status not in ("pending", "negotiating", "accepted", "converted"):
        raise HTTPException(410, "Esta propuesta ya no está disponible. Solicita una versión vigente a tu vendedor.")

    return row
