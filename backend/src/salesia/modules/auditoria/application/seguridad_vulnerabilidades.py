from fastapi import HTTPException, status

from salesia.modules.auditoria.application.configuracion import _PENTEST_FINDINGS
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_vulnerabilities_status(current_user: AuthenticatedUser):
    open_critical_or_high = [
        f for f in _PENTEST_FINDINGS if f["severity"] in ("CRITICAL", "HIGH") and f["status"] == "OPEN"
    ]
    return {
        "findings": _PENTEST_FINDINGS,
        "total_count": len(_PENTEST_FINDINGS),
        "open_critical_or_high_count": len(open_critical_or_high),
        "is_release_blocked": len(open_critical_or_high) > 0,
    }


def verify_vulnerability_release_gate(current_user: AuthenticatedUser):
    open_critical_or_high = [
        f for f in _PENTEST_FINDINGS if f["severity"] in ("CRITICAL", "HIGH") and f["status"] == "OPEN"
    ]
    if open_critical_or_high:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Release bloqueado: existen hallazgos de pentest críticos o altos sin resolver.",
        )
    return {
        "release_approved": True,
        "open_critical_findings": 0,
        "detail": "Todos los hallazgos críticos y altos de pentest han sido remediados y verificados.",
    }
