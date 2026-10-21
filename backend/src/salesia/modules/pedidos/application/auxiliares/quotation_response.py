import json
from datetime import timezone
from salesia.modules.pedidos.application.auxiliares.quotation_status import quotation_status


def quotation_response(row):

    return {
        "quotation_id": str(row.id),
        "company_id": str(row.company_id),
        "customer_id": str(row.customer_id),
        "branch_id": str(row.branch_id) if row.branch_id else None,
        "version": row.version,
        "quotation_number": row.quotation_number,
        "status": quotation_status(row),
        "stored_status": row.status,
        "valid_until": row.valid_until,
        "payment_terms_days": row.payment_terms_days,
        "delivery_terms": row.delivery_terms,
        "notes": row.notes,
        "special_conditions": row.special_conditions,
        "seller_id": str(row.seller_id) if row.seller_id else None,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "opened_at": row.opened_at.isoformat() if row.opened_at else None,
        "accepted_at": row.accepted_at.astimezone(timezone.utc).isoformat() if row.accepted_at else None,
        "delivery_channel": row.delivery_channel,
        "delivery_recipient": row.delivery_recipient,
        "communication_log": json.loads(row.communication_log_json or "[]"),
        "currency": row.currency,
        "lines": json.loads(row.lines_json),
        "subtotal_amount": str(row.subtotal_amount),
        "tax_amount": str(row.tax_amount),
        "total_amount": str(row.total_amount),
        "converted_order_id": str(row.converted_order_id) if row.converted_order_id else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
