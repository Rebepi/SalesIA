from fastapi import HTTPException, status

from salesia.modules.auditoria.application.contracts.seguridad_outgoing_fetch import OutgoingFetchRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.safe_client import safe_outgoing_request


def outgoing_fetch_safe(payload: OutgoingFetchRequest, current_user: AuthenticatedUser):
    try:
        result = safe_outgoing_request(payload.url, method=payload.method)
        return {
            "is_safe": True,
            "url": payload.url,
            "status_code": result["status_code"],
            "preview": result["content_preview"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SSRF bloqueado: {str(exc)}")
