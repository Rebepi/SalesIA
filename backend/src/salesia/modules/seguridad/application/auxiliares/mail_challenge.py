import json
import secrets
from datetime import timedelta
from urllib.parse import quote

from sqlalchemy import update

from salesia.modules.seguridad.application.auxiliares.build_auth_mail_payload import build_auth_mail_payload
from salesia.modules.seguridad.infrastructure.models import AuthChallenge, AuthMail
from salesia.modules.seguridad.infrastructure.sessions import cipher, fingerprint, utcnow
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import CompanyModel


def mail_challenge(db, user, purpose, invited_by=None, role_name=None):
    token = secrets.token_urlsafe(48)
    db.execute(
        update(AuthChallenge)
        .where(AuthChallenge.user_id == user.id, AuthChallenge.purpose == purpose, AuthChallenge.used_at.is_(None))
        .values(used_at=utcnow())
    )
    challenge = AuthChallenge(
        user_id=user.id, token_hash=fingerprint(token), purpose=purpose, expires_at=utcnow() + timedelta(hours=1)
    )
    db.add(challenge)
    link = f"{settings.frontend_url.rstrip('/')}/?auth_action={purpose}&token={quote(token)}"
    company = db.get(CompanyModel, user.company_id)
    company_name = company.trade_name or company.legal_name if company else "SalesIA Enterprise"
    payload = build_auth_mail_payload(user, purpose, link, company_name, invited_by, role_name)
    subject = (
        f"Invitación para unirte a {company_name}" if purpose == "invitation" else "Restablece tu acceso a SalesIA"
    )
    db.add(
        AuthMail(
            recipient=user.email,
            encrypted_body=cipher().encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode(),
            subject=subject,
            created_at=utcnow(),
        )
    )
    db.flush()
    return challenge
