import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.clientes.infrastructure.models import CustomerProfileModel


def resolve_payment_terms(db, company_id, customer_id, requested):
    profile = db.scalar(select(CustomerProfileModel).where(CustomerProfileModel.company_id == company_id, CustomerProfileModel.customer_id == customer_id))
    value = requested if requested is not None else profile.payment_terms_days if profile else 30
    if not 0 <= value <= 3650:
        raise HTTPException(422, "El plazo de pago debe estar entre cero y 3650 días.")
    return value


def set_sale_due_date(sale, confirmed_at, db=None):
    if db is None:
        sale.due_at = confirmed_at + timedelta(days=sale.payment_terms_days) if sale.is_credit else confirmed_at
        return
    from salesia.modules.organizacion.application.calendario_operativo import DateRequest, calculate_date, effective_calendar
    calendar = effective_calendar(db, sale.company_id, sale.branch_id)
    if not sale.is_credit or not calendar["configured"]:
        sale.due_at = confirmed_at + timedelta(days=sale.payment_terms_days) if sale.is_credit else confirmed_at
        snapshot = {"calendar": calendar, "due_at": sale.due_at.isoformat(), "legacy_elapsed_days": not calendar["configured"], "payment_terms_days": sale.payment_terms_days}
    else:
        moment = confirmed_at.replace(tzinfo=timezone.utc) if confirmed_at.tzinfo is None else confirmed_at
        result = calculate_date(calendar, DateRequest(start_at=moment, days=sale.payment_terms_days, purpose="payment", respect_cutoff=False))
        sale.due_at = datetime.fromisoformat(result["utc_at"])
        snapshot = {**result, "payment_terms_days": sale.payment_terms_days, "due_at": sale.due_at.isoformat()}
    sale.due_calendar_snapshot_json = json.dumps(snapshot)
