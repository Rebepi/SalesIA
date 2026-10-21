from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from zoneinfo import ZoneInfo
import json

from salesia.modules.catalogo.infrastructure_models import ProductWarrantyClaimModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import CostBudgetModel, ExpenseModel, PayableModel
from salesia.modules.inventario.infrastructure_models import DeliveryShipment, InventoryLot, Supplier, SupplyDocument
from salesia.modules.operaciones.infrastructure_models import CollaborationTask
from salesia.shared.infrastructure.models import ProductModel
from salesia.shared.infrastructure.transactions import CompanySettings


OPERATIONAL_REPORTS = {
    "REP_SUPPLIER_PAYABLES": ("Obligaciones y vencimientos de proveedores", "finance", "payments:read", PayableModel, "issue_date", ("document_number", "supplier_id", "currency", "amount", "paid_amount", "due_date", "status")),
    "REP_OPERATING_EXPENSES": ("Gastos operativos y aprobaciones", "finance", "payments:read", ExpenseModel, "expense_date", ("title", "category", "document_number", "currency", "amount", "status")),
    "REP_COST_BUDGETS": ("Presupuestos por centro de costo", "finance", "payments:read", CostBudgetModel, "created_at", ("cost_center_id", "period", "currency", "amount", "version")),
    "REP_PURCHASE_PENDING": ("Órdenes de compra y saldos pendientes", "logistics", "purchases:read", SupplyDocument, "created_at", ("supplier_id", "warehouse_id", "status", "version")),
    "REP_DELIVERY_OPERATIONS": ("Entregas e incidencias operativas", "logistics", "inventory:read", DeliveryShipment, "created_at", ("recipient_name", "delivery_address", "carrier", "tracking_number", "estimated_delivery_date", "dispatched_at", "delivered_at", "status")),
    "REP_LOT_EXPIRATION": ("Lotes y fechas de vencimiento", "logistics", "inventory:read", InventoryLot, "created_at", ("product_id", "lot_code", "manufacture_date", "expiration_date", "status")),
    "REP_WARRANTY_CASES": ("Atención de garantías", "commercial", "sales:read", ProductWarrantyClaimModel, "claim_date", ("sale_id", "product_id", "serial_number", "quantity", "issue_description", "warranty_until", "assigned_to", "diagnosis", "resolution", "status")),
    "REP_TEAM_TASKS": ("Actividades y vencimientos de equipo", "operations", "operations:manage", CollaborationTask, "created_at", ("title", "description", "assignee_id", "due_date", "priority", "status", "parent_id")),
}


def report_catalog():
    return [{"code": code, "name": config[0], "area": config[1], "objective": config[0], "description": "Una fila por registro operativo, con moneda y estado explícitos.", "formats": ["csv", "xlsx", "pdf", "json"], "date_field": config[4], "currency": "transaction", "allowed_roles": ["company_admin", "manager", "auditor"], "status_filter": ["all"], "required_permission": config[2], "parameters_schema": {"start_date": "ISO-8601", "end_date": "ISO-8601", "status": "string", "currency": "string"}} for code, config in OPERATIONAL_REPORTS.items()]


def required_report_permissions(code):
    if code in OPERATIONAL_REPORTS:
        return {OPERATIONAL_REPORTS[code][2]}
    return {
        "REP_SALES_DETAIL": {"sales:read"},
        "REP_STATISTICAL_DISTRIBUTION": {"sales:read"},
        "REP_CRM_CATALOG": {"customers:read", "products:read"},
        "REP_SALES_REPS_COMMISSIONS": {"sales:read"},
        "REP_KARDEX_VALUATION": {"inventory:read"},
        "REP_CASH_CLOSURE_RECEIVABLES": {"payments:read"},
    }.get(code, {"reports:read"})


def authorize_report(user, code):
    missing = required_report_permissions(code) - set(user.permissions)
    if missing:
        raise HTTPException(403, f"El reporte requiere permisos: {', '.join(sorted(missing))}.")


def execute_operational_report(code, company_id, db, limit, params):
    _, _, _, model, date_field, fields = OPERATIONAL_REPORTS[code]
    statement = select(model).where(model.company_id == company_id)
    if model is SupplyDocument:
        statement = statement.where(model.kind == "PURCHASE_ORDER")
    if params.get("status") and params["status"] != "all" and hasattr(model, "status"):
        statement = statement.where(model.status == params["status"])
    if params.get("currency") and hasattr(model, "currency"):
        statement = statement.where(model.currency == params["currency"])
    column = getattr(model, date_field)
    setting = db.get(CompanySettings, company_id)
    saved = json.loads(setting.values_json or "{}") if setting else {}
    zone = ZoneInfo(saved.get("timezone", "America/Lima"))
    for parameter, end in (("start_date", False), ("end_date", True)):
        value = params.get(parameter)
        if not value:
            continue
        try:
            day = date.fromisoformat(str(value)[:10])
        except ValueError:
            raise ValueError(f"Fecha inválida: {parameter}.")
        is_date = date_field in ("issue_date", "expense_date")
        bound = day if is_date else datetime.combine(day, time.max if end else time.min, tzinfo=zone).astimezone(timezone.utc)
        statement = statement.where(column <= bound if end else column >= bound)
    columns = ["id", date_field, *[field for field in fields if field != date_field]]
    if model is PayableModel:
        columns += ["supplier_name", "balance"]
    if model in (InventoryLot, ProductWarrantyClaimModel):
        columns += ["product_name"]
    if model is SupplyDocument:
        columns += ["supplier_name", "currency", "pending_quantity", "total_amount"]
    rows = []
    for row in db.scalars(statement.order_by(column.desc(), model.id).limit(limit)).all():
        result = {}
        for field in ["id", date_field, *fields]:
            value = getattr(row, field)
            result[field] = value.isoformat() if isinstance(value, (date, datetime)) else str(value) if value is not None else ""
        if hasattr(row, "supplier_id"):
            supplier = db.scalar(select(Supplier).where(Supplier.company_id == company_id, Supplier.id == row.supplier_id))
            result["supplier_name"] = supplier.legal_name if supplier else ""
        if model is PayableModel:
            result["balance"] = str(row.amount - row.paid_amount if row.status != "cancelled" else Decimal("0"))
        if model in (InventoryLot, ProductWarrantyClaimModel):
            product = db.scalar(select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.id == row.product_id))
            result["product_name"] = product.name if product else ""
        if model is SupplyDocument:
            import json
            details = json.loads(row.details_json or "{}")
            result["currency"] = details.get("currency", "")
            result["pending_quantity"] = str(sum((max(Decimal("0"), line.quantity - line.processed_quantity - line.cancelled_quantity) for line in row.lines), Decimal("0")) if row.status not in ("cancelled", "closed") else Decimal("0"))
            result["total_amount"] = str(details.get("total", details.get("total_amount", "0")))
        rows.append(result)
    return columns, rows
