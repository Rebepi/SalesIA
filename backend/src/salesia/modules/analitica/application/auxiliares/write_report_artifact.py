from salesia.modules.analitica.domain.reports import sanitize_branding_payload, write_report_artifact_v2
from salesia.shared.infrastructure.config import settings


def write_report_artifact(
    run_id,
    company_id,
    report_format,
    columns,
    rows,
    report_type="REP_SALES_DETAIL",
    status_condition=None,
    company=None,
):

    branding = (
        sanitize_branding_payload(company)
        if company
        else {
            "company_id": str(company_id),
            "legal_name": "SalesIA Enterprise",
            "tax_id": "",
            "safe_logo_url": "/assets/brand_logo.svg",
            "theme_color": "#1e3a8a",
            "template_version": "v1.0-enterprise",
            "print_layout": {"page_size": "A4", "orientation": "portrait", "show_header_every_page": True},
        }
    )

    return write_report_artifact_v2(
        run_id=run_id,
        company_id=company_id,
        report_format=report_format,
        columns=columns,
        rows=rows,
        report_type=report_type,
        storage_root_path=settings.private_storage_path,
        branding=branding,
        status_condition=status_condition,
    )
