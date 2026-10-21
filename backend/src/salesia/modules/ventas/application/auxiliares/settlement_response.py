from decimal import Decimal
import json


def settlement_response(row):
    detail = json.loads(row.calculation_detail_json or "{}")
    if not isinstance(detail, dict):
        detail = {"legacy": detail, "entries": [], "warnings": ["Cálculo histórico sin detalle por venta conciliado."]}

    attainment = (
        (row.net_sales / row.target_quota * Decimal("100")).quantize(Decimal("0.01"))
        if row.target_quota and row.target_quota > 0
        else Decimal("0")
    )

    return {
        "settlement_id": str(row.id),
        "rep_id": str(row.representative_id),
        "period": row.period,
        "currency": row.currency,
        "version": row.version,
        "calculation_hash": row.calculation_hash,
        "history": json.loads(row.history_json or "[]"),
        "payable_amount": str(row.payable_amount),
        "carried_balance": str(row.carried_balance),
        "payout_reference": row.payout_reference,
        "created_by": str(row.created_by) if row.created_by else None,
        "gross_sales": str(row.gross_sales),
        "returns_deductions": str(row.returns_amount),
        "prior_adjustments": str(row.prior_adjustments),
        "net_sales": str(row.net_sales),
        "target_quota": str(row.target_quota),
        "attainment_percentage": str(attainment),
        "commission_rate_percentage": str(row.commission_rate * Decimal("100")),
        "commission_amount": str(row.commission_amount),
        "status": row.status,
        "rules_version": row.rules_version,
        "rules_snapshot": json.loads(row.rules_snapshot_json or "{}"),
        "calculation_detail": detail,
        "calculated_at": row.created_at.isoformat(),
        "paid_at": row.paid_at.isoformat() if row.paid_at else None,
    }
