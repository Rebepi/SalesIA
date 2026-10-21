import ipaddress
import socket
from urllib.parse import urlparse

from salesia.modules.auditoria.application.contracts.seguridad_validate_url import UrlValidationRequest


def validate_url_for_ssrf(payload: UrlValidationRequest):
    parsed = urlparse(payload.url)
    if parsed.scheme not in ("http", "https"):
        return {"is_safe": False, "url": payload.url, "reason": f"Esquema no permitido: {parsed.scheme}"}

    hostname = parsed.hostname
    if not hostname:
        return {"is_safe": False, "url": payload.url, "reason": "URL sin nombre de host válido"}

    if parsed.username or parsed.password:
        return {"is_safe": False, "url": payload.url, "reason": "No se permiten credenciales embebidas en la URL"}
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return {
            "is_safe": False,
            "url": payload.url,
            "reason": "Intento de acceso a interfaz loopback bloqueado por protección anti-SSRF",
        }

    try:
        resolved = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
        if not resolved:
            return {"is_safe": False, "url": payload.url, "reason": "El host no pudo resolverse"}
        if any(not ipaddress.ip_address(address).is_global for address in resolved):
            return {"is_safe": False, "url": payload.url, "reason": "El host resuelve a una dirección no pública"}
    except (ValueError, OSError):
        return {"is_safe": False, "url": payload.url, "reason": "El host no pudo validarse"}

    return {"is_safe": True, "url": payload.url, "reason": "URL validada externamente de forma segura"}
