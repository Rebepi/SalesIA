import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application.auxiliares.default_settings_dict import default_settings_dict
from salesia.modules.organizacion.application.auxiliares.quota_usage import quota_usage
from salesia.modules.organizacion.application.contracts.organizacion import (
    BrandingPreviewModel,
    ContextSwitchModel,
    OnboardingSetupModel,
    PeriodCloseModel,
    PeriodReopenModel,
    PreferenceResetModel,
    QuotaCheckModel,
    TaxRuleModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel, BranchModel, CompanyModel, WarehouseModel
from salesia.shared.infrastructure.transactions import CompanySettings, DocumentSequence, next_number


def get_onboarding_status(current_user: AuthenticatedUser, db: Session):
    company = db.get(CompanyModel, current_user.company_id)
    branches_count = (
        db.scalar(
            select(func.count()).select_from(BranchModel).where(BranchModel.company_id == current_user.company_id)
        )
        or 0
    )
    warehouses_count = (
        db.scalar(
            select(func.count()).select_from(WarehouseModel).where(WarehouseModel.company_id == current_user.company_id)
        )
        or 0
    )
    sequences_count = (
        db.scalar(
            select(func.count())
            .select_from(DocumentSequence)
            .where(DocumentSequence.company_id == current_user.company_id)
        )
        or 0
    )

    next_step = "completed"
    if not company:
        next_step = "company"
    elif branches_count == 0:
        next_step = "branch"
    elif warehouses_count == 0:
        next_step = "warehouse"
    elif sequences_count == 0:
        next_step = "series"

    return {
        "company_id": current_user.company_id,
        "tax_id": company.tax_id if company else None,
        "legal_name": company.legal_name if company else None,
        "branches_count": branches_count,
        "warehouses_count": warehouses_count,
        "sequences_count": sequences_count,
        "is_completed": next_step == "completed",
        "next_step": next_step,
    }


def run_onboarding_setup(req: OnboardingSetupModel, current_user: AuthenticatedUser, db: Session):
    company = db.get(CompanyModel, current_user.company_id)
    resumed = False
    if not company:
        company = CompanyModel(
            id=current_user.company_id,
            tax_id=req.tax_id,
            legal_name=req.legal_name,
            trade_name=req.trade_name or req.legal_name,
            base_currency=req.base_currency,
            is_active=True,
        )
        db.add(company)
        db.flush()
    else:
        resumed = True

    branch = db.scalar(
        select(BranchModel).where(BranchModel.company_id == company.id, BranchModel.code == req.branch_code)
    )
    if not branch:
        branch = BranchModel(
            id=uuid4(),
            company_id=company.id,
            code=req.branch_code,
            name=req.branch_name,
            timezone=req.timezone,
            is_active=True,
        )
        db.add(branch)
        db.flush()

    warehouse = db.scalar(
        select(WarehouseModel).where(WarehouseModel.company_id == company.id, WarehouseModel.code == req.warehouse_code)
    )
    if not warehouse:
        warehouse = WarehouseModel(
            id=uuid4(),
            company_id=company.id,
            branch_id=branch.id,
            code=req.warehouse_code,
            name=req.warehouse_name,
            is_active=True,
        )
        db.add(warehouse)
        db.flush()

    seq = db.get(DocumentSequence, {"company_id": company.id, "series": req.series})
    if not seq:
        seq = DocumentSequence(company_id=company.id, series=req.series, value=0)
        db.add(seq)

    db.commit()
    return {
        "status": "completed",
        "company_id": company.id,
        "branch_id": branch.id,
        "warehouse_id": warehouse.id,
        "series": req.series,
        "resumed": resumed,
    }


def switch_branch_context(req: ContextSwitchModel, current_user: AuthenticatedUser, db: Session):
    branch = db.scalar(
        select(BranchModel).where(
            BranchModel.id == req.branch_id,
            BranchModel.company_id == current_user.company_id,
            BranchModel.is_active.is_(True),
        )
    )
    if not branch:
        raise HTTPException(404, "Sucursal no encontrada o inactiva.")
    return {
        "company_id": current_user.company_id,
        "branch_id": branch.id,
        "branch_code": branch.code,
        "branch_name": branch.name,
        "timezone": branch.timezone,
        "invalidated_caches": ["catalog", "customers", "inventory", "drafts", "sales"],
    }


def get_preferences_hierarchy(current_user: AuthenticatedUser, db: Session):
    defaults = default_settings_dict()
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    effective = {**defaults, **saved}
    return {"platform_defaults": defaults, "company_overrides": saved, "effective": effective}


def reset_preference(req: PreferenceResetModel, current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    if not row or not row.values_json:
        defaults = default_settings_dict()
        return {"key": req.key, "restored_value": defaults.get(req.key), "version": row.version if row else 0}
    current_values = json.loads(row.values_json)
    if req.key in current_values:
        del current_values[req.key]
        row.values_json = json.dumps(current_values)
        row.version += 1
        db.commit()
    defaults = default_settings_dict()
    return {"key": req.key, "restored_value": defaults.get(req.key), "version": row.version}


def list_sequences(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(select(DocumentSequence).where(DocumentSequence.company_id == current_user.company_id)).all()
    return [{"series": r.series, "value": r.value} for r in rows]


def reserve_next_sequence_number(series: str, current_user: AuthenticatedUser, db: Session):
    assigned = next_number(db, current_user.company_id, series)
    db.commit()
    return {"company_id": current_user.company_id, "series": series, "assigned_number": assigned}


def list_tax_rules(current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    custom_rules = saved.get("tax_rules")
    if custom_rules:
        return custom_rules
    return [
        {"code": "IGV", "rate": "0.1800", "name": "Impuesto General a las Ventas (18%)", "is_active": True},
        {"code": "EXO", "rate": "0.0000", "name": "Exonerado del Impuesto", "is_active": True},
        {"code": "INA", "rate": "0.0000", "name": "Inafecto de Impuesto", "is_active": True},
    ]


def update_tax_rule(req: TaxRuleModel, current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    current_values = default_settings_dict()
    if row and row.values_json:
        current_values.update(json.loads(row.values_json))
    rules = current_values.get("tax_rules") or [
        {"code": "IGV", "rate": "0.1800", "name": "Impuesto General a las Ventas (18%)", "is_active": True},
        {"code": "EXO", "rate": "0.0000", "name": "Exonerado del Impuesto", "is_active": True},
        {"code": "INA", "rate": "0.0000", "name": "Inafecto de Impuesto", "is_active": True},
    ]
    updated = False
    for r in rules:
        if r["code"] == req.code:
            r["rate"] = str(req.rate)
            r["name"] = req.name
            r["is_active"] = req.is_active
            updated = True
            break
    if not updated:
        rules.append({"code": req.code, "rate": str(req.rate), "name": req.name, "is_active": req.is_active})
    current_values["tax_rules"] = rules
    if row:
        row.version += 1
        row.values_json = json.dumps(current_values)
    else:
        row = CompanySettings(company_id=current_user.company_id, version=1, values_json=json.dumps(current_values))
        db.add(row)
    db.commit()
    return rules


def get_business_hours(current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    return saved.get(
        "business_hours",
        {
            "working_days": ["MON", "TUE", "WED", "THU", "FRI", "SAT"],
            "cutoff_time": "18:00",
            "timezone": "America/Lima",
        },
    )


def close_accounting_period(req: PeriodCloseModel, current_user: AuthenticatedUser, db: Session):
    from datetime import date
    from salesia.modules.organizacion.application.periodos import business_date
    cutoff = date.fromisoformat(req.closed_until)
    if cutoff > business_date(db, current_user.company_id):
        raise HTTPException(422, "No puedes cerrar un período futuro.")
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    row = db.get(CompanySettings, current_user.company_id)
    current_values = default_settings_dict()
    if row and row.values_json:
        current_values.update(json.loads(row.values_json))
    previous_cutoff = current_values.get("closed_until")
    if previous_cutoff and req.closed_until < previous_cutoff:
        raise HTTPException(409, "Usa la reapertura para modificar un cierre anterior.")
    current_values["reopened_period_ranges"] = [period for period in current_values.get("reopened_period_ranges", []) if period["start"] > req.closed_until]
    from salesia.modules.organizacion.application.periodos_funcionales import MODULES, pending
    pending_checks = pending(db, current_user.company_id, list(MODULES), cutoff)
    if any(item["blocking"] for item in pending_checks):
        raise HTTPException(409, {"message": "Hay bloqueos de operación pendientes. Revise el cierre por módulo antes de cerrar la empresa.", "checks": pending_checks})
    for control in current_values.get("module_periods", {}).values():
        control["reopenings"] = [period for period in control.get("reopenings", []) if period["start"] > req.closed_until]
    current_values["closed_until"] = req.closed_until
    if row:
        row.version += 1
        row.values_json = json.dumps(current_values)
    else:
        row = CompanySettings(company_id=current_user.company_id, version=1, values_json=json.dumps(current_values))
        db.add(row)
    db.add(
        AuditLogModel(
            id=uuid4(),
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="PERIOD_CLOSED",
            entity_type="AccountingPeriod",
            entity_id=current_user.company_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"closed_until": req.closed_until, "reason": req.reason}),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return {"status": "closed", "closed_until": req.closed_until, "version": row.version}


def reopen_accounting_period(req: PeriodReopenModel, current_user: AuthenticatedUser, db: Session):
    from datetime import date
    date.fromisoformat(req.reopen_date)
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    row = db.get(CompanySettings, current_user.company_id)
    current_values = default_settings_dict()
    if row and row.values_json:
        current_values.update(json.loads(row.values_json))
    cutoff = current_values.get("closed_until")
    if not cutoff or req.reopen_date > cutoff:
        raise HTTPException(409, "Selecciona una fecha que pertenezca al período cerrado.")
    end = (req.reopen_end or date.fromisoformat(req.reopen_date)).isoformat()
    if end < req.reopen_date or end > cutoff or (date.fromisoformat(end) - date.fromisoformat(req.reopen_date)).days > 366:
        raise HTTPException(422, "Indique únicamente el tramo cerrado que desea reabrir, con fechas ordenadas y hasta 367 días.")
    from datetime import timedelta
    moment = datetime.now(timezone.utc)
    ranges = current_values.get("reopened_period_ranges", [])
    ranges.append({"id": uuid4().hex, "start": req.reopen_date, "end": end, "expires_at": (moment + timedelta(hours=req.hours)).isoformat(), "reason": req.reason, "actor": current_user.email, "at": moment.isoformat()})
    current_values["reopened_period_ranges"] = ranges
    if row:
        row.version += 1
        row.values_json = json.dumps(current_values)
    else:
        row = CompanySettings(company_id=current_user.company_id, version=1, values_json=json.dumps(current_values))
        db.add(row)
    db.add(
        AuditLogModel(
            id=uuid4(),
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="PERIOD_REOPENED",
            entity_type="AccountingPeriod",
            entity_id=current_user.company_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"reopen_date": req.reopen_date, "reopen_end": end, "expires_at": ranges[-1]["expires_at"], "reason": req.reason}),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return {"status": "reopened", "reopen_date": req.reopen_date, "reopen_end": end, "expires_at": ranges[-1]["expires_at"], "version": row.version}


def get_branding(current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    return saved.get(
        "branding",
        {"logo_url": "", "legal_name": "SalesIA Enterprise", "footer_text": "Documento emitido electrónicamente."},
    )


def preview_branding(req: BrandingPreviewModel, current_user: AuthenticatedUser):
    safe_legal = (req.legal_name or "SalesIA Enterprise")[:128]
    safe_trade = (req.trade_name or safe_legal)[:128]
    safe_footer = (req.footer_text or "Comprobante de prueba")[:255]
    logo = (req.logo_url or "")[:512]
    return {
        "preview_header": f"{safe_legal} | {safe_trade}",
        "logo_url": logo,
        "preview_footer": safe_footer,
        "is_safe": True,
    }


def get_quotas(current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    quotas = saved.get(
        "quotas", {"max_files": 1000, "max_exports": 10, "max_import_rows": 5000, "max_intensive_queries": 50}
    )
    return {"company_id": current_user.company_id, "quotas": quotas, "usage": quota_usage(db, current_user.company_id)}


def check_quota(req: QuotaCheckModel, current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    saved = json.loads(row.values_json) if row and row.values_json else {}
    quotas = saved.get(
        "quotas", {"max_files": 1000, "max_exports": 10, "max_import_rows": 5000, "max_intensive_queries": 50}
    )
    resource_usage_keys = {
        "files": "files_used",
        "exports": "exports_active",
        "import_rows": "recent_import_rows",
        "intensive_queries": "intensive_queries_running",
    }
    usage_key = resource_usage_keys.get(req.resource)
    limit_key = f"max_{req.resource}"
    if not usage_key or limit_key not in quotas:
        raise HTTPException(422, "Recurso de cuota desconocido.")
    limit = int(quotas[limit_key])
    current_usage = quota_usage(db, current_user.company_id)[usage_key]
    projected_usage = current_usage + req.requested_quantity
    if projected_usage > limit:
        raise HTTPException(
            429,
            f"Se excedió la cuota de '{req.resource}'. Límite: {limit}, uso actual: {current_usage}, solicitado: {req.requested_quantity}. Considere procesar por lotes o contactar a soporte.",
        )
    return {
        "allowed": True,
        "resource": req.resource,
        "limit": limit,
        "current_usage": current_usage,
        "requested": req.requested_quantity,
        "projected_usage": projected_usage,
        "remaining_after_request": limit - projected_usage,
    }


def verify_test_mode(current_user: AuthenticatedUser, db: Session):
    company = db.get(CompanyModel, current_user.company_id)
    branches = db.scalars(select(BranchModel).where(BranchModel.company_id == current_user.company_id)).all()
    synthetic_base = Decimal("100.000000")
    synthetic_tax_rate = Decimal("0.1800")
    synthetic_tax = (synthetic_base * synthetic_tax_rate).quantize(Decimal("0.000001"))
    return {
        "test_mode": True,
        "verified": True,
        "database_connected": True,
        "company_verified": bool(company),
        "active_branches_count": len([b for b in branches if b.is_active]),
        "synthetic_tax_calculation": {
            "subtotal": str(synthetic_base),
            "rate": str(synthetic_tax_rate),
            "tax": str(synthetic_tax),
            "total": str(synthetic_base + synthetic_tax),
        },
        "live_effects_emitted": False,
    }
