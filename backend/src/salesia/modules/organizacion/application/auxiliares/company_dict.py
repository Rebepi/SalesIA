from typing import Any

from salesia.shared.infrastructure.models import CompanyModel


def company_dict(row: CompanyModel) -> dict[str, Any]:
    return {
        "company_id": row.id,
        "tax_id": row.tax_id,
        "legal_name": row.legal_name,
        "trade_name": row.trade_name,
        "base_currency": row.base_currency,
        "is_active": row.is_active,
        "created_at": row.created_at,
    }
