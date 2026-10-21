from fastapi import APIRouter

from salesia.modules.auditoria.application.auxiliares.parse_diff import _parse_diff as _parse_diff
from salesia.modules.auditoria.application.contracts.auditoria_consulta import (
    AuditLogCreateRequest as AuditLogCreateRequest,
)
from salesia.modules.auditoria.application.contracts.auditoria_consulta import (
    AuditRetentionPurgeRequest as AuditRetentionPurgeRequest,
)
from salesia.modules.auditoria.application.contracts.privacidad_anonymize_customer import (
    AnonymizeCustomerRequest as AnonymizeCustomerRequest,
)
from salesia.modules.auditoria.application.contracts.privacidad_bloqueo_legal import (
    LegalHoldRequest as LegalHoldRequest,
)
from salesia.modules.auditoria.application.contracts.privacidad_mask_data import MaskDataRequest as MaskDataRequest
from salesia.modules.auditoria.application.contracts.seguridad_claves_api import (
    ApiKeyCreateRequest as ApiKeyCreateRequest,
)
from salesia.modules.auditoria.application.contracts.seguridad_fraud import FraudCheckRequest as FraudCheckRequest
from salesia.modules.auditoria.application.contracts.seguridad_incident import (
    UserQuarantineRequest as UserQuarantineRequest,
)
from salesia.modules.auditoria.application.contracts.seguridad_outgoing_fetch import (
    OutgoingFetchRequest as OutgoingFetchRequest,
)
from salesia.modules.auditoria.application.contracts.seguridad_sanitize_input import (
    SanitizeInputRequest as SanitizeInputRequest,
)
from salesia.modules.auditoria.application.contracts.seguridad_validate_upload import (
    FileUploadValidationRequest as FileUploadValidationRequest,
)
from salesia.modules.auditoria.application.contracts.seguridad_validate_url import (
    UrlValidationRequest as UrlValidationRequest,
)
from salesia.modules.auditoria.presentation.routes import (
    auditoria_consulta,
    auditoria_integridad,
    privacidad_anonymize_customer,
    privacidad_bloqueo_legal,
    privacidad_export_personal_data,
    privacidad_inventario_datos,
    privacidad_mask_data,
    seguridad_amenazas,
    seguridad_claves_api,
    seguridad_fraud,
    seguridad_incident,
    seguridad_outgoing_fetch,
    seguridad_sanitize_input,
    seguridad_supply_chain,
    seguridad_validate_upload,
    seguridad_validate_url,
    seguridad_vulnerabilidades,
)

router = APIRouter(tags=["Seguridad, Auditoría y Privacidad"])
router.include_router(auditoria_consulta.router)
router.include_router(auditoria_integridad.router)
router.include_router(seguridad_claves_api.router)
router.include_router(seguridad_validate_url.router)
router.include_router(seguridad_sanitize_input.router)
router.include_router(privacidad_inventario_datos.router)
router.include_router(privacidad_mask_data.router)
router.include_router(privacidad_export_personal_data.router)
router.include_router(privacidad_anonymize_customer.router)
router.include_router(privacidad_bloqueo_legal.router)
router.include_router(seguridad_outgoing_fetch.router)
router.include_router(seguridad_amenazas.router)
router.include_router(seguridad_validate_upload.router)
router.include_router(seguridad_fraud.router)
router.include_router(seguridad_vulnerabilidades.router)
router.include_router(seguridad_incident.router)
router.include_router(seguridad_supply_chain.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_audit_logs",
            "verify_logs_integrity",
            "get_timeline",
            "purge_retention",
            "get_audit_log_detail",
            "deny_audit_mutation",
            "record_audit_log",
            "export_audit_logs",
            "create_api_key",
            "list_api_keys",
            "revoke_api_key",
            "validate_url_for_ssrf",
            "sanitize_input_text",
            "get_privacy_data_inventory",
            "mask_personal_data",
            "export_customer_personal_data",
            "anonymize_customer",
            "manage_legal_hold",
            "verify_api_key_endpoint",
            "outgoing_fetch_safe",
            "get_threat_model",
            "validate_file_upload",
            "check_commercial_fraud",
            "get_vulnerabilities_status",
            "verify_vulnerability_release_gate",
            "quarantine_compromised_user",
            "get_supply_chain_security_status",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
list_audit_logs = auditoria_consulta.list_audit_logs
verify_logs_integrity = auditoria_integridad.verify_logs_integrity
get_timeline = auditoria_consulta.get_timeline
purge_retention = auditoria_consulta.purge_retention
get_audit_log_detail = auditoria_consulta.get_audit_log_detail
deny_audit_mutation = auditoria_consulta.deny_audit_mutation
record_audit_log = auditoria_consulta.record_audit_log
export_audit_logs = auditoria_consulta.export_audit_logs
create_api_key = seguridad_claves_api.create_api_key
list_api_keys = seguridad_claves_api.list_api_keys
revoke_api_key = seguridad_claves_api.revoke_api_key
validate_url_for_ssrf = seguridad_validate_url.validate_url_for_ssrf
sanitize_input_text = seguridad_sanitize_input.sanitize_input_text
get_privacy_data_inventory = privacidad_inventario_datos.get_privacy_data_inventory
mask_personal_data = privacidad_mask_data.mask_personal_data
export_customer_personal_data = privacidad_export_personal_data.export_customer_personal_data
anonymize_customer = privacidad_anonymize_customer.anonymize_customer
manage_legal_hold = privacidad_bloqueo_legal.manage_legal_hold
verify_api_key_endpoint = seguridad_claves_api.verify_api_key_endpoint
outgoing_fetch_safe = seguridad_outgoing_fetch.outgoing_fetch_safe
get_threat_model = seguridad_amenazas.get_threat_model
validate_file_upload = seguridad_validate_upload.validate_file_upload
check_commercial_fraud = seguridad_fraud.check_commercial_fraud
get_vulnerabilities_status = seguridad_vulnerabilidades.get_vulnerabilities_status
verify_vulnerability_release_gate = seguridad_vulnerabilidades.verify_vulnerability_release_gate
quarantine_compromised_user = seguridad_incident.quarantine_compromised_user
get_supply_chain_security_status = seguridad_supply_chain.get_supply_chain_security_status
