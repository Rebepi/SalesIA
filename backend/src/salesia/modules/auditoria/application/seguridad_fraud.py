from decimal import Decimal

from salesia.modules.auditoria.application.contracts.seguridad_fraud import FraudCheckRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def check_commercial_fraud(payload: FraudCheckRequest, current_user: AuthenticatedUser):
    if payload.actor_id == payload.approver_id:
        return {
            "allowed": False,
            "fraud_detected": True,
            "violation_type": "SELF_APPROVAL_PROHIBITED",
            "detail": "Autoaprobación prohibida: el operador no puede aprobar su propia operación.",
        }
    recent_sum = sum(payload.recent_transactions, Decimal("0.00"))
    projected_total = recent_sum + payload.amount
    if projected_total > payload.aggregate_limit:
        return {
            "allowed": False,
            "fraud_detected": True,
            "violation_type": "SMURFING_AGGREGATE_EXCEEDED",
            "detail": f"Alerta de fraccionamiento: el acumulado de operaciones ({projected_total}) excede el límite de política ({payload.aggregate_limit}).",
        }
    if payload.amount > payload.single_tx_limit:
        return {
            "allowed": True,
            "fraud_detected": False,
            "requires_supervision": True,
            "detail": "El importe individual excede el umbral ordinario y requiere autorización gerencial.",
        }
    return {
        "allowed": True,
        "fraud_detected": False,
        "requires_supervision": False,
        "detail": "Operación conforme a las políticas de mitigación de fraude comercial.",
    }
