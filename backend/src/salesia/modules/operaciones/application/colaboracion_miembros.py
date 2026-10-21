from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import UserModel


def collaboration_members(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(UserModel)
        .where(UserModel.company_id == current_user.company_id, UserModel.is_active.is_(True))
        .order_by(UserModel.full_name, UserModel.email)
    ).all()

    return {"items": [{"id": str(row.id), "name": row.full_name or row.email, "email": row.email} for row in rows]}
