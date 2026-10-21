def rep_detail_response(row):

    return {
        "rep_id": str(row.id),
        "code": row.code,
        "user_id": str(row.user_id) if row.user_id else None,
        "full_name": row.full_name,
        "branch_id": str(row.branch_id) if row.branch_id else None,
        "team": row.team,
        "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
        "territory": row.territory,
        "monthly_quota": str(row.monthly_quota) if row.monthly_quota is not None else None,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat(),
    }


def rep_detail_response(row):

    return {
        "rep_id": str(row.id),
        "code": row.code,
        "user_id": str(row.user_id) if row.user_id else None,
        "full_name": row.full_name,
        "branch_id": str(row.branch_id) if row.branch_id else None,
        "team": row.team,
        "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
        "territory": row.territory,
        "monthly_quota": str(row.monthly_quota) if row.monthly_quota is not None else None,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
