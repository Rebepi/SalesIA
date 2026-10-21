import hashlib
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel, CashCustodyTransferModel
from salesia.modules.finanzas.infrastructure.models.caja_chica import PettyCashAdvanceModel, PettyCashFundModel
from salesia.modules.inventario.infrastructure_models import InventoryPickingList, InventoryQuarantine, InventoryReservation, InventorySerial, LocationStock, PhysicalCountSession, SupplyDocument
from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel
from salesia.modules.inventario.infrastructure.models.ventanas_entrega import DeliveryWindowModel, DeliveryWindowReservationModel
from salesia.modules.pedidos.infrastructure.models.documentos import OrderModel, QuotationModel
from salesia.shared.infrastructure.models import BranchModel, CashSessionModel, CompanyModel, InventoryStockModel, SaleModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class RetirementRequest(BaseModel):
    preview_hash: str = Field(min_length=64, max_length=64)
    reason: str = Field(min_length=5, max_length=2000)


def location(db, company_id, kind, identifier, lock=False):
    model = BranchModel if kind == "branch" else WarehouseModel
    query = select(model).where(model.company_id == company_id, model.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Sede o almacén no encontrado en la empresa activa.")
    return row


def preview(db, company_id, kind: Literal["branch", "warehouse"], identifier):
    row = location(db, company_id, kind, identifier)
    warehouse_ids = select(WarehouseModel.id).where(WarehouseModel.company_id == company_id, WarehouseModel.branch_id == identifier) if kind == "branch" else [identifier]
    checks = []

    def check(code, label, model, conditions, guidance):
        count = db.scalar(select(func.count()).select_from(model).where(model.company_id == company_id, *conditions)) or 0
        checks.append({"code": code, "label": label, "count": count, "blocking": count > 0, "guidance": guidance})

    check("stock", "Existencias o reservas de stock", InventoryStockModel, [InventoryStockModel.warehouse_id.in_(warehouse_ids), or_(InventoryStockModel.physical_quantity != 0, InventoryStockModel.reserved_quantity != 0)], "Transfiera o regularice las existencias con su documento y resuelva las reservas antes del retiro.")
    check("locations", "Existencias en ubicaciones internas", LocationStock, [LocationStock.warehouse_id.in_(warehouse_ids), LocationStock.quantity != 0], "Concilie los saldos de ubicaciones con el stock del almacén.")
    check("reservations", "Reservas activas", InventoryReservation, [InventoryReservation.warehouse_id.in_(warehouse_ids), InventoryReservation.status == "ACTIVE", InventoryReservation.reserved_quantity > 0], "Libere o cumpla las reservas desde sus documentos de origen.")
    check("quarantine", "Unidades en cuarentena", InventoryQuarantine, [InventoryQuarantine.warehouse_id.in_(warehouse_ids), InventoryQuarantine.status == "IN_QUARANTINE", InventoryQuarantine.quantity > 0], "Inspeccione y resuelva el destino de la mercadería retenida.")
    check("serials", "Series bajo custodia del almacén", InventorySerial, [InventorySerial.warehouse_id.in_(warehouse_ids), InventorySerial.status.in_(["IN_STOCK", "RESERVED", "IN_QUARANTINE", "PICKED"])], "Concilie las series o transfiera su custodia física antes de retirar el almacén.")
    check("counts", "Conteos físicos abiertos", PhysicalCountSession, [PhysicalCountSession.warehouse_id.in_(warehouse_ids), PhysicalCountSession.status.notin_(["approved", "cancelled", "completed"])], "Concluya o cancele los conteos conservando su resultado.")
    check("picking", "Preparaciones abiertas", InventoryPickingList, [InventoryPickingList.warehouse_id.in_(warehouse_ids), InventoryPickingList.status.notin_(["COMPLETED", "CANCELLED", "completed", "cancelled"])], "Concluya o cancele la preparación y sus reservas.")
    check("documents", "Compras, traslados y entregas abiertos", SupplyDocument, [or_(SupplyDocument.warehouse_id.in_(warehouse_ids), SupplyDocument.source_warehouse_id.in_(warehouse_ids)), SupplyDocument.status.notin_(["cancelled", "closed", "completed", "accepted", "received", "delivered", "returned", "rejected"])], "Resuelva cada documento desde compras o logística. Los traslados en tránsito deben recibirse o revertirse de forma documentada.")
    check("routes", "Recorridos de entrega abiertos", DeliveryRouteModel, [DeliveryRouteModel.warehouse_id.in_(warehouse_ids), DeliveryRouteModel.status.notin_(["completed", "cancelled"])], "Concluya o cancele los recorridos con el resultado de sus paradas.")
    sale_scope = SaleModel.branch_id == identifier if kind == "branch" else SaleModel.warehouse_id == identifier
    check("draft_sales", "Ventas en borrador", SaleModel, [sale_scope, SaleModel.status == "draft"], "Confirme, cancele o cambie el almacén del borrador según corresponda.")
    order_scope = OrderModel.branch_id == identifier if kind == "branch" else OrderModel.warehouse_id == identifier
    check("orders", "Pedidos comerciales abiertos", OrderModel, [order_scope, OrderModel.status.notin_(["completed", "cancelled", "fulfilled", "closed"])], "Cumpla o cancele los pedidos y resuelva sus cantidades pendientes antes de retirar la ubicación.")
    if kind == "branch":
        check("quotations", "Cotizaciones vigentes", QuotationModel, [QuotationModel.branch_id == identifier, QuotationModel.status.notin_(["converted", "cancelled", "rejected", "expired", "superseded"])], "Convierta, cierre o cancele las cotizaciones ligadas a esta sede.")
        check("cash", "Cajas abiertas", CashSessionModel, [CashSessionModel.branch_id == identifier, CashSessionModel.status == "open"], "Realice el arqueo y cierre o relevo de cada caja.")
        check("custody", "Fondos con saldo en custodia", CashCustodyAccountModel, [CashCustodyAccountModel.branch_id == identifier, CashCustodyAccountModel.balance != 0], "Traspase los fondos con recepción del destinatario; respete cada moneda.")
        account_ids = select(CashCustodyAccountModel.id).where(CashCustodyAccountModel.company_id == company_id, CashCustodyAccountModel.branch_id == identifier)
        session_ids = select(CashSessionModel.id).where(CashSessionModel.company_id == company_id, CashSessionModel.branch_id == identifier)
        check("cash_transfers", "Traspasos de efectivo pendientes", CashCustodyTransferModel, [or_(CashCustodyTransferModel.source_account_id.in_(account_ids), CashCustodyTransferModel.destination_account_id.in_(account_ids), CashCustodyTransferModel.source_session_id.in_(session_ids), CashCustodyTransferModel.destination_session_id.in_(session_ids)), CashCustodyTransferModel.status.in_(["sent", "disputed", "return_pending"])], "Confirme la recepción o devolución documentada de cada traspaso.")
        fund_ids = select(PettyCashFundModel.id).where(PettyCashFundModel.company_id == company_id, PettyCashFundModel.account_id.in_(account_ids))
        check("advances", "Anticipos de caja chica pendientes", PettyCashAdvanceModel, [PettyCashAdvanceModel.fund_id.in_(fund_ids), PettyCashAdvanceModel.status.notin_(["closed", "cancelled", "rejected"])], "Rinda o cancele los anticipos y complete las diferencias reconocidas.")
        window_ids = select(DeliveryWindowModel.id).where(DeliveryWindowModel.company_id == company_id, DeliveryWindowModel.branch_id == identifier)
        check("appointments", "Reservas de atención pendientes", DeliveryWindowReservationModel, [DeliveryWindowReservationModel.window_id.in_(window_ids), DeliveryWindowReservationModel.status.in_(["booked", "checked_in"])], "Atienda, reprograme o cancele las reservas antes de retirar la sede.")
    children = db.scalars(select(WarehouseModel).where(WarehouseModel.company_id == company_id, WarehouseModel.branch_id == identifier, WarehouseModel.is_active.is_(True)).order_by(WarehouseModel.code)).all() if kind == "branch" else []
    data = {"kind": kind, "id": str(identifier), "name": row.name, "code": row.code, "is_active": row.is_active, "updated_at": row.updated_at.isoformat(), "checks": checks, "can_retire": not any(item["blocking"] for item in checks), "warehouses_to_retire": [{"id": str(item.id), "code": item.code, "name": item.name, "updated_at": item.updated_at.isoformat()} for item in children], "effects": ["Se impide seleccionar esta ubicación para nuevas operaciones.", "Los documentos históricos conservan su sede y almacén."] + (["También se desactivan sus almacenes activos, cuentas de custodia, fondos y franjas de atención sin pendientes."] if kind == "branch" else [])}
    parent = db.scalar(select(BranchModel).where(BranchModel.company_id == company_id, BranchModel.id == row.branch_id)) if kind == "warehouse" else None
    data["can_reactivate"] = kind == "branch" or bool(parent and parent.is_active)
    data["preview_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return data


def assert_can_retire(db, company_id, kind, identifier):
    result = preview(db, company_id, kind, identifier)
    if not result["can_retire"]:
        raise HTTPException(409, {"message": "Resuelva los pendientes antes de retirar la ubicación.", "retirement": result})
    return result


def apply_retirement(db, user, kind, row, reason):
    result = assert_can_retire(db, user.company_id, kind, row.id)
    row.is_active = False
    if kind == "branch":
        for warehouse in db.scalars(select(WarehouseModel).where(WarehouseModel.company_id == user.company_id, WarehouseModel.branch_id == row.id)).all():
            warehouse.is_active = False
        accounts = db.scalars(select(CashCustodyAccountModel).where(CashCustodyAccountModel.company_id == user.company_id, CashCustodyAccountModel.branch_id == row.id)).all()
        for account in accounts:
            if account.is_active:
                account.is_active = False
                account.version += 1
        account_ids = [account.id for account in accounts]
        for fund in db.scalars(select(PettyCashFundModel).where(PettyCashFundModel.company_id == user.company_id, PettyCashFundModel.account_id.in_(account_ids), PettyCashFundModel.is_active.is_(True))).all():
            fund.is_active = False
            fund.version += 1
        for window in db.scalars(select(DeliveryWindowModel).where(DeliveryWindowModel.company_id == user.company_id, DeliveryWindowModel.branch_id == row.id, DeliveryWindowModel.is_active.is_(True))).all():
            window.is_active = False
            window.version += 1
            history = json.loads(window.history_json)
            history.append({"action": "RETIRE_BRANCH", "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "version": window.version, "reason": reason})
            window.history_json = json.dumps(history)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="RETIRE_LOCATION", entity_type="Branch" if kind == "branch" else "Warehouse", entity_id=row.id, diff={"reason": reason, "preview": result})
    return result


def retire(db, user, kind, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"location.retire:{kind}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = location(db, user.company_id, kind, identifier, True)
    result = preview(db, user.company_id, kind, identifier)
    if result["preview_hash"] != payload.preview_hash:
        raise HTTPException(409, "La ubicación o sus pendientes cambiaron. Actualice la revisión de retiro.")
    if not row.is_active:
        raise HTTPException(409, "La ubicación ya está inactiva.")
    result = apply_retirement(db, user, kind, row, payload.reason)
    db.flush()
    response = {"id": str(row.id), "kind": kind, "is_active": False, "retired_warehouses": result["warehouses_to_retire"], "reason": payload.reason}
    complete_request(record, response)
    db.commit()
    return response


def reactivate(db, user, kind, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"location.reactivate:{kind}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = location(db, user.company_id, kind, identifier, True)
    result = preview(db, user.company_id, kind, identifier)
    if result["preview_hash"] != payload.preview_hash:
        raise HTTPException(409, "La ubicación cambió. Actualice la revisión antes de reactivarla.")
    if row.is_active or not result["can_reactivate"]:
        raise HTTPException(409, "La ubicación ya está activa o su sede continúa inactiva.")
    row.is_active = True
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REACTIVATE_LOCATION", entity_type="Branch" if kind == "branch" else "Warehouse", entity_id=row.id, diff={"reason": payload.reason, "preview_hash": payload.preview_hash})
    db.flush()
    response = {"id": str(row.id), "kind": kind, "is_active": True, "reason": payload.reason}
    complete_request(record, response)
    db.commit()
    return response
