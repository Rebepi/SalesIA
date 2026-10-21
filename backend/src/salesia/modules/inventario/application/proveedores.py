import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.proveedores import SupplierCreateRequest, SupplierUpdateRequest
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument, SupplyLine
from salesia.modules.inventario.service import product
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def list_suppliers(
    search: Optional[str],
    is_active: Optional[bool],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(Supplier).where(Supplier.company_id == current_user.company_id)

    if search:
        query = query.where(Supplier.legal_name.ilike(f"%{search}%") | Supplier.tax_id.ilike(f"%{search}%"))

    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    rows = db.scalars(query.order_by(Supplier.legal_name).offset(offset).limit(limit)).all()

    can_view_finance = (
        "purchases:read" in current_user.permissions
        or "finance:read" in current_user.permissions
        or current_user.role in ("company_admin", "platform_admin")
    )

    items = [
        {
            "id": str(r.id),
            "tax_id": r.tax_id,
            "legal_name": r.legal_name,
            "contact_name": r.contact_name,
            "email": r.email,
            "phone": r.phone,
            "payment_terms_days": r.payment_terms_days,
            "currency": r.currency,
            "bank_name": r.bank_name if can_view_finance else None,
            "bank_account": r.bank_account if can_view_finance else None,
            "notes": r.notes,
            "is_active": r.is_active,
            "qualification_status": r.qualification_status,
            "qualification_until": r.qualification_until.isoformat() if r.qualification_until else None,
            "version": r.version,
        }
        for r in rows
    ]

    return {"items": items, "count": len(items)}


def create_supplier(payload: SupplierCreateRequest, current_user: AuthenticatedUser, db: Session):
    if db.scalar(
        select(Supplier.id).where(Supplier.company_id == current_user.company_id, Supplier.tax_id == payload.tax_id)
    ):
        raise HTTPException(409, "El proveedor ya existe.")

    row = Supplier(
        company_id=current_user.company_id,
        tax_id=payload.tax_id,
        legal_name=payload.legal_name,
        contact_name=payload.contact_name,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        payment_terms_days=payload.payment_terms_days,
        currency=payload.currency,
        bank_name=payload.bank_name,
        bank_account=payload.bank_account,
        notes=payload.notes,
        is_active=True,
        qualification_status="pending_evaluation",
    )

    db.add(row)

    db.commit()

    return {"id": str(row.id), **payload.model_dump(mode="json"), "is_active": row.is_active, "qualification_status": row.qualification_status, "version": row.version}


def get_supplier(supplier_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.company_id == current_user.company_id))

    if not row:
        raise HTTPException(404, "Proveedor no encontrado.")

    can_view_finance = (
        "purchases:read" in current_user.permissions
        or "finance:read" in current_user.permissions
        or current_user.role in ("company_admin", "platform_admin")
    )

    return {
        "id": str(row.id),
        "tax_id": row.tax_id,
        "legal_name": row.legal_name,
        "contact_name": row.contact_name,
        "email": row.email,
        "phone": row.phone,
        "payment_terms_days": row.payment_terms_days,
        "currency": row.currency,
        "bank_name": row.bank_name if can_view_finance else None,
        "bank_account": row.bank_account if can_view_finance else None,
        "notes": row.notes,
        "is_active": row.is_active,
        "qualification_status": row.qualification_status,
        "qualification_until": row.qualification_until.isoformat() if row.qualification_until else None,
        "version": row.version,
    }


def update_supplier(supplier_id: UUID, payload: SupplierUpdateRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.company_id == current_user.company_id).with_for_update())

    if not row:
        raise HTTPException(404, "Proveedor no encontrado.")

    data = payload.model_dump(exclude_unset=True, exclude={"version", "change_reason"})
    sensitive = bool(set(data) & {"bank_name", "bank_account", "currency", "payment_terms_days"})
    if sensitive and not ({"payments:write", "organization:manage"} & set(current_user.permissions)):
        raise HTTPException(403, "Modificar referencias financieras del proveedor requiere autorización de finanzas o administración.")
    if (payload.version is not None and payload.version != row.version) or (sensitive and payload.version is None):
        raise HTTPException(409, "Recarga la ficha y envía su versión vigente para modificar datos financieros.")
    if sensitive and not payload.change_reason:
        raise HTTPException(422, "Documenta el motivo del cambio de datos financieros.")
    before = {field: getattr(row, field) for field in data}

    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])

    for k, v in data.items():
        setattr(row, k, v)

    row.version += 1
    from salesia.modules.auditoria.service import record_audit_event
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="UPDATE_SUPPLIER", entity_type="Supplier", entity_id=row.id, diff={"before": before, "after": data, "version": row.version, "reason": payload.change_reason, "sensitive_change": sensitive})
    db.commit()

    return {
        "id": str(row.id),
        "tax_id": row.tax_id,
        "legal_name": row.legal_name,
        "contact_name": row.contact_name,
        "email": row.email,
        "phone": row.phone,
        "payment_terms_days": row.payment_terms_days,
        "currency": row.currency,
        "bank_name": row.bank_name,
        "bank_account": row.bank_account,
        "notes": row.notes,
        "is_active": row.is_active,
        "qualification_status": row.qualification_status,
        "qualification_until": row.qualification_until.isoformat() if row.qualification_until else None,
        "version": row.version,
    }


def get_supplier_performance(supplier_id: UUID, current_user: AuthenticatedUser, db: Session):
    from salesia.modules.inventario.application.desempeno_proveedor import supplier_performance
    return supplier_performance(db, current_user, supplier_id)


def supplier_price_history(supplier_id: UUID, product_id: UUID, current_user: AuthenticatedUser, db: Session):
    supplier = db.scalar(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.company_id == current_user.company_id)
    )

    if not supplier:
        raise HTTPException(404, "Proveedor no encontrado.")

    product(db, current_user.company_id, product_id)

    rows = db.execute(
        select(SupplyDocument, SupplyLine)
        .join(SupplyLine, SupplyLine.document_id == SupplyDocument.id)
        .where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.kind == "PURCHASE_ORDER",
            SupplyDocument.supplier_id == supplier_id,
            SupplyDocument.status.in_(("approved", "partially_received", "received")),
            SupplyLine.product_id == product_id,
        )
        .order_by(SupplyDocument.created_at.desc())
        .limit(10)
    ).all()

    return {
        "items": [
            {
                "order_id": str(order.id),
                "created_at": order.created_at.isoformat(),
                "currency": json.loads(order.details_json or "{}").get("currency"),
                "unit_cost": str(line.unit_cost),
                "quantity": str(line.quantity),
            }
            for order, line in rows
        ]
    }
