from fastapi import APIRouter

from salesia.modules.finanzas.application.auxiliares.ensure_default_methods import (
    ensure_default_methods as ensure_default_methods,
)
from salesia.modules.finanzas.application.auxiliares.get_sale_eligible_lines import (
    _get_sale_eligible_lines as _get_sale_eligible_lines,
)
from salesia.modules.finanzas.application.auxiliares.serialize_return import _serialize_return as _serialize_return
from salesia.modules.finanzas.application.contracts.caja_arqueo_relevo import (
    ApproveDifferenceRequest as ApproveDifferenceRequest,
)
from salesia.modules.finanzas.application.contracts.caja_arqueo_relevo import BlindCountRequest as BlindCountRequest
from salesia.modules.finanzas.application.contracts.caja_arqueo_relevo import (
    CashSessionCloseRequest as CashSessionCloseRequest,
)
from salesia.modules.finanzas.application.contracts.caja_sesiones_movimientos import (
    CashSessionMovementRequest as CashSessionMovementRequest,
)
from salesia.modules.finanzas.application.contracts.caja_sesiones_movimientos import (
    CashSessionOpenRequest as CashSessionOpenRequest,
)
from salesia.modules.finanzas.application.contracts.comunes import ReconciliationLine as ReconciliationLine
from salesia.modules.finanzas.application.contracts.comunes import ReturnExchangeItem as ReturnExchangeItem
from salesia.modules.finanzas.application.contracts.comunes import ReturnInspectionItem as ReturnInspectionItem
from salesia.modules.finanzas.application.contracts.comunes import ReturnItemRequest as ReturnItemRequest
from salesia.modules.finanzas.application.contracts.conciliaciones import (
    ReconciliationCreateRequest as ReconciliationCreateRequest,
)
from salesia.modules.finanzas.application.contracts.conciliaciones import (
    ReconciliationResolveRequest as ReconciliationResolveRequest,
)
from salesia.modules.finanzas.application.contracts.cuentas_cobrar import (
    CollectionActivityRequest as CollectionActivityRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnAcceptRequest as ReturnAcceptRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnCancelRequest as ReturnCancelRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnCreateRequest as ReturnCreateRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnExchangeRequest as ReturnExchangeRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnRejectRequest as ReturnRejectRequest,
)
from salesia.modules.finanzas.application.contracts.devoluciones_sin_comprobante import (
    ReturnWithoutReceiptRequest as ReturnWithoutReceiptRequest,
)
from salesia.modules.finanzas.application.contracts.exchange_rate import (
    CurrencyConvertRequest as CurrencyConvertRequest,
)
from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    IntegrationCreateRequest as IntegrationCreateRequest,
)
from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    PaymentIntentConfirmRequest as PaymentIntentConfirmRequest,
)
from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    PaymentIntentCreateRequest as PaymentIntentCreateRequest,
)
from salesia.modules.finanzas.application.contracts.integraciones_pago import (
    PaymentIntentSyncRequest as PaymentIntentSyncRequest,
)
from salesia.modules.finanzas.application.contracts.medios_pago import (
    PaymentMethodCreateRequest as PaymentMethodCreateRequest,
)
from salesia.modules.finanzas.application.contracts.medios_pago import (
    PaymentMethodUpdateRequest as PaymentMethodUpdateRequest,
)
from salesia.modules.finanzas.application.contracts.pagos import PaymentAllocationRequest as PaymentAllocationRequest
from salesia.modules.finanzas.application.contracts.pagos import PaymentCreateRequest as PaymentCreateRequest
from salesia.modules.finanzas.application.contracts.pagos import PaymentDisputeRequest as PaymentDisputeRequest
from salesia.modules.finanzas.application.contracts.pagos import PaymentReversalRequest as PaymentReversalRequest
from salesia.modules.finanzas.application.contracts.pagos import ProofOfTransferRequest as ProofOfTransferRequest
from salesia.modules.finanzas.application.contracts.pagos import (
    ProofOfTransferVerifyRequest as ProofOfTransferVerifyRequest,
)
from salesia.modules.finanzas.application.contracts.pagos_elegibles import (
    StoreCreditApplyRequest as StoreCreditApplyRequest,
)
from salesia.modules.finanzas.application.contracts.reembolsos import RefundCreateRequest as RefundCreateRequest
from salesia.modules.finanzas.application.contracts.reembolsos import (
    RefundStatusUpdateRequest as RefundStatusUpdateRequest,
)
from salesia.modules.finanzas.presentation.routes import (
    caja_arqueo_relevo,
    caja_sesiones_movimientos,
    conciliaciones,
    credito_tienda,
    cuentas_cobrar,
    devoluciones_operaciones,
    devoluciones_sin_comprobante,
    disputas,
    exchange_rate,
    integraciones_pago,
    medios_pago,
    pagos,
    pagos_elegibles,
    reembolsos,
)

router = APIRouter(tags=["Finanzas y Pagos"])
router.include_router(medios_pago.router)
router.include_router(pagos.router)
router.include_router(reembolsos.router)
router.include_router(integraciones_pago.router)
router.include_router(cuentas_cobrar.router)
router.include_router(disputas.router)
router.include_router(conciliaciones.router)
router.include_router(caja_sesiones_movimientos.router)
router.include_router(caja_arqueo_relevo.router)
router.include_router(exchange_rate.router)
router.include_router(pagos_elegibles.router)
router.include_router(credito_tienda.router)
router.include_router(devoluciones_operaciones.router)
router.include_router(devoluciones_sin_comprobante.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_payment_methods",
            "create_payment_method",
            "update_payment_method",
            "create_payment",
            "list_payments",
            "get_payment",
            "allocate_payment",
            "create_refund",
            "create_payment_connection",
            "rotate_payment_connection_secret",
            "get_receivables",
            "receivable_context",
            "create_collection_activity",
            "create_payment_intent",
            "get_payment_intent",
            "confirm_payment_intent",
            "sync_payment_intent_status",
            "submit_proof_of_transfer",
            "verify_proof_of_transfer",
            "reverse_payment",
            "create_payment_dispute",
            "list_payment_disputes",
            "create_reconciliation",
            "get_reconciliation",
            "resolve_reconciliation_item",
            "open_cash_session",
            "list_cash_sessions",
            "current_cash_session",
            "get_blind_session_status",
            "submit_blind_count",
            "approve_cash_difference",
            "add_cash_session_movement",
            "close_cash_session",
            "convert_currency",
            "apply_store_credit",
            "get_customer_store_credit",
            "update_refund_status",
            "list_refunds",
            "get_refund",
            "get_credit_note",
            "list_credit_notes",
            "get_eligible_return_lines",
            "create_return",
            "list_returns",
            "get_return",
            "reject_return",
            "cancel_return",
            "accept_return",
            "exchange_return",
            "create_return_without_receipt",
        )
    )
}
router.routes.sort(key=lambda route: _router_order.get(route.name, len(_router_order)))
from salesia.modules.finanzas.presentation.routes.obligaciones import router as obligations_router

router.include_router(obligations_router)
list_payment_methods = medios_pago.list_payment_methods
create_payment_method = medios_pago.create_payment_method
update_payment_method = medios_pago.update_payment_method
create_payment = pagos.create_payment
list_payments = pagos.list_payments
get_payment = pagos.get_payment
allocate_payment = pagos.allocate_payment
create_refund = reembolsos.create_refund
create_payment_connection = integraciones_pago.create_payment_connection
rotate_payment_connection_secret = integraciones_pago.rotate_payment_connection_secret
get_receivables = cuentas_cobrar.get_receivables
receivable_context = cuentas_cobrar.receivable_context
create_collection_activity = cuentas_cobrar.create_collection_activity
create_payment_intent = integraciones_pago.create_payment_intent
get_payment_intent = integraciones_pago.get_payment_intent
confirm_payment_intent = integraciones_pago.confirm_payment_intent
sync_payment_intent_status = integraciones_pago.sync_payment_intent_status
submit_proof_of_transfer = pagos.submit_proof_of_transfer
verify_proof_of_transfer = pagos.verify_proof_of_transfer
reverse_payment = pagos.reverse_payment
create_payment_dispute = pagos.create_payment_dispute
list_payment_disputes = disputas.list_payment_disputes
create_reconciliation = conciliaciones.create_reconciliation
get_reconciliation = conciliaciones.get_reconciliation
resolve_reconciliation_item = conciliaciones.resolve_reconciliation_item
open_cash_session = caja_sesiones_movimientos.open_cash_session
list_cash_sessions = caja_sesiones_movimientos.list_cash_sessions
current_cash_session = caja_sesiones_movimientos.current_cash_session
get_blind_session_status = caja_arqueo_relevo.get_blind_session_status
submit_blind_count = caja_arqueo_relevo.submit_blind_count
approve_cash_difference = caja_arqueo_relevo.approve_cash_difference
add_cash_session_movement = caja_sesiones_movimientos.add_cash_session_movement
close_cash_session = caja_arqueo_relevo.close_cash_session
convert_currency = exchange_rate.convert_currency
apply_store_credit = pagos_elegibles.apply_store_credit
get_customer_store_credit = credito_tienda.get_customer_store_credit
update_refund_status = reembolsos.update_refund_status
list_refunds = reembolsos.list_refunds
get_refund = reembolsos.get_refund
get_credit_note = devoluciones_operaciones.get_credit_note
list_credit_notes = devoluciones_operaciones.list_credit_notes
get_eligible_return_lines = devoluciones_operaciones.get_eligible_return_lines
create_return = devoluciones_operaciones.create_return
list_returns = devoluciones_operaciones.list_returns
get_return = devoluciones_operaciones.get_return
reject_return = devoluciones_operaciones.reject_return
cancel_return = devoluciones_operaciones.cancel_return
accept_return = devoluciones_operaciones.accept_return
exchange_return = devoluciones_operaciones.exchange_return
create_return_without_receipt = devoluciones_sin_comprobante.create_return_without_receipt

webhook_router = APIRouter(tags=["Webhooks de Pagos"])
webhook_router.include_router(integraciones_pago.webhook_router)

_webhook_router_order = {name: index for index, name in enumerate(("payment_webhook",))}
webhook_router.routes.sort(key=lambda route: _webhook_router_order.get(route.name, len(_router_order)))
payment_webhook = integraciones_pago.payment_webhook

from salesia.modules.finanzas.presentation.routes.cuotas_cobranza import router as receivable_schedules_router

router.include_router(receivable_schedules_router)

from salesia.modules.finanzas.presentation.routes.custodia import router as cash_custody_router

router.include_router(cash_custody_router)

from salesia.modules.finanzas.presentation.routes.caja_chica import router as petty_cash_router

router.include_router(petty_cash_router)

from salesia.modules.finanzas.presentation.routes.prevision_efectivo import router as cash_forecast_router

router.include_router(cash_forecast_router)

from salesia.modules.finanzas.presentation.routes.politicas_devolucion import router as return_policy_router

router.include_router(return_policy_router)

from salesia.modules.finanzas.presentation.routes.liquidaciones_devolucion import router as return_settlement_router

router.include_router(return_settlement_router)
