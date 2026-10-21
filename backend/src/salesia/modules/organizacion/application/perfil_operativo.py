import hashlib
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel, ProductWarrantyClaimModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import ExpenseModel, PayableModel
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel, CashCustodyTransferModel
from salesia.modules.finanzas.infrastructure.models.caja_chica import PettyCashAdvanceModel
from salesia.modules.inventario.infrastructure_models import InventoryPickingList, InventoryQuarantine, InventoryReservation, InventorySerial, LocationStock, PhysicalCountSession, SupplyDocument
from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel
from salesia.modules.inventario.infrastructure.models.ventanas_entrega import DeliveryWindowReservationModel
from salesia.modules.pedidos.infrastructure.models.documentos import OrderModel, QuotationModel
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import CommissionSettlement as CommissionSettlementModel
from salesia.shared.infrastructure.models import CashSessionModel, CompanyModel, InventoryStockModel, ProductModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

AREAS = {
    "inventory": {"label": "Inventario físico", "requires": []},
    "purchases": {"label": "Compras de mercadería", "requires": ["inventory", "payables"]},
    "delivery": {"label": "Reparto y retiro programado", "requires": ["inventory"]},
    "quotations": {"label": "Cotizaciones", "requires": []},
    "orders": {"label": "Pedidos comerciales", "requires": ["quotations"]},
    "commissions": {"label": "Equipo, metas y comisiones", "requires": []},
    "cash": {"label": "Caja y efectivo", "requires": []},
    "credit": {"label": "Venta a crédito y cobranza", "requires": []},
    "warranties": {"label": "Garantías", "requires": []},
    "expenses": {"label": "Gastos y presupuestos", "requires": []},
    "payables": {"label": "Cuentas por pagar", "requires": []},
    "analytics": {"label": "Analítica avanzada", "requires": []},
}
PROFILES = {
    "complete": {"label": "Todas las áreas actuales", "enabled": list(AREAS)},
    "commerce": {"label": "Comercio", "enabled": [key for key in AREAS if key not in ("delivery",)]},
    "distribution": {"label": "Distribución", "enabled": list(AREAS)},
    "services": {"label": "Servicios sin existencias físicas", "enabled": ["quotations", "orders", "commissions", "cash", "credit", "warranties", "expenses", "payables", "analytics"]},
}


class ProfileChange(BaseModel):
    expected_version: int = Field(ge=0)
    profile: Literal["complete", "commerce", "distribution", "services", "custom"]
    enabled: list[str] = Field(max_length=12)
    reason: str = Field(min_length=5, max_length=2000)


class ProfileSave(ProfileChange):
    preview_hash: str = Field(min_length=64, max_length=64)


def current(db, company_id):
    row = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "operating_profile", AnalyticsArtifact.artifact_key == "company").order_by(AnalyticsArtifact.version.desc()).limit(1))
    return {"company_id": str(company_id), "version": row.version if row else 0, **(json.loads(row.data_json) if row else {"profile": "complete", "enabled": list(AREAS)}), "areas": AREAS, "profiles": PROFILES}


def blockers(db, company_id):
    result = {key: [] for key in AREAS}

    def check(area, label, model, *conditions):
        count = db.scalar(select(func.count()).select_from(model).where(model.company_id == company_id, *conditions)) or 0
        if count:
            result[area].append({"label": label, "count": count})

    check("inventory", "Existencias o reservas de stock", InventoryStockModel, or_(InventoryStockModel.physical_quantity != 0, InventoryStockModel.reserved_quantity != 0))
    check("inventory", "Existencias en ubicaciones", LocationStock, LocationStock.quantity != 0)
    check("inventory", "Reservas activas", InventoryReservation, InventoryReservation.status == "ACTIVE", InventoryReservation.reserved_quantity > 0)
    check("inventory", "Unidades en cuarentena", InventoryQuarantine, InventoryQuarantine.status == "IN_QUARANTINE", InventoryQuarantine.quantity > 0)
    check("inventory", "Series en custodia", InventorySerial, InventorySerial.status.in_(["IN_STOCK", "RESERVED", "IN_QUARANTINE", "PICKED"]))
    check("inventory", "Conteos abiertos", PhysicalCountSession, PhysicalCountSession.status.notin_(["approved", "cancelled", "completed"]))
    check("inventory", "Preparaciones abiertas", InventoryPickingList, InventoryPickingList.status.notin_(["COMPLETED", "CANCELLED", "completed", "cancelled"]))
    physical_products = db.scalar(select(func.count()).select_from(ProductModel).outerjoin(ProductProfileModel, (ProductProfileModel.product_id == ProductModel.id) & (ProductProfileModel.company_id == company_id)).where(ProductModel.company_id == company_id, ProductModel.is_active.is_(True), or_(ProductProfileModel.id.is_(None), ProductProfileModel.track_inventory.is_(True), ProductProfileModel.is_kit.is_(True)))) or 0
    if physical_products:
        result["inventory"].append({"label": "Productos físicos activos", "count": physical_products})
    terminal = ["cancelled", "closed", "completed", "accepted", "received", "delivered", "returned", "rejected"]
    check("purchases", "Documentos de compras abiertos", SupplyDocument, SupplyDocument.kind.in_(["PURCHASE_ORDER", "GOODS_RECEIPT", "PURCHASE_RETURN", "PURCHASE_REQUISITION", "PURCHASE_AGREEMENT"]), SupplyDocument.status.notin_(terminal))
    check("purchases", "Reclamos de proveedor sin resolver", SupplierClaimModel, SupplierClaimModel.status.notin_(["closed", "cancelled", "rejected"]))
    check("inventory", "Traslados abiertos", SupplyDocument, SupplyDocument.kind == "TRANSFER", SupplyDocument.status.notin_(terminal))
    check("delivery", "Entregas abiertas", SupplyDocument, SupplyDocument.kind == "DELIVERY", SupplyDocument.status.notin_(terminal))
    check("delivery", "Recorridos abiertos", DeliveryRouteModel, DeliveryRouteModel.status.notin_(["completed", "cancelled"]))
    check("delivery", "Citas pendientes", DeliveryWindowReservationModel, DeliveryWindowReservationModel.status.in_(["booked", "checked_in"]))
    check("quotations", "Cotizaciones abiertas", QuotationModel, QuotationModel.status.notin_(["converted", "superseded", "rejected", "expired", "cancelled"]))
    check("orders", "Pedidos abiertos", OrderModel, OrderModel.status.notin_(["fulfilled", "cancelled", "completed", "closed"]))
    check("commissions", "Liquidaciones pendientes", CommissionSettlementModel, CommissionSettlementModel.status.notin_(["paid", "cancelled"]))
    check("credit", "Deudas o borradores a crédito", SaleModel, or_(SaleModel.is_credit.is_(True) & (SaleModel.status == "draft"), SaleModel.status.in_(["confirmed", "paid"]) & (SaleModel.total_amount > SaleModel.paid_amount)))
    check("cash", "Cajas abiertas", CashSessionModel, CashSessionModel.status == "open")
    check("cash", "Fondos con saldo", CashCustodyAccountModel, CashCustodyAccountModel.balance != 0)
    check("cash", "Traspasos pendientes", CashCustodyTransferModel, CashCustodyTransferModel.status.in_(["sent", "disputed", "return_pending"]))
    check("cash", "Anticipos por rendir", PettyCashAdvanceModel, PettyCashAdvanceModel.status.notin_(["closed", "cancelled", "rejected"]))
    check("warranties", "Garantías en trámite", ProductWarrantyClaimModel, ProductWarrantyClaimModel.status.notin_(["closed", "cancelled", "rejected", "delivered"]))
    check("expenses", "Gastos en trámite", ExpenseModel, ExpenseModel.status.notin_(["paid", "cancelled", "rejected"]))
    check("payables", "Obligaciones con saldo o en revisión", PayableModel, PayableModel.status.notin_(["paid", "cancelled"]))
    return result


def preview(db, company_id, payload):
    existing = current(db, company_id)
    if existing["version"] != payload.expected_version:
        raise HTTPException(409, "El perfil operativo cambió. Consulte la configuración vigente.")
    enabled = sorted(payload.enabled)
    if len(set(enabled)) != len(enabled) or set(enabled) - set(AREAS):
        raise HTTPException(422, "Seleccione áreas conocidas sin repeticiones.")
    if payload.profile != "custom" and set(enabled) != set(PROFILES[payload.profile]["enabled"]):
        raise HTTPException(422, "La selección no corresponde al perfil. Use un perfil personalizado si cambia sus áreas.")
    dependency_errors = [{"area": key, "missing": [required for required in AREAS[key]["requires"] if required not in enabled]} for key in enabled if any(required not in enabled for required in AREAS[key]["requires"])]
    disabled = sorted(set(existing["enabled"]) - set(enabled))
    pending = blockers(db, company_id) if disabled else {}
    active_blockers = {key: pending[key] for key in disabled if pending.get(key)}
    result = {"version": existing["version"], "profile": payload.profile, "enabled": enabled, "disabled": disabled, "activated": sorted(set(enabled) - set(existing["enabled"])), "dependencies": dependency_errors, "blockers": active_blockers, "can_apply": not dependency_errors and not active_blockers, "effects": ["Las áreas desactivadas dejan de ofrecer nuevas operaciones y formularios asociados.", "El historial permanece consultable y conserva los permisos de cada usuario.", "El cambio de perfil no altera stock, cobros ni documentos históricos."]}
    result["preview_hash"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


def save(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "operating_profile.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    result = preview(db, user.company_id, payload)
    if payload.preview_hash != result["preview_hash"]:
        raise HTTPException(409, "Las dependencias o los pendientes cambiaron. Revise el impacto nuevamente.")
    if not result["can_apply"]:
        raise HTTPException(409, {"message": "Resuelva las dependencias y los documentos pendientes antes de desactivar áreas.", "preview": result})
    row = AnalyticsArtifact(company_id=user.company_id, kind="operating_profile", artifact_key="company", version=result["version"] + 1, status="active", created_by=user.user_id, data_json=json.dumps({"profile": payload.profile, "enabled": result["enabled"], "reason": payload.reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()}))
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_OPERATING_PROFILE", entity_type="AnalyticsArtifact", entity_id=row.id, diff={"version": row.version, "reason": payload.reason, "impact": result})
    response = current(db, user.company_id)
    complete_request(record, response)
    db.commit()
    return response


def require_area(db, company_id, area):
    if area not in current(db, company_id)["enabled"]:
        raise HTTPException(409, f"El área {AREAS[area]['label']} está desactivada en el perfil de la empresa. Revise su configuración antes de registrar nuevas operaciones.")


def require_sale_areas(db, sale):
    enabled = current(db, sale.company_id)["enabled"]
    if sale.is_credit and "credit" not in enabled:
        require_area(db, sale.company_id, "credit")
    from salesia.shared.infrastructure.models import SaleLineModel
    from salesia.modules.organizacion.application.periodos import business_date, require_open_period
    if sale.is_credit:
        require_open_period(db, sale.company_id, business_date(db, sale.company_id), ["receivables"])
    physical = db.scalar(select(ProductModel.id).join(SaleLineModel, SaleLineModel.product_id == ProductModel.id).outerjoin(ProductProfileModel, (ProductProfileModel.product_id == ProductModel.id) & (ProductProfileModel.company_id == sale.company_id)).where(ProductModel.company_id == sale.company_id, SaleLineModel.company_id == sale.company_id, SaleLineModel.sale_id == sale.id, or_(ProductProfileModel.id.is_(None), ProductProfileModel.track_inventory.is_(True), ProductProfileModel.is_kit.is_(True))).limit(1))
    if physical:
        require_area(db, sale.company_id, "inventory")
        require_open_period(db, sale.company_id, business_date(db, sale.company_id), ["inventory"])


def require_product_inventory(db, company_id, track_inventory, is_kit=False, is_active=True):
    if is_active and (track_inventory or is_kit):
        require_area(db, company_id, "inventory")


def area_for_path(path):
    path = path.removeprefix("/api/v1")
    if path.startswith(("/supplier-balances", "/supplier-credits")):
        return "payables"
    groups = {"analytics": ("/datasets", "/dataset-", "/statistics", "/probability", "/random-variables", "/insights", "/analytics/models", "/analytics/demand-forecast", "/analytics/time-series"), "purchases": ("/purchase-", "/purchases", "/suppliers", "/supplier-", "/goods-receipts", "/replenishment"), "delivery": ("/deliveries", "/delivery-"), "commissions": ("/sales/commission", "/sales/performance-targets", "/sales/targets"), "credit": ("/receivables",), "cash": ("/cash-sessions", "/cash-custody", "/petty-cash"), "warranties": ("/warranty",), "expenses": ("/expenses", "/expense-", "/budgets"), "payables": ("/payables", "/supplier-credits"), "quotations": ("/quotations",), "orders": ("/orders",), "inventory": ("/inventory", "/stock", "/transfers", "/physical-count", "/warehouse-locations", "/lots", "/serials", "/quarantine", "/picking")}
    return next((area for area, prefixes in groups.items() if any(path.startswith(prefix) for prefix in prefixes)), None)
