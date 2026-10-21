import urllib.parse
from typing import Optional

from fastapi import HTTPException


def validate_carrier_url(url: Optional[str]) -> Optional[str]:

    if not url:
        return None

    parsed = urllib.parse.urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(422, "El protocolo de seguimiento debe ser HTTP o HTTPS.")

    allowed_domains = {
        "dhl.com",
        "www.dhl.com",
        "fedex.com",
        "www.fedex.com",
        "ups.com",
        "www.ups.com",
        "olvaexpress.pe",
        "www.olvaexpress.pe",
        "olva.pe",
        "carrier.com",
        "tracking.carrier.com",
    }

    host = (parsed.hostname or "").lower()

    if not any(host == d or host.endswith("." + d) for d in allowed_domains):
        raise HTTPException(422, "El dominio del transportista no está autorizado.")

    return url
