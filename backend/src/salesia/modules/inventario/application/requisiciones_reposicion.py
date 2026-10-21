import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.application.contracts.requisiciones_reposicion import PurchaseRequisitionCreateRequest
from salesia.modules.inventario.infrastructure_models import StockRule, Supplier, SupplyDocument
from salesia.modules.inventario.service import create_document, document, product, response, transition
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.organizacion.application.politicas import effective_policy
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, SaleLineModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_purchase_requisition(
    payload: PurchaseRequisitionCreateRequest,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: Optional[str],
):
    record = None

    if idempotency_key:
        record, cached = claim_request(
            db, current_user.company_id, "purchase_requisition.create", idempotency_key, payload.model_dump(mode="json")
        )

        if cached is not None:
            return cached

    if payload.suggested_supplier_id and not db.scalar(
        select(Supplier.id).where(
            Supplier.id == payload.suggested_supplier_id,
            Supplier.company_id == current_user.company_id,
            Supplier.is_active.is_(True),
        )
    ):
        raise HTTPException(422, "El proveedor sugerido no existe o está inactivo.")

    details = {
        "priority": payload.priority,
        "justification": payload.justification,
        "suggested_supplier_id": str(payload.suggested_supplier_id) if payload.suggested_supplier_id else None,
    }

    doc = create_document(
        db,
        current_user,
        "PURCHASE_REQUISITION",
        "pending_approval",
        payload.warehouse_id,
        payload.items,
        details_json=json.dumps(details),
    )

    result = response(doc)

    if record is not None:
        complete_request(record, result)

    db.commit()

    return result


def list_purchase_requisitions(current_user: AuthenticatedUser, db: Session):
    docs = db.scalars(
        select(SupplyDocument)
        .where(SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "PURCHASE_REQUISITION")
        .order_by(SupplyDocument.created_at.desc())
    ).all()

    return {"items": [response(d) for d in docs], "count": len(docs)}


def approve_purchase_requisition(id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "PURCHASE_REQUISITION", id)

    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, current_user, "purchase_requisition", [row.created_by], "SupplyDocument", row.id)
    transition(db, row, {"pending_approval"}, "approved")

    db.commit()

    return response(row)


def suggest_requisition_from_stock(warehouse_id: UUID, current_user: AuthenticatedUser, db: Session):
    result = get_replenishment_suggestions(warehouse_id, current_user, db)
    suggestions = []
    for item in result["suggestions"]:
        if Decimal(item["suggested_quantity"]) <= 0:
            continue
        suggestions.append({**item, "reorder_point": item["assumptions"]["reorder_point"], "min_quantity": item["assumptions"]["safety_stock"]})
    return {"suggestions": suggestions, "auto_submitted": False}


def get_replenishment_suggestions(warehouse_id: Optional[UUID], current_user: AuthenticatedUser, db: Session):
    from collections import defaultdict
    from salesia.modules.inventario.application.catalogo_proveedor import current_condition, rounded_purchase_quantity
    from salesia.modules.inventario.infrastructure.models.catalogo_proveedor import SupplierProductModel
    from salesia.modules.organizacion.application.periodos import business_date
    from salesia.shared.infrastructure.models import CompanyModel, WarehouseModel
    if warehouse_id and not db.scalar(select(WarehouseModel.id).where(WarehouseModel.company_id == current_user.company_id, WarehouseModel.id == warehouse_id, WarehouseModel.is_active.is_(True))):
        raise HTTPException(422, "Selecciona un almacén activo de la empresa.")
    company = db.get(CompanyModel, current_user.company_id)
    today = business_date(db, current_user.company_id)
    policy = effective_policy(db, current_user.company_id, "replenishment_policy")
    history_days = int(policy.get("history_days", 30))
    from salesia.modules.inventario.application.homologacion_proveedor import supplier_qualified
    suppliers = {row.id: row for row in db.scalars(select(Supplier).where(Supplier.company_id == current_user.company_id, Supplier.is_active.is_(True))).all() if supplier_qualified(row, today)}
    catalog = defaultdict(list)
    for condition in db.scalars(select(SupplierProductModel).where(SupplierProductModel.company_id == current_user.company_id, SupplierProductModel.is_active.is_(True))).all():
        if condition.supplier_id in suppliers and current_condition(condition, today):
            catalog[condition.product_id].append(condition)
    incoming, commitments = defaultdict(lambda: Decimal("0")), defaultdict(list)
    order_query = select(SupplyDocument).where(SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "PURCHASE_ORDER", SupplyDocument.status.in_(("approved", "partially_received")))
    if warehouse_id:
        order_query = order_query.where(SupplyDocument.warehouse_id == warehouse_id)
    for order in db.scalars(order_query).all():
        details = json.loads(order.details_json or "{}")
        due = details.get("delivery_date")
        for line in order.lines:
            pending = max(Decimal("0"), line.quantity - line.processed_quantity - line.cancelled_quantity)
            if pending > 0:
                incoming[line.product_id] += pending
                commitments[line.product_id].append({"order_id": str(order.id), "warehouse_id": str(order.warehouse_id), "quantity": str(pending), "delivery_date": due, "overdue": bool(due and due[:10] < today.isoformat())})
    in_transit, transfer_commitments = defaultdict(lambda: Decimal("0")), defaultdict(list)
    transfers_query = select(SupplyDocument).where(SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "TRANSFER", SupplyDocument.status.in_(("in_transit", "partially_received")))
    if warehouse_id:
        transfers_query = transfers_query.where(SupplyDocument.warehouse_id == warehouse_id)
    for transfer in db.scalars(transfers_query).all():
        for line in transfer.lines:
            pending = max(Decimal("0"), line.quantity - line.processed_quantity - line.damaged_quantity)
            if pending > 0:
                in_transit[line.product_id] += pending
                transfer_commitments[line.product_id].append({"transfer_id": str(transfer.id), "warehouse_id": str(transfer.warehouse_id), "quantity": str(pending)})
    results = []
    for product_row in db.scalars(select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.is_active.is_(True))).all():
        profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == product_row.id))
        if profile and (profile.product_type == "service" or not profile.track_inventory or profile.is_kit or profile.status in ("archived", "suspended", "discontinued")):
            continue
        conditions = sorted(catalog[product_row.id], key=lambda row: (not row.is_preferred, row.currency != company.base_currency, row.supplier_id != (profile.supplier_id if profile else None), row.lead_time_days, str(row.id)))
        condition = conditions[0] if conditions else None
        supplier_id = condition.supplier_id if condition else profile.supplier_id if profile and profile.supplier_id in suppliers else None
        rule_query = select(StockRule).where(StockRule.company_id == current_user.company_id, StockRule.product_id == product_row.id, StockRule.is_active.is_(True))
        if warehouse_id:
            rule_query = rule_query.where(StockRule.warehouse_id == warehouse_id)
        rules = db.scalars(rule_query).all()
        sold = db.scalar(select(func.coalesce(func.sum(SaleLineModel.quantity), 0)).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(SaleModel.company_id == current_user.company_id, SaleLineModel.product_id == product_row.id, SaleModel.status.in_(("confirmed", "paid", "refunded")), func.coalesce(SaleModel.confirmed_at, SaleModel.created_at) >= datetime.now(timezone.utc) - timedelta(days=history_days), *([SaleModel.warehouse_id == warehouse_id] if warehouse_id else []))) or Decimal("0")
        from salesia.modules.finanzas.infrastructure_models import ReturnLineModel, ReturnModel
        returned = db.scalar(select(func.coalesce(func.sum(ReturnLineModel.quantity), 0)).join(ReturnModel, ReturnModel.id == ReturnLineModel.return_id).join(SaleModel, SaleModel.id == ReturnModel.sale_id).where(ReturnModel.company_id == current_user.company_id, ReturnModel.status == "accepted", ReturnLineModel.product_id == product_row.id, SaleModel.company_id == current_user.company_id, func.coalesce(SaleModel.confirmed_at, SaleModel.created_at) >= datetime.now(timezone.utc) - timedelta(days=history_days), *([SaleModel.warehouse_id == warehouse_id] if warehouse_id else []))) or Decimal("0")
        sold = max(Decimal("0"), sold - returned)
        daily_demand = (sold / Decimal(history_days)).quantize(Decimal("0.000001"))
        sufficient = bool(rules and sold > 0)
        lead_days = condition.lead_time_days if condition else int(policy.get("default_lead_time_days", 7))
        safety = sum((rule.min_quantity for rule in rules), Decimal("0"))
        reorder = sum((rule.reorder_point for rule in rules), Decimal("0"))
        available = db.scalar(select(func.coalesce(func.sum(InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity), 0)).where(InventoryStockModel.company_id == current_user.company_id, InventoryStockModel.product_id == product_row.id, *([InventoryStockModel.warehouse_id == warehouse_id] if warehouse_id else []))) or Decimal("0")
        pending = incoming[product_row.id]
        transit = in_transit[product_row.id]
        position = available + pending + transit
        target = max(reorder, daily_demand * Decimal(lead_days) + safety)
        if sufficient:
            needed = max(Decimal("0"), target - position)
        elif rules and position <= max(reorder, safety):
            fixed = sum((rule.reorder_quantity for rule in rules), Decimal("0"))
            target = sum((rule.max_quantity for rule in rules), Decimal("0"))
            needed = max(Decimal("0"), fixed - pending - transit) if fixed > 0 else max(Decimal("0"), target - position)
        else:
            needed = Decimal("0")
        warnings = []
        if any(item["overdue"] for item in commitments[product_row.id]):
            warnings.append("Hay compras atrasadas; revisa su entrega antes de generar otra orden.")
        if any(not item["delivery_date"] for item in commitments[product_row.id]):
            warnings.append("Hay compras pendientes sin fecha de entrega confirmada.")
        if not condition:
            warnings.append("Se usa el plazo general; no existen condiciones vigentes del proveedor para el producto.")
        suggested = rounded_purchase_quantity(needed, condition)
        from salesia.modules.catalogo.service import validate_unit_fraction
        from salesia.shared.infrastructure.errors import DomainConflictException
        from decimal import ROUND_CEILING
        try:
            validate_unit_fraction(db, current_user.company_id, product_row.unit_of_measure, suggested)
        except DomainConflictException:
            suggested = suggested.to_integral_value(rounding=ROUND_CEILING)
        results.append({"product_id": str(product_row.id), "product_name": product_row.name, "sku": product_row.sku, "unit_cost": str(condition.unit_cost if condition else product_row.unit_cost), "currency": condition.currency if condition else suppliers[supplier_id].currency if supplier_id else company.base_currency, "warehouse_id": str(warehouse_id) if warehouse_id else None, "suggested_supplier_id": str(supplier_id) if supplier_id else None, "supplier_condition_id": str(condition.id) if condition else None, "current_available": str(available), "pending_purchase_quantity": str(pending), "in_transit_quantity": str(transit), "transfer_commitments": transfer_commitments[product_row.id], "inventory_position": str(position), "purchase_commitments": commitments[product_row.id], "warnings": warnings, "assumptions": {"daily_demand": str(daily_demand), "history_days": history_days, "lead_time_days": lead_days, "lead_time_source": "supplier_product" if condition else "company_default", "safety_stock": str(safety), "reorder_point": str(reorder), "minimum_quantity": str(condition.minimum_quantity) if condition else "0", "order_multiple": str(condition.order_multiple) if condition else "0"}, "suggested_quantity": str(suggested), "data_insufficient": not sufficient, "status": "NEEDS_REVIEW" if warnings and pending > 0 else "READY" if sufficient else "NEEDS_DATA", "can_auto_approve": False})
    return {"suggestions": results}
