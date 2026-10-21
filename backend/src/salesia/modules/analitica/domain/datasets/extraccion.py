from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.datasets.calidad_privacidad import build_data_quality_report
from salesia.modules.analitica.domain.datasets.definiciones import DatasetGrain
from salesia.shared.infrastructure.models import (
    KardexMovementModel,
    PaymentModel,
    ProductModel,
    SaleLineModel,
    SaleModel,
)


def extract_operational_dataset_rows(
    db: Session, company_id: UUID, grain: str, filters: Optional[dict[str, Any]] = None, watermark: Optional[str] = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filters = filters or {}
    allowed_statuses = tuple(filters.get("statuses") or ["confirmed", "paid"])
    excluded_counts: dict[str, int] = {
        "annulled_status": 0,
        "cancelled_status": 0,
        "draft_status": 0,
        "other_status": 0,
    }

    if grain == DatasetGrain.TICKET.value:
        q_all = select(SaleModel).where(SaleModel.company_id == company_id)
        if filters.get("branch_id"):
            q_all = q_all.where(SaleModel.branch_id == UUID(str(filters["branch_id"])))
        if filters.get("currency"):
            q_all = q_all.where(SaleModel.currency == filters["currency"])
        if filters.get("period") and filters["period"] != "all":
            days = int(str(filters["period"]).replace("d", ""))
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            q_all = q_all.where(SaleModel.created_at >= cutoff)
        if watermark:
            q_all = q_all.where(SaleModel.created_at <= datetime.fromisoformat(watermark))

        all_sales = db.scalars(q_all.order_by(SaleModel.created_at.desc())).all()
        total_received = len(all_sales)

        used_rows: list[dict[str, Any]] = []
        for s in all_sales:
            if s.status not in allowed_statuses:
                key = f"{s.status}_status"
                if key in excluded_counts:
                    excluded_counts[key] += 1
                else:
                    excluded_counts["other_status"] += 1
                if s.status in ("cancelled", "annulled"):
                    excluded_counts["annulled_status"] = excluded_counts.get("annulled_status", 0) + 1
                continue

            paid_sum = db.scalar(
                select(func.coalesce(func.sum(PaymentModel.amount), Decimal("0.000000"))).where(
                    PaymentModel.sale_id == s.id, PaymentModel.status == "confirmed"
                )
            )
            used_rows.append(
                {
                    "sale_id": str(s.id),
                    "id": str(s.id),
                    "series_number": f"{s.series}-{s.number:06d}",
                    "customer_id": str(s.customer_id),
                    "status": s.status,
                    "currency": s.currency,
                    "subtotal_amount": str(s.subtotal_amount),
                    "tax_amount": str(s.tax_amount),
                    "total_amount": str(s.total_amount),
                    "paid_amount": str(paid_sum if paid_sum > Decimal("0") else s.paid_amount),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
            )

        quality = build_data_quality_report(
            total_received=total_received,
            used_rows=used_rows,
            excluded_counts=excluded_counts,
            variable_names=["total_amount", "paid_amount"],
        )
        return used_rows, quality

    elif grain == DatasetGrain.LINES.value:
        q_sales = select(SaleModel).where(SaleModel.company_id == company_id)
        if filters.get("branch_id"):
            q_sales = q_sales.where(SaleModel.branch_id == UUID(str(filters["branch_id"])))
        if watermark:
            q_sales = q_sales.where(SaleModel.created_at <= datetime.fromisoformat(watermark))

        all_sales = db.scalars(q_sales).all()
        total_received = 0
        used_rows = []

        for s in all_sales:
            lines = db.scalars(select(SaleLineModel).where(SaleLineModel.sale_id == s.id)).all()
            total_received += len(lines)
            if s.status not in allowed_statuses:
                key = f"{s.status}_status"
                cnt = len(lines)
                if key in excluded_counts:
                    excluded_counts[key] += cnt
                else:
                    excluded_counts["other_status"] += cnt
                if s.status in ("cancelled", "annulled"):
                    excluded_counts["annulled_status"] = excluded_counts.get("annulled_status", 0) + cnt
                continue

            for line in lines:
                product = db.get(ProductModel, line.product_id)
                cost_val = (
                    line.unit_cost_snapshot
                    if hasattr(line, "unit_cost_snapshot") and line.unit_cost_snapshot is not None
                    else (product.unit_cost if product else None)
                )
                price_val = (
                    line.unit_price_snapshot
                    if hasattr(line, "unit_price_snapshot") and line.unit_price_snapshot is not None
                    else (line.unit_price if hasattr(line, "unit_price") else Decimal("0"))
                )
                used_rows.append(
                    {
                        "line_id": str(line.id),
                        "id": str(line.id),
                        "sale_id": str(s.id),
                        "product_id": str(line.product_id),
                        "sku_snapshot": line.sku_snapshot,
                        "name_snapshot": line.name_snapshot,
                        "quantity": str(line.quantity),
                        "unit_price": str(price_val),
                        "unit_cost": str(cost_val) if cost_val is not None else None,
                        "tax_rate": str(
                            line.tax_rate_snapshot
                            if hasattr(line, "tax_rate_snapshot")
                            else getattr(line, "tax_rate", Decimal("0"))
                        ),
                        "subtotal_amount": str(line.subtotal_amount),
                        "tax_amount": str(line.tax_amount),
                        "total_amount": str(line.total_amount),
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                    }
                )

        quality = build_data_quality_report(
            total_received=total_received,
            used_rows=used_rows,
            excluded_counts=excluded_counts,
            variable_names=["quantity", "unit_price", "unit_cost", "total_amount"],
        )
        return used_rows, quality

    elif grain == DatasetGrain.PAYMENTS.value:
        payments = db.scalars(select(PaymentModel).where(PaymentModel.company_id == company_id)).all()
        used_rows = [
            {
                "payment_id": str(p.id),
                "id": str(p.id),
                "sale_id": str(p.sale_id),
                "amount": str(p.amount),
                "payment_method": p.payment_method,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
            if p.status == "confirmed"
        ]
        quality = build_data_quality_report(
            len(payments), used_rows, {"non_confirmed": len(payments) - len(used_rows)}, ["amount"]
        )
        return used_rows, quality

    elif grain == DatasetGrain.MOVEMENTS.value:
        moves = db.scalars(select(KardexMovementModel).where(KardexMovementModel.company_id == company_id)).all()
        used_rows = [
            {
                "movement_id": str(m.id),
                "id": str(m.id),
                "product_id": str(m.product_id),
                "movement_type": m.movement_type,
                "quantity": str(m.quantity),
                "unit_cost": str(m.unit_cost),
                "total_cost": str(m.total_cost),
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in moves
        ]
        quality = build_data_quality_report(len(moves), used_rows, {}, ["quantity", "unit_cost", "total_cost"])
        return used_rows, quality

    else:
        return [], build_data_quality_report(0, [], {}, [])
