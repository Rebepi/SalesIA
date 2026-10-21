from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import verify_audit_chain
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def verify_logs_integrity(current_user: AuthenticatedUser, db: Session):
    return verify_audit_chain(db, current_user.company_id)
