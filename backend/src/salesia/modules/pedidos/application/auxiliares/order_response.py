import json


def order_response(row, customer_name=None):

    return {
        "order_id": str(row.id),
        "id": str(row.id),
        "company_id": str(row.company_id),
        "quotation_id": str(row.quotation_id) if row.quotation_id else None,
        "order_number": row.order_number,
        "customer_id": str(row.customer_id),
        "customer_name": customer_name,
        "branch_id": str(row.branch_id),
        "warehouse_id": str(row.warehouse_id),
        "status": row.status,
        "currency": row.currency,
        "lines": json.loads(row.lines_json),
        "subtotal_amount": str(row.subtotal_amount),
        "tax_amount": str(row.tax_amount),
        "total_amount": str(row.total_amount),
        "stock_reserved": row.stock_reserved,
        "requires_approval": row.requires_approval,
        "payment_terms_days": row.payment_terms_days,
        "delivery_terms": row.delivery_terms,
        "customer_po_number": row.customer_po_number,
        "attachments": json.loads(row.attachments_json) if row.attachments_json else [],
        "reservation_expires_at": row.reservation_expires_at,
        "history": json.loads(row.history_json),
        "picking": json.loads(row.picking_json or "{}"),
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
