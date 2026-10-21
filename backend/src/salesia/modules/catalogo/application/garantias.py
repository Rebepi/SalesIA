import calendar
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.application.contracts.garantias import WarrantyClaimCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel, ProductWarrantyClaimModel
from salesia.modules.finanzas.application.auxiliares.get_sale_eligible_lines import _get_sale_eligible_lines
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import CustomerModel, ProductModel, SaleLineModel, SaleModel, UserModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def add_months(value, months):
    ordinal = value.year * 12 + value.month - 1 + months
    year, month = divmod(ordinal, 12)
    return value.replace(year=year, month=month + 1, day=min(value.day, calendar.monthrange(year, month + 1)[1]))


def coverage(db, sale, line):
    profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == sale.company_id, ProductProfileModel.product_id == line.product_id))
    historical = line.warranty_months_snapshot is not None
    months = line.warranty_months_snapshot if historical else profile.warranty_period_months if profile else 0
    policy = line.warranty_policy_snapshot if historical else profile.warranty_policy if profile else None
    purchased_at = aware(line.delivered_at or sale.confirmed_at or sale.created_at)
    return months, policy, add_months(purchased_at, months), "sale_snapshot" if historical else "legacy_current_policy"


def serialize_claim(db, row):
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == row.company_id, SaleModel.id == row.sale_id))
    product = db.scalar(select(ProductModel).where(ProductModel.company_id == row.company_id, ProductModel.id == row.product_id))
    assigned = db.scalar(select(UserModel).where(UserModel.company_id == row.company_id, UserModel.id == row.assigned_to)) if row.assigned_to else None
    return {"id": str(row.id), "sale_id": str(row.sale_id), "sale_line_id": str(row.sale_line_id) if row.sale_line_id else None, "receipt": f"{sale.series}-{sale.number:08d}" if sale else "Venta original", "product_id": str(row.product_id), "product_name": product.name if product else "Producto", "serial_number": row.serial_number, "quantity": str(row.quantity), "claim_date": row.claim_date.isoformat(), "warranty_period_months_snapshot": row.warranty_period_months_snapshot, "warranty_until": row.warranty_until.isoformat() if row.warranty_until else None, "policy_snapshot": row.policy_snapshot, "issue_description": row.issue_description, "status": row.status, "version": row.version, "assigned_to": str(row.assigned_to) if row.assigned_to else None, "assigned_name": assigned.email if assigned else None, "diagnosis": row.diagnosis, "resolution": row.resolution, "history": json.loads(row.history_json or "[]")}


def create_warranty_claim(req: WarrantyClaimCreateModel, current_user: AuthenticatedUser, db: Session, idempotency_key=None):
    record, cached = claim_request(db, current_user.company_id, "warranty.create", idempotency_key, req.model_dump(mode="json"))
    if cached is not None:
        return cached
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.id == req.sale_id).with_for_update())
    if not sale:
        raise DomainNotFoundException("Venta original no encontrada.")
    if sale.status not in ("confirmed", "paid"):
        raise HTTPException(409, "La garantía requiere una venta confirmada y no anulada.")
    statement = select(SaleLineModel).where(SaleLineModel.company_id == current_user.company_id, SaleLineModel.sale_id == sale.id, SaleLineModel.product_id == req.product_id)
    if req.sale_line_id:
        statement = statement.where(SaleLineModel.id == req.sale_line_id)
    lines = db.scalars(statement).all()
    if len(lines) != 1:
        raise HTTPException(422, "Selecciona una línea de venta concreta del producto.")
    line = lines[0]
    months, policy, until, source = coverage(db, sale, line)
    if months <= 0 or until < datetime.now(timezone.utc):
        raise HTTPException(409, "El producto no tiene una garantía vigente según la política registrada.")
    _, eligible_lines = _get_sale_eligible_lines(db, sale.id, current_user.company_id)
    eligible = next(item for item in eligible_lines if item["sale_line_id"] == line.id)
    if req.quantity > eligible["eligible_quantity"]:
        raise HTTPException(422, "La cantidad supera las unidades entregadas que no están comprometidas en devoluciones.")
    sold_serials = eligible["serial_numbers"]
    if sold_serials and (req.serial_number not in sold_serials or req.quantity != 1):
        raise HTTPException(422, "Selecciona una serie vendida en esa línea y una unidad por expediente.")
    if req.serial_number and not sold_serials:
        raise HTTPException(422, "La venta no registra esa serie como unidad vendida.")
    active_query = select(ProductWarrantyClaimModel).where(ProductWarrantyClaimModel.company_id == current_user.company_id, ProductWarrantyClaimModel.sale_id == sale.id, ProductWarrantyClaimModel.product_id == line.product_id, or_(ProductWarrantyClaimModel.sale_line_id == line.id, ProductWarrantyClaimModel.sale_line_id.is_(None)), ProductWarrantyClaimModel.status.notin_(("delivered", "cancelled", "rejected")))
    active_claims = db.scalars(active_query).all()
    if req.serial_number and any(item.serial_number == req.serial_number for item in active_claims):
        raise HTTPException(409, "La serie ya tiene un expediente de garantía abierto.")
    if sum((item.quantity for item in active_claims), Decimal("0")) + req.quantity > eligible["eligible_quantity"]:
        raise HTTPException(409, "Las unidades de esta línea ya se devolvieron o tienen garantías abiertas.")
    current = datetime.now(timezone.utc)
    history = [{"action": "CREATE", "status": "open", "actor": current_user.email, "at": current.isoformat(), "notes": req.issue_description, "coverage_source": source}]
    claim = ProductWarrantyClaimModel(id=uuid4(), company_id=current_user.company_id, sale_id=sale.id, sale_line_id=line.id, product_id=line.product_id, serial_number=req.serial_number, quantity=req.quantity, claim_date=current, warranty_period_months_snapshot=months, warranty_until=until, policy_snapshot=policy, issue_description=req.issue_description, status="open", version=1, history_json=json.dumps(history))
    db.add(claim)
    db.flush()
    result = serialize_claim(db, claim)
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="CREATE_WARRANTY_CLAIM", entity_type="ProductWarrantyClaim", entity_id=claim.id, diff={"sale_id": str(sale.id), "quantity": str(req.quantity), "coverage_source": source})
    complete_request(record, result)
    db.commit()
    return result


def eligible_warranty_sales(product_id: UUID, search: Optional[str], current_user: AuthenticatedUser, db: Session):
    product = db.scalar(select(ProductModel).where(ProductModel.id == product_id, ProductModel.company_id == current_user.company_id))
    if not product:
        raise DomainNotFoundException("Producto no encontrado.")
    statement = select(SaleModel, CustomerModel, SaleLineModel).join(SaleLineModel, SaleLineModel.sale_id == SaleModel.id).join(CustomerModel, CustomerModel.id == SaleModel.customer_id).where(SaleModel.company_id == current_user.company_id, SaleLineModel.company_id == current_user.company_id, SaleLineModel.product_id == product_id, SaleModel.status.in_(("confirmed", "paid")))
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(CustomerModel.legal_name.ilike(pattern), CustomerModel.doc_number.ilike(pattern), SaleModel.series.ilike(pattern)))
    rows = db.execute(statement.order_by(SaleModel.created_at.desc()).limit(500)).all()
    items = []
    for sale, customer, line in rows:
        months, policy, until, source = coverage(db, sale, line)
        if months <= 0 or until < datetime.now(timezone.utc):
            continue
        _, eligible_lines = _get_sale_eligible_lines(db, sale.id, current_user.company_id)
        eligible = next(item for item in eligible_lines if item["sale_line_id"] == line.id)
        active = db.scalar(select(func.coalesce(func.sum(ProductWarrantyClaimModel.quantity), 0)).where(ProductWarrantyClaimModel.company_id == current_user.company_id, ProductWarrantyClaimModel.sale_id == sale.id, or_(ProductWarrantyClaimModel.sale_line_id == line.id, ProductWarrantyClaimModel.sale_line_id.is_(None)), ProductWarrantyClaimModel.product_id == line.product_id, ProductWarrantyClaimModel.status.notin_(("delivered", "cancelled", "rejected")))) or Decimal("0")
        available = max(Decimal("0"), eligible["eligible_quantity"] - active)
        if available <= 0:
            continue
        items.append({"id": str(sale.id), "sale_id": str(sale.id), "sale_line_id": str(line.id), "receipt": f"{sale.series}-{sale.number:08d}", "customer_name": customer.legal_name, "purchased_at": (line.delivered_at or sale.confirmed_at or sale.created_at).isoformat(), "quantity": str(available), "warranty_until": until.isoformat(), "coverage_source": source, "serial_numbers": eligible["serial_numbers"]})
        if len(items) >= 50:
            break
    return {"items": items, "total_count": len(items)}


def list_claims(db, user, status=None, product_id=None, limit=50, offset=0):
    statement = select(ProductWarrantyClaimModel).where(ProductWarrantyClaimModel.company_id == user.company_id)
    if status:
        statement = statement.where(ProductWarrantyClaimModel.status == status)
    if product_id:
        statement = statement.where(ProductWarrantyClaimModel.product_id == product_id)
    count = db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = db.scalars(statement.order_by(ProductWarrantyClaimModel.claim_date.desc(), ProductWarrantyClaimModel.id).limit(limit).offset(offset)).all()
    return {"items": [serialize_claim(db, row) for row in rows], "total_count": count}


def update_claim(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"warranty.action:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = db.scalar(select(ProductWarrantyClaimModel).where(ProductWarrantyClaimModel.company_id == user.company_id, ProductWarrantyClaimModel.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Expediente no encontrado.")
    if row.version != payload.version:
        raise HTTPException(409, "El expediente cambió; recarga antes de continuar.")
    if row.status in ("delivered", "cancelled", "rejected"):
        raise HTTPException(409, "El expediente está cerrado.")
    transitions = {"diagnose": ({"open"}, "diagnosis"), "await_parts": ({"diagnosis", "repairing"}, "awaiting_parts"), "repair": ({"diagnosis", "awaiting_parts"}, "repairing"), "ready": ({"diagnosis", "repairing"}, "ready"), "deliver": ({"ready"}, "delivered"), "reject": ({"open", "diagnosis"}, "rejected"), "cancel": ({"open", "diagnosis", "awaiting_parts"}, "cancelled")}
    before = row.status
    if payload.action == "assign":
        if payload.assigned_to is None:
            raise HTTPException(422, "Selecciona un responsable activo.")
        target = db.scalar(select(UserModel).where(UserModel.id == payload.assigned_to, UserModel.company_id == user.company_id, UserModel.is_active.is_(True)))
        if target is None:
            raise HTTPException(422, "El responsable no está activo en esta empresa.")
        row.assigned_to = target.id
    else:
        allowed, status = transitions[payload.action]
        if row.status not in allowed:
            raise HTTPException(409, "La acción no corresponde al estado actual de la garantía.")
        row.status = status
    if payload.action == "diagnose":
        row.diagnosis = payload.notes
    if payload.action in ("ready", "reject", "deliver", "cancel"):
        row.resolution = payload.notes
    row.version += 1
    history = json.loads(row.history_json or "[]")
    history.append({"action": payload.action.upper(), "before": before, "status": row.status, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "notes": payload.notes, "assigned_to": str(row.assigned_to) if row.assigned_to else None})
    row.history_json = json.dumps(history)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="UPDATE_WARRANTY_CLAIM", entity_type="ProductWarrantyClaim", entity_id=row.id, diff=history[-1])
    result = serialize_claim(db, row)
    complete_request(record, result)
    db.commit()
    return result
