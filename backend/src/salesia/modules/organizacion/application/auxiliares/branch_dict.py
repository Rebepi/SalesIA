from typing import Any

from salesia.shared.infrastructure.models import BranchModel


def branch_dict(row: BranchModel) -> dict[str, Any]:
    return {
        "branch_id": row.id,
        "company_id": row.company_id,
        "code": row.code,
        "name": row.name,
        "timezone": row.timezone,
        "is_active": row.is_active,
    }
