ALLOWED_EVENT_FIELDS = {
    "category",
    "recurrence",
    "channel",
    "total_amount",
    "days_since_first_sale",
    "items_count",
    "status",
    "customer_tier",
    "is_recurrent",
    "payment_method",
    "document_type",
    "branch_id",
}


DISALLOWED_SQL_PATTERNS = [
    "select",
    "insert",
    "update",
    "delete",
    "drop",
    "truncate",
    "alter",
    "table",
    "where",
    "union",
    "exec",
    "--",
    ";",
    "/*",
    "*/",
]


DISALLOWED_PREDICTOR_FIELDS = {
    "post_purchase_survey",
    "return_status",
    "refund_date",
    "delivery_confirmation",
    "nps_rating",
    "claim_status",
    "subsequent_order_count",
}


ALLOWED_OPERATORS = {"eq", "neq", "gte", "gt", "lte", "lt", "in"}
