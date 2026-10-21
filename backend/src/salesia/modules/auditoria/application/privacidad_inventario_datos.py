from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_privacy_data_inventory(current_user: AuthenticatedUser):
    return {
        "inventory": [
            {
                "entity": "Customer",
                "fields": ["doc_number", "legal_name", "email", "phone"],
                "classification": "PII_CONFIDENTIAL",
                "retention_policy": "5_years_tax_compliance",
            },
            {
                "entity": "User",
                "fields": ["email", "full_name", "password_hash"],
                "classification": "CREDENTIAL_RESTRICTED",
                "retention_policy": "duration_of_contract",
            },
            {
                "entity": "AuditLog",
                "fields": ["actor_email", "ip_address"],
                "classification": "FORENSIC_INTERNAL",
                "retention_policy": "7_years_audit_requirement",
            },
        ]
    }
