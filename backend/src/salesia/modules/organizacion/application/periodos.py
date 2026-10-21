import json
import calendar
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import select

from salesia.shared.infrastructure.models import CompanyModel
from salesia.shared.infrastructure.transactions import CompanySettings


def require_open_period(db, company_id, operation_date: date, modules=None):
    db.scalar(select(CompanyModel).where(CompanyModel.id == company_id).with_for_update())
    row = db.get(CompanySettings, company_id)
    saved = json.loads(row.values_json or "{}") if row else {}
    closed_until = saved.get("closed_until")
    controls = saved.get("module_periods", {})
    requested = modules or db.info.get("period_modules") or list(controls) or ["general"]
    now = datetime.now(timezone.utc)
    general_closed = bool(closed_until and operation_date <= date.fromisoformat(closed_until)) or operation_date.strftime("%Y-%m") in saved.get("closed_periods", [])
    reopened = []
    for module in requested:
        control = controls.get(module, {})
        local_cutoff = control.get("closed_until")
        module_closed = bool(local_cutoff and operation_date <= date.fromisoformat(local_cutoff))
        if not general_closed and not module_closed:
            continue
        authorizations = control.get("reopenings", []) if module_closed else [*saved.get("reopened_period_ranges", []), *control.get("reopenings", [])]
        authorization = next((period for period in reversed(authorizations) if date.fromisoformat(period["start"]) <= operation_date <= date.fromisoformat(period["end"]) and (not period.get("modules") or module in period["modules"]) and (not period.get("expires_at") or datetime.fromisoformat(period["expires_at"]).astimezone(timezone.utc) > now)), None)
        if authorization is None:
            raise HTTPException(409, f"La operación del módulo {module} pertenece a un período cerrado. Autorice únicamente el tramo necesario antes de modificarlo.")
        reopened.append({"module": module, "authorization": authorization})
    actor = db.info.get("period_actor")
    if reopened and actor:
        identity = (str(company_id), operation_date.isoformat(), tuple(requested))
        recorded = db.info.setdefault("period_reopening_audits", set())
        if identity not in recorded:
            from salesia.modules.auditoria.service import record_audit_event
            record_audit_event(db, company_id=company_id, actor_id=actor["id"], actor_email=actor["email"], action="OPERATION_IN_REOPENED_PERIOD", entity_type="AccountingPeriod", entity_id=company_id, diff={"business_date": operation_date.isoformat(), "authorizations": reopened, "request": db.info.get("period_request")})
            recorded.add(identity)


def request_period_modules(module, path):
    if "/commission" in path or "/performance-targets" in path:
        return ["commissions"]
    if any(part in path for part in ("/cash-", "/petty-cash")):
        return ["treasury"]
    if any(part in path for part in ("/returns", "/refunds", "/credit-notes")):
        return ["returns"]
    if any(part in path for part in ("/payables", "/supplier-credits", "/supplier-balances")):
        return ["payables"]
    if any(part in path for part in ("/expenses", "/expense-", "/budgets")):
        return ["expenses"]
    if any(part in path for part in ("/purchase", "/supplier", "/goods-receipts")):
        return ["purchases"]
    if module == "ventas":
        return ["sales"]
    if module == "inventario":
        return ["inventory"]
    if module == "finanzas":
        return ["receivables"]
    return []


def require_open_range(db, company_id, start, end, modules=None):
    if end < start or (end - start).days > 366:
        raise HTTPException(422, "El tramo de validación debe abarcar como máximo 367 días ordenados.")
    day = start
    while day <= end:
        require_open_period(db, company_id, day, modules)
        if day == end:
            break
        day += timedelta(days=1)


def require_open_month(db, company_id, period, modules=None):
    try:
        start = date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(422, "Indique un período válido con formato AAAA-MM.")
    end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
    require_open_range(db, company_id, start, end, modules)


def business_date(db, company_id, at=None):
    row = db.get(CompanySettings, company_id)
    saved = json.loads(row.values_json or "{}") if row else {}
    try:
        zone = ZoneInfo(saved.get("timezone", "America/Lima"))
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, "La zona horaria de la empresa no es válida.")
    moment = at or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(zone).date()
