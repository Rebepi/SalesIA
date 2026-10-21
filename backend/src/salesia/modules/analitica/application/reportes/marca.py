import re
from typing import Any

from salesia.shared.infrastructure.models import CompanyModel


def sanitize_branding_payload(company: CompanyModel) -> dict[str, Any]:
    safe_legal_name = re.sub(r"<[^>]*>", "", company.legal_name or "")
    safe_tax_id = re.sub(r"<[^>]*>", "", company.tax_id or "")
    return {
        "company_id": str(company.id),
        "company_name": safe_legal_name,
        "legal_name": safe_legal_name,
        "trade_name": re.sub(r"<[^>]*>", "", company.trade_name or safe_legal_name),
        "tax_id": safe_tax_id,
        "safe_logo_url": "/assets/brand_logo.svg",
        "theme_color": "#1e3a8a",
        "primary_color": "#1e3a8a",
        "secondary_color": "#0f766e",
        "footer_text": f"Documento emitido por {safe_legal_name}",
        "template_version": "v1.0-enterprise",
        "print_layout": {"page_size": "A4", "orientation": "portrait", "show_header_every_page": True},
    }
