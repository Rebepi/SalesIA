import json


def _serialize_return(ret):

    evidence = json.loads(ret.evidence_urls_json) if ret.evidence_urls_json else []

    details_base = json.loads(ret.details_json) if ret.details_json else {}

    from salesia.modules.finanzas.application.politicas_devolucion import return_valuation
    details_base["valuation"] = return_valuation(ret)
    details_base["evidence_urls"] = evidence

    details_base["is_without_receipt"] = ret.is_without_receipt

    if ret.requested_by:
        details_base["requested_by"] = str(ret.requested_by)

    if ret.rejection_criterion:
        details_base["rejection_criterion"] = ret.rejection_criterion

    if ret.rejection_reason:
        details_base["rejection_reason"] = ret.rejection_reason

    return {
        "id": str(ret.id),
        "company_id": str(ret.company_id),
        "sale_id": str(ret.sale_id) if ret.sale_id else None,
        "customer_id": str(ret.customer_id),
        "warehouse_id": str(ret.warehouse_id),
        "status": ret.status,
        "reason": ret.reason,
        "credit_note_id": str(ret.credit_note_id) if ret.credit_note_id else None,
        "details": details_base,
        "lines": [
            {
                "product_id": str(ln.product_id),
                "sale_line_id": str(ln.sale_line_id) if ln.sale_line_id else None,
                "serial_numbers": json.loads(ln.serial_numbers_json or "[]"),
                "quantity": str(ln.quantity),
                "disposition": ln.disposition,
                "unit_price_snapshot": str(ln.unit_price_snapshot),
                "discount_per_unit": str(ln.discount_per_unit),
            }
            for ln in ret.lines
        ],
        "created_at": ret.created_at.isoformat(),
    }
