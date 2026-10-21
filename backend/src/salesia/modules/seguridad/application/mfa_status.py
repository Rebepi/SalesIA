from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.mfa_status import PasswordResetRequestModel
from salesia.shared.infrastructure.models import UserModel


def get_mfa_status(email: str, db: Session):
    clean_email = email.lower().strip()
    if not clean_email or "@" not in clean_email:
        return {"mfa_enabled": False}
    user = db.scalar(select(UserModel).where(func.lower(UserModel.email) == clean_email))
    return {"mfa_enabled": bool(user and user.mfa_enabled and user.is_active)}


def check_mfa_status(req: PasswordResetRequestModel, db: Session):
    clean_email = str(req.email).lower().strip()
    user = db.scalar(select(UserModel).where(func.lower(UserModel.email) == clean_email))
    return {"mfa_enabled": bool(user and user.mfa_enabled and user.is_active)}
