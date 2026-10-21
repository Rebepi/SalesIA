from typing import Any


def default_settings_dict() -> dict[str, Any]:
    return {
        "rounding_mode": "ROUND_HALF_EVEN",
        "default_tax_rate": "0.18",
        "credit_limit_strict": True,
        "tax_included_in_price": False,
        "branding": {"logo_url": "", "legal_name": "SalesIA Enterprise", "footer_text": "Gracias por su compra."},
        "closed_periods": [],
        "closed_until": None,
        "quotas": {"max_files": 1000, "max_exports": 10, "max_import_rows": 5000, "max_intensive_queries": 50},
        "test_mode": False,
        "pricing_policy": {
            "default_volume_discounts_enabled": True,
            "volume_tiers": [{"min_quantity": "10", "discount_percentage": "0.05"}, {"min_quantity": "50", "discount_percentage": "0.10"}],
            "minimum_margin_percentage": "0",
            "maximum_manual_discount_percentage": "100",
        },
        "commission_policy": {
            "version": 1,
            "tiers": [{"minimum_attainment": "0", "rate": "0"}, {"minimum_attainment": "80", "rate": "0.025"}, {"minimum_attainment": "100", "rate": "0.045"}, {"minimum_attainment": "120", "rate": "0.07"}],
        },
        "supplier_performance_policy": {"history_days": 365, "minimum_samples": 3, "on_time_weight": "35", "fill_weight": "25", "acceptance_weight": "25", "invoice_weight": "15"},
        "replenishment_policy": {"default_lead_time_days": 7, "history_days": 30},
        "purchase_matching_policy": {"unit_price_tolerance_percentage": "0", "rounding_tolerance": "0.01"},
    }
