from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.statistics import (
    calculate_quantiles,
    calculate_stdev,
    calculate_variance,
    compute_statistical_summary,
)
from salesia.modules.operaciones.infrastructure_models import CommissionSettlement, SalesRepresentative
from salesia.shared.infrastructure.models import (
    CustomerModel,
    KardexMovementModel,
    PaymentModel,
    ProductModel,
    SaleModel,
)
from salesia.shared.infrastructure.transactions import RefundModel


def _execute_report_data(
    report_type: str, company_id: UUID, db: Session, limit: int = 50000
) -> tuple[list[str], list[dict[str, Any]]]:

    if report_type == "REP_SALES_DETAIL":
        columns = [
            "sale_id",
            "series_number",
            "customer_id",
            "subtotal",
            "tax",
            "total_amount",
            "paid_amount",
            "currency",
            "status",
            "created_at",
        ]

        sales = (
            db.execute(
                select(SaleModel)
                .where(SaleModel.company_id == company_id)
                .order_by(SaleModel.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        rows = [
            {
                "sale_id": str(s.id),
                "series_number": f"{s.series}-{s.number:06d}",
                "customer_id": str(s.customer_id) if s.customer_id else "",
                "subtotal": str(s.subtotal_amount),
                "tax": str(s.tax_amount),
                "total_amount": str(s.total_amount),
                "paid_amount": str(s.paid_amount),
                "currency": s.currency,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in sales
        ]

        return columns, rows

    elif report_type == "REP_STATISTICAL_DISTRIBUTION":
        columns = ["metric", "value"]

        sales = (
            db.execute(
                select(SaleModel.total_amount)
                .where(SaleModel.company_id == company_id, SaleModel.status.in_(["confirmed", "paid"]))
                .limit(limit)
            )
            .scalars()
            .all()
        )

        amounts = [Decimal(str(a)) for a in sales if a is not None]

        if not amounts:
            rows = [
                {"metric": "sample_size_n", "value": "0"},
                {"metric": "mean_ticket", "value": "0.00"},
                {"metric": "median_ticket", "value": "0.00"},
                {"metric": "variance", "value": "0.00"},
                {"metric": "standard_deviation", "value": "0.00"},
            ]

        else:
            summary = compute_statistical_summary(amounts)

            var = calculate_variance(amounts, is_sample=True) if len(amounts) > 1 else Decimal("0.000000")

            sd = calculate_stdev(amounts, is_sample=True) if len(amounts) > 1 else Decimal("0.000000")

            quant = calculate_quantiles(amounts)

            rows = [
                {"metric": "sample_size_n", "value": str(len(amounts))},
                {"metric": "mean_ticket", "value": str(summary.mean)},
                {"metric": "median_ticket", "value": str(summary.median)},
                {"metric": "minimum_ticket", "value": str(summary.minimum)},
                {"metric": "maximum_ticket", "value": str(summary.maximum)},
                {"metric": "variance", "value": str(var)},
                {"metric": "standard_deviation", "value": str(sd)},
                {"metric": "q1", "value": str(quant["q1"])},
                {"metric": "q3", "value": str(quant["q3"])},
                {"metric": "iqr", "value": str(quant["iqr"])},
            ]

        return columns, rows

    elif report_type == "REP_CRM_CATALOG":
        columns = ["entity_type", "id", "code_or_doc", "name", "category_or_type", "status"]

        customers = (
            db.execute(select(CustomerModel).where(CustomerModel.company_id == company_id).limit(limit // 2))
            .scalars()
            .all()
        )

        products = (
            db.execute(select(ProductModel).where(ProductModel.company_id == company_id).limit(limit // 2))
            .scalars()
            .all()
        )

        rows = []

        for c in customers:
            rows.append(
                {
                    "entity_type": "customer",
                    "id": str(c.id),
                    "code_or_doc": c.doc_number,
                    "name": c.legal_name,
                    "category_or_type": c.doc_type,
                    "status": "active" if c.is_active else "inactive",
                }
            )

        for p in products:
            rows.append(
                {
                    "entity_type": "product",
                    "id": str(p.id),
                    "code_or_doc": p.sku,
                    "name": p.name,
                    "category_or_type": p.category,
                    "status": "active" if p.is_active else "inactive",
                }
            )

        return columns, rows

    elif report_type == "REP_SALES_REPS_COMMISSIONS":
        columns = [
            "rep_or_branch_id",
            "sales_count",
            "gross_amount",
            "returns_deductions",
            "net_amount",
            "commission_rate",
            "payable_commission",
        ]

        reps = db.scalars(select(SalesRepresentative).where(SalesRepresentative.company_id == company_id)).all()

        rows = []

        for r in reps:
            sales = db.scalars(
                select(SaleModel).where(
                    SaleModel.company_id == company_id,
                    SaleModel.sales_rep_id == r.id,
                    SaleModel.status.in_(["confirmed", "paid"]),
                )
            ).all()

            total_gross = sum((s.total_amount for s in sales), Decimal("0.000000"))

            refund_sum = db.scalar(
                select(func.coalesce(func.sum(RefundModel.amount), 0))
                .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
                .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
                .where(RefundModel.company_id == company_id, SaleModel.sales_rep_id == r.id)
            ) or Decimal("0.000000")

            net_amt = max(Decimal("0"), total_gross - refund_sum)

            latest_settle = db.scalar(
                select(CommissionSettlement)
                .where(CommissionSettlement.company_id == company_id, CommissionSettlement.representative_id == r.id)
                .order_by(CommissionSettlement.created_at.desc())
            )

            comm_rate = (
                latest_settle.commission_rate
                if latest_settle
                else (Decimal("0.045") if net_amt >= r.monthly_quota else Decimal("0.025"))
            )

            payable = (net_amt * comm_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

            rows.append(
                {
                    "rep_or_branch_id": str(r.id),
                    "sales_count": str(len(sales)),
                    "gross_amount": str(total_gross),
                    "returns_deductions": str(refund_sum),
                    "net_amount": str(net_amt),
                    "commission_rate": f"{(comm_rate * Decimal('100')):.2f}%",
                    "payable_commission": str(payable),
                }
            )

        if not rows:
            sales = (
                db.execute(
                    select(SaleModel)
                    .where(SaleModel.company_id == company_id, SaleModel.status.in_(["confirmed", "paid"]))
                    .limit(limit)
                )
                .scalars()
                .all()
            )

            total_gross = sum((s.total_amount for s in sales), Decimal("0.000000"))

            refund_sum = db.scalar(
                select(func.coalesce(func.sum(RefundModel.amount), 0)).where(RefundModel.company_id == company_id)
            ) or Decimal("0.000000")

            net_amt = max(Decimal("0"), total_gross - refund_sum)

            payable = (net_amt * Decimal("0.025")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

            rows.append(
                {
                    "rep_or_branch_id": str(company_id),
                    "sales_count": str(len(sales)),
                    "gross_amount": str(total_gross),
                    "returns_deductions": str(refund_sum),
                    "net_amount": str(net_amt),
                    "commission_rate": "2.50%",
                    "payable_commission": str(payable),
                }
            )

        return columns, rows

    elif report_type == "REP_KARDEX_VALUATION":
        columns = [
            "product_id",
            "sku",
            "name",
            "last_movement_type",
            "quantity_delta",
            "physical_stock",
            "moving_average_cost",
            "total_valuation",
        ]

        movements = (
            db.execute(
                select(KardexMovementModel)
                .where(KardexMovementModel.company_id == company_id)
                .order_by(KardexMovementModel.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        rows = []

        for m in movements:
            val = (m.resulting_physical_qty * m.moving_average_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

            rows.append(
                {
                    "product_id": str(m.product_id),
                    "sku": "SKU-" + str(m.product_id)[:8],
                    "name": "Producto Inventariado",
                    "last_movement_type": m.movement_type,
                    "quantity_delta": str(m.quantity_delta),
                    "physical_stock": str(m.resulting_physical_qty),
                    "moving_average_cost": str(m.moving_average_cost),
                    "total_valuation": str(val),
                }
            )

        return columns, rows

    elif report_type == "REP_CASH_CLOSURE_RECEIVABLES":
        columns = [
            "sale_id",
            "series_number",
            "customer_id",
            "total_amount",
            "paid_amount",
            "pending_receivable",
            "status",
        ]

        sales = (
            db.execute(
                select(SaleModel)
                .where(SaleModel.company_id == company_id)
                .order_by(SaleModel.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        rows = []

        for s in sales:
            pending = (s.total_amount - s.paid_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

            rows.append(
                {
                    "sale_id": str(s.id),
                    "series_number": f"{s.series}-{s.number:06d}",
                    "customer_id": str(s.customer_id) if s.customer_id else "",
                    "total_amount": str(s.total_amount),
                    "paid_amount": str(s.paid_amount),
                    "pending_receivable": str(pending),
                    "status": s.status,
                }
            )

        return columns, rows

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tipo de reporte desconocido: {report_type}"
        )
