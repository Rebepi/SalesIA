import ipaddress
import socket
from typing import Any, Optional
from urllib.parse import urlparse, urljoin
import httpx


def validate_outgoing_target_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Esquema no permitido: {parsed.scheme}")

    if parsed.username or parsed.password:
        raise ValueError("No se permiten credenciales embebidas en la URL")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL sin nombre de host válido")

    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or hostname.lower().endswith((".local", ".internal", ".lan")):
        raise ValueError("Destino a red privada o local prohibida por política anti-SSRF")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        resolved_infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        if not resolved_infos:
            raise ValueError("El host no pudo resolverse por DNS")
        for info in resolved_infos:
            ip_str = info[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved or not ip_obj.is_global:
                raise ValueError(f"Destino no permitido: {hostname} resuelve a dirección IP no pública {ip_str}")
    except socket.gaierror:
        raise ValueError("El host no pudo resolverse por DNS")


def safe_outgoing_request(
    url: str,
    method: str = "GET",
    headers: Optional[dict[str, str]] = None,
    json_body: Optional[Any] = None,
    timeout: float = 5.0,
    max_redirects: int = 3
) -> dict[str, Any]:
    validate_outgoing_target_url(url)
    current_url = url
    redirect_count = 0

    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        while True:
            resp = client.request(method=method, url=current_url, headers=headers, json=json_body)
            if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                if redirect_count >= max_redirects:
                    raise ValueError("Se excedió el número máximo de redirecciones permitidas")
                next_url = urljoin(current_url, resp.headers["location"])
                validate_outgoing_target_url(next_url)
                current_url = next_url
                redirect_count += 1
                continue
            return {
                "status_code": resp.status_code,
                "url": str(resp.url),
                "headers": dict(resp.headers),
                "content_preview": resp.text[:1000]
            }
