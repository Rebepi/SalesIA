from datetime import date
from decimal import Decimal, ROUND_CEILING
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, update

from salesia.modules.inventario.application.homologacion_proveedor import supplier_qualified
from salesia.modules.inventario.infrastructure.models.catalogo_proveedor import SupplierProductModel
from salesia.modules.inventario.infrastructure_models import Supplier
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.organizacion.application.periodos import business_date
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class SupplierProductRequest(BaseModel):
    supplier_id: UUID
    product_id: UUID
    purchase_presentation: str = Field(default="", max_length=128)
    supplier_sku: str = Field(default="", max_length=128)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    unit_cost: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    minimum_quantity: Decimal = Field(default=Decimal("1"), gt=0, max_digits=20, decimal_places=6)
    order_multiple: Decimal = Field(default=Decimal("1"), gt=0, max_digits=20, decimal_places=6)
    lead_time_days: int = Field(default=7, ge=0, le=3650)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    is_preferred: bool = False
    is_active: bool = True
    version: int = Field(default=0, ge=0)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("La vigencia final no puede ser anterior al inicio.")
        return self


def current_condition(row, today):
    return row.is_active and (row.valid_from is None or row.valid_from <= today) and (row.valid_until is None or row.valid_until >= today)


def rounded_purchase_quantity(quantity, condition):
    if quantity <= 0:
        return Decimal("0")
    if condition is None:
        return quantity
    return (max(quantity, condition.minimum_quantity) / condition.order_multiple).to_integral_value(rounding=ROUND_CEILING) * condition.order_multiple


def serialize(db, row, today):
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == row.company_id, Supplier.id == row.supplier_id))
    product = db.scalar(select(ProductModel).where(ProductModel.company_id == row.company_id, ProductModel.id == row.product_id))
    return {"id": str(row.id), "supplier_id": str(row.supplier_id), "supplier_name": supplier.legal_name if supplier else "Proveedor", "product_id": str(row.product_id), "product_name": product.name if product else "Producto", "sku": product.sku if product else "", "supplier_sku": row.supplier_sku, "purchase_presentation": row.purchase_presentation, "currency": row.currency, "unit_cost": str(row.unit_cost), "minimum_quantity": str(row.minimum_quantity), "order_multiple": str(row.order_multiple), "lead_time_days": row.lead_time_days, "valid_from": row.valid_from.isoformat() if row.valid_from else None, "valid_until": row.valid_until.isoformat() if row.valid_until else None, "is_preferred": row.is_preferred, "is_active": row.is_active, "is_current": current_condition(row, today) and bool(supplier and supplier_qualified(supplier, today) and product and product.is_active), "version": row.version, "notes": row.notes}


def list_catalog(db, user, supplier_id=None, product_id=None, currency=None, current_only=False, limit=50, offset=0):
    from sqlalchemy import func, or_
    today = business_date(db, user.company_id)
    statement = select(SupplierProductModel).join(Supplier, Supplier.id == SupplierProductModel.supplier_id).join(ProductModel, ProductModel.id == SupplierProductModel.product_id).where(SupplierProductModel.company_id == user.company_id, Supplier.company_id == user.company_id, ProductModel.company_id == user.company_id)
    if supplier_id:
        statement = statement.where(SupplierProductModel.supplier_id == supplier_id)
    if product_id:
        statement = statement.where(SupplierProductModel.product_id == product_id)
    if currency:
        statement = statement.where(SupplierProductModel.currency == currency)
    if current_only:
        statement = statement.where(SupplierProductModel.is_active.is_(True), Supplier.is_active.is_(True), Supplier.qualification_status == "approved", or_(Supplier.qualification_until.is_(None), Supplier.qualification_until >= today), ProductModel.is_active.is_(True), or_(SupplierProductModel.valid_from.is_(None), SupplierProductModel.valid_from <= today), or_(SupplierProductModel.valid_until.is_(None), SupplierProductModel.valid_until >= today))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(statement.order_by(SupplierProductModel.is_preferred.desc(), SupplierProductModel.product_id, SupplierProductModel.unit_cost, SupplierProductModel.id).offset(offset).limit(limit)).all()
    return {"items": [serialize(db, row, today) for row in rows], "total_count": total}


def save_catalog(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "supplier_catalog.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == payload.supplier_id))
    product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == payload.product_id))
    if supplier is None or product is None or (payload.is_active and (not supplier.is_active or not product.is_active)):
        raise HTTPException(422, "Selecciona un proveedor y un producto activos de la empresa.")
    from salesia.modules.catalogo.service import validate_unit_fraction
    validate_unit_fraction(db, user.company_id, product.unit_of_measure, payload.minimum_quantity)
    validate_unit_fraction(db, user.company_id, product.unit_of_measure, payload.order_multiple)
    row = db.scalar(select(SupplierProductModel).where(SupplierProductModel.company_id == user.company_id, SupplierProductModel.supplier_id == payload.supplier_id, SupplierProductModel.product_id == payload.product_id, SupplierProductModel.currency == payload.currency).with_for_update())
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "Las condiciones cambiaron; recarga el catálogo antes de guardar.")
    before = serialize(db, row, business_date(db, user.company_id)) if row else None
    if payload.is_preferred and payload.is_active:
        db.execute(update(SupplierProductModel).where(SupplierProductModel.company_id == user.company_id, SupplierProductModel.product_id == payload.product_id, SupplierProductModel.currency == payload.currency, SupplierProductModel.supplier_id != payload.supplier_id, SupplierProductModel.is_preferred.is_(True)).values(is_preferred=False, version=SupplierProductModel.version + 1))
    if row is None:
        row = SupplierProductModel(company_id=user.company_id, supplier_id=payload.supplier_id, product_id=payload.product_id, currency=payload.currency, version=0)
        db.add(row)
    for field, value in payload.model_dump(exclude={"version"}).items():
        setattr(row, field, value)
    row.supplier_sku = row.supplier_sku.strip()
    row.is_preferred = payload.is_preferred and payload.is_active
    row.version += 1
    db.flush()
    result = serialize(db, row, business_date(db, user.company_id))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_SUPPLIER_PRODUCT", entity_type="SupplierProduct", entity_id=row.id, diff={"before": before, "after": result})
    complete_request(record, result)
    db.commit()
    return result


def purchase_catalog_snapshot(db, user, supplier_id, currency, items):
    today = business_date(db, user.company_id)
    snapshots = []
    for item in items:
        row = db.scalar(select(SupplierProductModel).where(SupplierProductModel.company_id == user.company_id, SupplierProductModel.supplier_id == supplier_id, SupplierProductModel.product_id == item.product_id, SupplierProductModel.currency == currency))
        if row is None or not current_condition(row, today):
            continue
        if item.quantity < row.minimum_quantity or item.quantity % row.order_multiple != 0:
            raise HTTPException(422, f"El proveedor exige al menos {row.minimum_quantity} y múltiplos de {row.order_multiple} para el producto {item.product_id}.")
        snapshots.append({"condition_id": str(row.id), "condition_version": row.version, "product_id": str(row.product_id), "supplier_sku": row.supplier_sku, "purchase_presentation": row.purchase_presentation, "currency": row.currency, "catalog_unit_cost": str(row.unit_cost), "ordered_unit_cost": str(item.unit_cost), "minimum_quantity": str(row.minimum_quantity), "order_multiple": str(row.order_multiple), "lead_time_days": row.lead_time_days, "valid_from": row.valid_from.isoformat() if row.valid_from else None, "valid_until": row.valid_until.isoformat() if row.valid_until else None})
    return snapshots
