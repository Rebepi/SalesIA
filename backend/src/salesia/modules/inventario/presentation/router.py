from fastapi import APIRouter

from salesia.modules.inventario.application.auxiliares.build_inventory_row import (
    build_inventory_row as build_inventory_row,
)
from salesia.modules.inventario.application.auxiliares.purchase_line_values import (
    purchase_line_values as purchase_line_values,
)
from salesia.modules.inventario.application.auxiliares.validate_carrier_url import (
    validate_carrier_url as validate_carrier_url,
)
from salesia.modules.inventario.application.contracts.adjustments import AdjustmentRequest as AdjustmentRequest
from salesia.modules.inventario.application.contracts.compras_costos_conciliacion import (
    ThreeWayMatchRequest as ThreeWayMatchRequest,
)
from salesia.modules.inventario.application.contracts.comunes import CountEntry as CountEntry
from salesia.modules.inventario.application.contracts.comunes import InvoiceMatchLine as InvoiceMatchLine
from salesia.modules.inventario.application.contracts.comunes import LandedChargeItem as LandedChargeItem
from salesia.modules.inventario.application.contracts.comunes import (
    PurchaseOrderCreateRequest as PurchaseOrderCreateRequest,
)
from salesia.modules.inventario.application.contracts.comunes import (
    PurchaseOrderUpdateRequest as PurchaseOrderUpdateRequest,
)
from salesia.modules.inventario.application.contracts.comunes import (
    PurchaseReturnCreateRequest as PurchaseReturnCreateRequest,
)
from salesia.modules.inventario.application.contracts.comunes import PurchaseReturnItem as PurchaseReturnItem
from salesia.modules.inventario.application.contracts.comunes import PurchaseStockLine as PurchaseStockLine
from salesia.modules.inventario.application.contracts.comunes import (
    ReturnAcceptInspectionItem as ReturnAcceptInspectionItem,
)
from salesia.modules.inventario.application.contracts.comunes import ReturnLine as ReturnLine
from salesia.modules.inventario.application.contracts.comunes import StockLine as StockLine
from salesia.modules.inventario.application.contracts.comunes import (
    ThreeWayMatchResolveRequest as ThreeWayMatchResolveRequest,
)
from salesia.modules.inventario.application.contracts.comunes import TransferReceiveItem as TransferReceiveItem
from salesia.modules.inventario.application.contracts.conciliacion import (
    ReconcileRepairRequest as ReconcileRepairRequest,
)
from salesia.modules.inventario.application.contracts.conciliacion import ReconcileRequest as ReconcileRequest
from salesia.modules.inventario.application.contracts.conteos import CountEntriesRequest as CountEntriesRequest
from salesia.modules.inventario.application.contracts.conteos import PhysicalCountRequest as PhysicalCountRequest
from salesia.modules.inventario.application.contracts.cuarentena import (
    QuarantineClassifyRequest as QuarantineClassifyRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ExchangeCreateRequest as ExchangeCreateRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ReturnAcceptRequest as ReturnAcceptRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ReturnCancelRequest as ReturnCancelRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ReturnCreateRequest as ReturnCreateRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ReturnRejectRequest as ReturnRejectRequest,
)
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ReturnWithoutReceiptRequest as ReturnWithoutReceiptRequest,
)
from salesia.modules.inventario.application.contracts.entregas_incidentes import (
    DeliveryIncidentCreateRequest as DeliveryIncidentCreateRequest,
)
from salesia.modules.inventario.application.contracts.entregas_incidentes import (
    ProofOfDeliveryRequest as ProofOfDeliveryRequest,
)
from salesia.modules.inventario.application.contracts.entregas_incidentes import (
    TrackingEventCreateRequest as TrackingEventCreateRequest,
)
from salesia.modules.inventario.application.contracts.entregas_operaciones import (
    DeliveryCompleteRequest as DeliveryCompleteRequest,
)
from salesia.modules.inventario.application.contracts.entregas_operaciones import (
    DeliveryCreateRequest as DeliveryCreateRequest,
)
from salesia.modules.inventario.application.contracts.entregas_operaciones import (
    DeliveryInterceptRequest as DeliveryInterceptRequest,
)
from salesia.modules.inventario.application.contracts.lotes_series import LotCreateRequest as LotCreateRequest
from salesia.modules.inventario.application.contracts.lotes_series import SerialCreateRequest as SerialCreateRequest
from salesia.modules.inventario.application.contracts.lotes_series import SerialSellRequest as SerialSellRequest
from salesia.modules.inventario.application.contracts.preparacion import PickingCreateRequest as PickingCreateRequest
from salesia.modules.inventario.application.contracts.preparacion import PickingVerifyRequest as PickingVerifyRequest
from salesia.modules.inventario.application.contracts.proveedores import SupplierCreateRequest as SupplierCreateRequest
from salesia.modules.inventario.application.contracts.proveedores import SupplierUpdateRequest as SupplierUpdateRequest
from salesia.modules.inventario.application.contracts.recepciones import LandedCostRequest as LandedCostRequest
from salesia.modules.inventario.application.contracts.reglas import StockRuleRequest as StockRuleRequest
from salesia.modules.inventario.application.contracts.requisiciones_reposicion import (
    PurchaseRequisitionCreateRequest as PurchaseRequisitionCreateRequest,
)
from salesia.modules.inventario.application.contracts.reservas import (
    ReservationCreateRequest as ReservationCreateRequest,
)
from salesia.modules.inventario.application.contracts.reservas import (
    ReservationReleaseRequest as ReservationReleaseRequest,
)
from salesia.modules.inventario.application.contracts.transferencias import (
    TransferCreateRequest as TransferCreateRequest,
)
from salesia.modules.inventario.application.contracts.transferencias import (
    TransferReceiveRequest as TransferReceiveRequest,
)
from salesia.modules.inventario.application.contracts.ubicaciones import LocationCreateRequest as LocationCreateRequest
from salesia.modules.inventario.application.contracts.ubicaciones import (
    LocationTransferRequest as LocationTransferRequest,
)
from salesia.modules.inventario.application.contracts.ubicaciones import LocationUpdateRequest as LocationUpdateRequest
from salesia.modules.inventario.application.contracts.valorizacion import ValuationRequest as ValuationRequest
from salesia.modules.inventario.presentation.routes import (
    adjustments,
    alertas,
    compras_costos_conciliacion,
    conciliacion,
    conteos,
    cuarentena,
    devoluciones_consulta,
    devoluciones_operaciones,
    entregas_incidentes,
    entregas_operaciones,
    existencias,
    lotes_series,
    movimientos,
    ordenes_compra,
    preparacion,
    proveedores,
    recepciones,
    reglas,
    requisiciones_reposicion,
    reservas,
    transferencias,
    ubicaciones,
    valorizacion,
)

router = APIRouter(tags=["Inventario y Cadena de Suministro"])
router.include_router(existencias.router)
router.include_router(movimientos.router)
router.include_router(adjustments.router)
router.include_router(transferencias.router)
router.include_router(conteos.router)
router.include_router(ubicaciones.router)
router.include_router(lotes_series.router)
router.include_router(reglas.router)
router.include_router(alertas.router)
router.include_router(reservas.router)
router.include_router(cuarentena.router)
router.include_router(conciliacion.router)
router.include_router(preparacion.router)
router.include_router(valorizacion.router)
router.include_router(proveedores.router)
router.include_router(requisiciones_reposicion.router)
router.include_router(ordenes_compra.router)
router.include_router(recepciones.router)
router.include_router(compras_costos_conciliacion.router)
router.include_router(entregas_operaciones.router)
router.include_router(entregas_incidentes.router)
router.include_router(devoluciones_consulta.router)
router.include_router(devoluciones_operaciones.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_inventory",
            "list_movements",
            "create_adjustment",
            "list_transfers",
            "create_transfer",
            "dispatch_transfer",
            "receive_transfer",
            "cancel_transfer",
            "list_counts",
            "create_stock_count",
            "update_count_entries",
            "approve_stock_count",
            "create_location",
            "list_locations",
            "update_location",
            "transfer_location_stock",
            "create_lot",
            "list_lots",
            "lot_trace",
            "serial_trace",
            "block_lot",
            "create_serial",
            "list_serials",
            "sell_serial",
            "configure_stock_rule",
            "list_stock_rules",
            "deactivate_stock_rule",
            "list_alerts",
            "trigger_alert_recalculation",
            "resolve_alert_endpoint",
            "create_reservation_endpoint",
            "release_reservation_endpoint",
            "list_quarantine_items",
            "classify_quarantine_item",
            "run_stock_reconciliation",
            "repair_stock_reconciliation",
            "create_picking_list",
            "verify_picking_item",
            "complete_picking_list",
            "get_valuation_setting",
            "set_valuation_setting",
            "list_suppliers",
            "create_supplier",
            "get_supplier",
            "update_supplier",
            "get_supplier_performance",
            "create_purchase_requisition",
            "list_purchase_requisitions",
            "approve_purchase_requisition",
            "suggest_requisition_from_stock",
            "get_replenishment_suggestions",
            "supplier_price_history",
            "create_purchase_order",
            "list_purchase_orders",
            "get_purchase_order",
            "approve_purchase_order",
            "update_purchase_order",
            "get_purchase_order_timeline",
            "purchase_receiving_context",
            "create_goods_receipt",
            "add_landed_cost",
            "create_purchase_return",
            "process_three_way_match",
            "resolve_three_way_match",
            "create_delivery",
            "list_deliveries",
            "get_delivery",
            "dispatch_delivery",
            "record_tracking_event",
            "record_proof_of_delivery",
            "get_proof_of_delivery",
            "record_delivery_incident",
            "cancel_delivery",
            "intercept_delivery",
            "complete_delivery",
            "get_sale_return_eligibility",
            "list_returns",
            "get_return",
            "create_return",
            "accept_return",
            "reject_return",
            "cancel_return",
            "exchange_return",
            "create_return_without_receipt",
        )
    )
}
router.routes.sort(key=lambda route: _router_order.get(route.name, len(_router_order)))
list_inventory = existencias.list_inventory
list_movements = movimientos.list_movements
create_adjustment = adjustments.create_adjustment
list_transfers = transferencias.list_transfers
create_transfer = transferencias.create_transfer
dispatch_transfer = transferencias.dispatch_transfer
receive_transfer = transferencias.receive_transfer
cancel_transfer = transferencias.cancel_transfer
list_counts = conteos.list_counts
create_stock_count = conteos.create_stock_count
update_count_entries = conteos.update_count_entries
approve_stock_count = conteos.approve_stock_count
create_location = ubicaciones.create_location
list_locations = ubicaciones.list_locations
update_location = ubicaciones.update_location
transfer_location_stock = ubicaciones.transfer_location_stock
create_lot = lotes_series.create_lot
list_lots = lotes_series.list_lots
lot_trace = lotes_series.lot_trace
serial_trace = lotes_series.serial_trace
block_lot = lotes_series.block_lot
create_serial = lotes_series.create_serial
list_serials = lotes_series.list_serials
sell_serial = lotes_series.sell_serial
configure_stock_rule = reglas.configure_stock_rule
list_stock_rules = reglas.list_stock_rules
deactivate_stock_rule = reglas.deactivate_stock_rule
list_alerts = alertas.list_alerts
trigger_alert_recalculation = alertas.trigger_alert_recalculation
resolve_alert_endpoint = alertas.resolve_alert_endpoint
create_reservation_endpoint = reservas.create_reservation_endpoint
release_reservation_endpoint = reservas.release_reservation_endpoint
list_quarantine_items = cuarentena.list_quarantine_items
classify_quarantine_item = cuarentena.classify_quarantine_item
run_stock_reconciliation = conciliacion.run_stock_reconciliation
repair_stock_reconciliation = conciliacion.repair_stock_reconciliation
create_picking_list = preparacion.create_picking_list
verify_picking_item = preparacion.verify_picking_item
complete_picking_list = preparacion.complete_picking_list
get_valuation_setting = valorizacion.get_valuation_setting
set_valuation_setting = valorizacion.set_valuation_setting
list_suppliers = proveedores.list_suppliers
create_supplier = proveedores.create_supplier
get_supplier = proveedores.get_supplier
update_supplier = proveedores.update_supplier
get_supplier_performance = proveedores.get_supplier_performance
create_purchase_requisition = requisiciones_reposicion.create_purchase_requisition
list_purchase_requisitions = requisiciones_reposicion.list_purchase_requisitions
approve_purchase_requisition = requisiciones_reposicion.approve_purchase_requisition
suggest_requisition_from_stock = requisiciones_reposicion.suggest_requisition_from_stock
get_replenishment_suggestions = requisiciones_reposicion.get_replenishment_suggestions
supplier_price_history = proveedores.supplier_price_history
create_purchase_order = ordenes_compra.create_purchase_order
list_purchase_orders = ordenes_compra.list_purchase_orders
get_purchase_order = ordenes_compra.get_purchase_order
approve_purchase_order = ordenes_compra.approve_purchase_order
update_purchase_order = ordenes_compra.update_purchase_order
get_purchase_order_timeline = ordenes_compra.get_purchase_order_timeline
purchase_receiving_context = ordenes_compra.purchase_receiving_context
create_goods_receipt = recepciones.create_goods_receipt
add_landed_cost = recepciones.add_landed_cost
create_purchase_return = ordenes_compra.create_purchase_return
process_three_way_match = compras_costos_conciliacion.process_three_way_match
resolve_three_way_match = ordenes_compra.resolve_three_way_match
create_delivery = entregas_operaciones.create_delivery
list_deliveries = entregas_operaciones.list_deliveries
get_delivery = entregas_operaciones.get_delivery
dispatch_delivery = entregas_operaciones.dispatch_delivery
record_tracking_event = entregas_incidentes.record_tracking_event
record_proof_of_delivery = entregas_incidentes.record_proof_of_delivery
get_proof_of_delivery = entregas_incidentes.get_proof_of_delivery
record_delivery_incident = entregas_incidentes.record_delivery_incident
cancel_delivery = entregas_operaciones.cancel_delivery
intercept_delivery = entregas_operaciones.intercept_delivery
complete_delivery = entregas_operaciones.complete_delivery
get_sale_return_eligibility = devoluciones_consulta.get_sale_return_eligibility
list_returns = devoluciones_consulta.list_returns
get_return = devoluciones_consulta.get_return
create_return = devoluciones_operaciones.create_return
accept_return = devoluciones_operaciones.accept_return
reject_return = devoluciones_operaciones.reject_return
cancel_return = devoluciones_operaciones.cancel_return
exchange_return = devoluciones_operaciones.exchange_return
create_return_without_receipt = devoluciones_operaciones.create_return_without_receipt

from salesia.modules.inventario.presentation.routes.catalogo_proveedor import router as supplier_catalog_router

router.include_router(supplier_catalog_router)

from salesia.modules.inventario.presentation.routes.ofertas_proveedores import router as supplier_offers_router

router.include_router(supplier_offers_router)

from salesia.modules.inventario.presentation.routes.acuerdos_compra import router as purchase_agreements_router

router.include_router(purchase_agreements_router)

from salesia.modules.inventario.presentation.routes.homologacion_proveedor import router as supplier_qualification_router

router.include_router(supplier_qualification_router)

from salesia.modules.inventario.presentation.routes.reclamos_proveedor import router as supplier_claims_router

router.include_router(supplier_claims_router)

from salesia.modules.inventario.presentation.routes.recorridos import router as delivery_routes_router

router.include_router(delivery_routes_router)

from salesia.modules.inventario.presentation.routes.entregas_parciales import router as delivery_results_router

router.include_router(delivery_results_router)

from salesia.modules.inventario.presentation.routes.ventanas_entrega import router as delivery_windows_router

router.include_router(delivery_windows_router)
