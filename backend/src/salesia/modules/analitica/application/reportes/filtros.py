from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from salesia.shared.infrastructure.models import CompanyModel, SaleModel
from salesia.shared.infrastructure.transactions import CompanySettings


def sales_filters(db, company_id, params, require_currency=False):
    import json
    filters = [SaleModel.company_id == company_id]
    company = db.get(CompanyModel, company_id)
    currency = params.get("currency") or (company.base_currency if require_currency and company else None)
    if currency:
        filters.append(SaleModel.currency == str(currency).upper())
    basis = params.get("date_basis", "created_at")
    if basis not in ("created_at", "confirmed_at", "due_at"):
        raise ValueError("La fecha de referencia debe ser emisión, confirmación o vencimiento.")
    column = getattr(SaleModel, basis)
    setting = db.get(CompanySettings, company_id)
    saved = json.loads(setting.values_json or "{}") if setting else {}
    zone = ZoneInfo(saved.get("timezone", "America/Lima"))
    for key, end in (("start_date", False), ("end_date", True)):
        value = params.get(key)
        if not value:
            continue
        try:
            text = str(value)
            if "T" in text:
                moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=zone)
            else:
                moment = datetime.combine(date.fromisoformat(text), time.max if end else time.min, tzinfo=zone)
        except ValueError:
            raise ValueError(f"La fecha {key} no es válida.")
        moment = moment.astimezone(timezone.utc)
        filters.append(column <= moment if end else column >= moment)
    return filters
