import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.infrastructure_models import CreditNoteModel
from salesia.modules.inventario.infrastructure_models import SupplyDocument, SupplyLine
from salesia.modules.inventario.service import document, response
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import SaleModel


def get_sale_return_eligibility(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    sale = db.scalar(select(SaleModel).where(SaleModel.id == sale_id, SaleModel.company_id == current_user.company_id))

    if not sale:
        other = db.scalar(select(SaleModel.id).where(SaleModel.id == sale_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Venta no encontrada.")

    returned_records = db.execute(
        select(SupplyLine.product_id, func.coalesce(func.sum(SupplyLine.quantity), Decimal("0")))
        .join(SupplyDocument, SupplyDocument.id == SupplyLine.document_id)
        .where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.kind == "RETURN",
            SupplyDocument.sale_id == sale.id,
            SupplyDocument.status.in_(("pending_inspection", "accepted")),
        )
        .group_by(SupplyLine.product_id)
    ).all()

    returned_map = dict(returned_records)

    ref_date = sale.confirmed_at or sale.created_at or datetime.now(timezone.utc)

    if ref_date.tzinfo is None:
        ref_date = ref_date.replace(tzinfo=timezone.utc)

    sale_age = datetime.now(timezone.utc) - ref_date

    window_expired = sale_age.days > 30

    lines_res = []

    for line in sale.lines:
        ret_qty = returned_map.get(line.product_id, Decimal("0.000000"))

        elig_qty = max(Decimal("0.000000"), line.quantity - ret_qty)

        disc_per_unit = (
            (line.discount_amount / line.quantity).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
            if line.quantity > 0
            else Decimal("0.000000")
        )

        net_unit = (
            (line.subtotal_amount / line.quantity).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
            if line.quantity > 0
            else line.unit_price_snapshot
        )

        lines_res.append(
            {
                "product_id": str(line.product_id),
                "sku": line.sku_snapshot,
                "name": line.name_snapshot,
                "sold_quantity": str(line.quantity),
                "returned_quantity": str(ret_qty),
                "eligible_quantity": str(elig_qty),
                "unit_price": str(line.unit_price_snapshot),
                "unit_cost": str(line.unit_cost_snapshot),
                "tax_rate": str(line.tax_rate_snapshot),
                "discount_amount": str(line.discount_amount),
                "prorated_discount_per_unit": str(disc_per_unit),
                "net_unit_price": str(net_unit),
                "subtotal_amount": str(line.subtotal_amount),
                "tax_amount": str(line.tax_amount),
                "total_amount": str(line.total_amount),
            }
        )

    return {
        "sale_id": str(sale.id),
        "series": sale.series,
        "number": sale.number,
        "status": sale.status,
        "warehouse_id": str(sale.warehouse_id) if sale.warehouse_id else None,
        "currency": sale.currency,
        "total_amount": str(sale.total_amount),
        "paid_amount": str(sale.paid_amount),
        "is_credit": sale.is_credit,
        "commercial_window_days": sale_age.days,
        "commercial_window_expired": window_expired,
        "lines": lines_res,
    }


def list_returns(sale_id: Optional[UUID], status: Optional[str], current_user: AuthenticatedUser, db: Session):
    query = select(SupplyDocument).where(
        SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "RETURN"
    )

    if sale_id:
        query = query.where(SupplyDocument.sale_id == sale_id)

    if status:
        query = query.where(SupplyDocument.status == status)

    query = query.order_by(SupplyDocument.created_at.desc())

    rows = db.scalars(query).all()

    return [response(r) for r in rows]


def get_return(return_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "RETURN", return_id)

    res = response(row)

    details = json.loads(row.details_json or "{}")

    res["details"] = details

    if row.sale_id:
        cn = db.scalar(
            select(CreditNoteModel).where(
                CreditNoteModel.return_id == row.id, CreditNoteModel.company_id == current_user.company_id
            )
        )

        if cn:
            res["credit_note"] = {
                "id": str(cn.id),
                "series": cn.series,
                "number": cn.number,
                "total_amount": str(cn.total_amount),
                "status": cn.status,
            }

    return res
