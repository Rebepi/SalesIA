import json
from datetime import datetime, timezone
from decimal import Decimal


def response_for(sale):
    total = Decimal(str(sale.total_amount or 0))
    paid = Decimal(str(sale.paid_amount or 0))
    balance = max(Decimal("0.00"), total - paid)

    raw_status = str(sale.status or "draft").lower()
    if raw_status in ("cancelled", "annulled"):
        doc_status = "Anulada"
    elif raw_status in ("confirmed", "paid"):
        doc_status = "Confirmada"
    else:
        doc_status = "Borrador"

    if paid <= 0:
        pay_status = "Sin cobrar"
    elif paid >= total:
        pay_status = "Pagada"
    else:
        pay_status = "Parcial"

    if raw_status == "draft":
        delivery_status = "Pendiente"
        sunat_status = "No aplica"
    elif raw_status in ("cancelled", "annulled"):
        delivery_status = "No aplica"
        sunat_status = "Baja"
    else:
        delivery_status = {"delivered": "Entregada", "partial": "Parcial", "pending": "Pendiente"}.get(sale.fulfillment_status, "Pendiente")
        sunat_status = "Aceptado"

    return_status = "Sin devolución"
    if raw_status == "refunded":
        return_status = "Total"

    customer_name = ""
    customer_doc = ""
    if hasattr(sale, "customer") and sale.customer:
        customer_name = getattr(sale.customer, "legal_name", "") or getattr(sale.customer, "name", "")
        doc_type = getattr(sale.customer, "doc_type", "") or ""
        doc_num = getattr(sale.customer, "doc_number", "") or ""
        customer_doc = f"{doc_type} {doc_num}".strip()

    branch_name = ""
    if hasattr(sale, "branch") and sale.branch:
        branch_name = getattr(sale.branch, "name", "") or ""

    sales_rep_name = ""
    if hasattr(sale, "sales_rep") and sale.sales_rep:
        sales_rep_name = getattr(sale.sales_rep, "full_name", "") or ""

    created_iso = sale.created_at.isoformat() if hasattr(sale, "created_at") and sale.created_at else None

    return {
        "sale_id": str(sale.id),
        "id": str(sale.id),
        "company_id": str(sale.company_id),
        "branch_id": str(sale.branch_id),
        "customer_id": str(sale.customer_id),
        "warehouse_id": str(sale.warehouse_id) if sale.warehouse_id else None,
        "sales_rep_id": str(sale.sales_rep_id) if sale.sales_rep_id else None,
        "status": sale.status,
        "currency": sale.currency,
        "exchange_rate": str(sale.exchange_rate),
        "total_amount": str(sale.total_amount),
        "paid_amount": str(sale.paid_amount),
        "balance_amount": str(balance),
        "items_count": len(sale.lines),
        "return_policies": [{"sale_line_id": str(line.id), "product_name": line.name_snapshot, "policy": json.loads(line.return_policy_snapshot) if line.return_policy_snapshot else None} for line in sale.lines],
        "version": sale.version,
        "is_credit": sale.is_credit,
        "payment_terms_days": sale.payment_terms_days,
        "due_at": sale.due_at.isoformat() if sale.due_at else None,
        "order_id": str(sale.order_id) if sale.order_id else None,
        "fulfillment_status": sale.fulfillment_status,
        "document_type": "RECEIPT" if sale.series.startswith("B") else "INVOICE",
        "number": f"{sale.series}-{sale.number:08d}",
        "series": sale.series,
        "correlative": sale.number,
        "coupon_code": sale.coupon_code,
        "notes": sale.notes,
        "delivery_address": sale.delivery_address,
        "internal_observations": sale.internal_observations,
        "due_calendar": json.loads(sale.due_calendar_snapshot_json) if sale.due_calendar_snapshot_json else None,
        "pricing_explanation": json.loads(sale.pricing_explanation_json or "[]"),
        "created_at": created_iso,
        "customer_name": customer_name,
        "customer_document": customer_doc,
        "branch_name": branch_name,
        "sales_rep_name": sales_rep_name,
        "document_status": doc_status,
        "payment_status": pay_status,
        "delivery_status": delivery_status,
        "sunat_status": sunat_status,
        "return_status": return_status,
        "origin": "ORDER" if sale.order_id else "POS",
    }

