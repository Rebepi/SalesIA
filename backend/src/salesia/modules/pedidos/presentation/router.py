from fastapi import APIRouter

from salesia.modules.pedidos.application.auxiliares.add_history import add_history as add_history
from salesia.modules.pedidos.application.auxiliares.audit import audit as audit
from salesia.modules.pedidos.application.auxiliares.build_order import build_order as build_order
from salesia.modules.pedidos.application.auxiliares.emit import emit as emit
from salesia.modules.pedidos.application.auxiliares.locked_order import locked_order as locked_order
from salesia.modules.pedidos.application.auxiliares.money import money as money
from salesia.modules.pedidos.application.auxiliares.now import now as now
from salesia.modules.pedidos.application.auxiliares.order_response import order_response as order_response
from salesia.modules.pedidos.application.auxiliares.price_lines import price_lines as price_lines
from salesia.modules.pedidos.application.auxiliares.public_quotation import public_quotation as public_quotation
from salesia.modules.pedidos.application.auxiliares.quotation_pdf import quotation_pdf as quotation_pdf
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response as quotation_response
from salesia.modules.pedidos.application.auxiliares.validate_references import (
    validate_references as validate_references,
)
from salesia.modules.pedidos.application.contracts.comunes import CancelItemRequest as CancelItemRequest
from salesia.modules.pedidos.application.contracts.comunes import FulfilledItem as FulfilledItem
from salesia.modules.pedidos.application.contracts.cotizaciones_ciclo_vida import (
    AcceptQuotationRequest as AcceptQuotationRequest,
)
from salesia.modules.pedidos.application.contracts.cotizaciones_ciclo_vida import (
    QuotationVersionModel as QuotationVersionModel,
)
from salesia.modules.pedidos.application.contracts.cotizaciones_documentos import (
    QuotationSendRequest as QuotationSendRequest,
)
from salesia.modules.pedidos.application.contracts.cotizaciones_registro import (
    QuotationCreateModel as QuotationCreateModel,
)
from salesia.modules.pedidos.application.contracts.pedidos_despacho import (
    OrderFulfillPartialModel as OrderFulfillPartialModel,
)
from salesia.modules.pedidos.application.contracts.pedidos_registro import ConfirmOrderRequest as ConfirmOrderRequest
from salesia.modules.pedidos.application.contracts.pedidos_registro import DocumentLine as DocumentLine
from salesia.modules.pedidos.application.contracts.pedidos_registro import OrderCancelRequest as OrderCancelRequest
from salesia.modules.pedidos.application.contracts.pedidos_registro import OrderCreateModel as OrderCreateModel
from salesia.modules.pedidos.application.contracts.pedidos_registro import PickingScanRequest as PickingScanRequest
from salesia.modules.pedidos.application.contracts.pedidos_registro import (
    UpdateOrderLinesRequest as UpdateOrderLinesRequest,
)
from salesia.modules.pedidos.application.contracts.pedidos_reservas_faltantes import (
    OrderShortageResolution as OrderShortageResolution,
)
from salesia.modules.pedidos.application.contracts.portal_cotizaciones import (
    PublicQuotationAcceptance as PublicQuotationAcceptance,
)
from salesia.modules.pedidos.presentation.routes import (
    cotizaciones_ciclo_vida,
    cotizaciones_documentos,
    cotizaciones_registro,
    pedidos_despacho,
    pedidos_registro,
    pedidos_reservas_faltantes,
    portal_cotizaciones,
)

router = APIRouter(tags=["Cotizaciones y Pedidos"])
router.include_router(cotizaciones_registro.router)
router.include_router(cotizaciones_ciclo_vida.router)
router.include_router(cotizaciones_documentos.router)
router.include_router(pedidos_registro.router)
router.include_router(pedidos_reservas_faltantes.router)
router.include_router(pedidos_despacho.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "create_quotation",
            "list_quotations",
            "get_quotation",
            "create_quotation_version",
            "accept_quotation",
            "preview_quotation",
            "download_quotation_pdf",
            "send_quotation",
            "convert_quotation_to_order",
            "list_orders",
            "get_order",
            "create_order",
            "approve_order",
            "confirm_order",
            "release_order_reservation",
            "renew_order_reservation",
            "update_order_lines",
            "fulfill_partial_order",
            "cancel_order",
            "get_order_tracking",
            "clone_order",
            "get_order_shortages",
            "resolve_order_shortage",
            "create_order_picking",
            "scan_order_picking",
            "complete_order_picking",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
create_quotation = cotizaciones_registro.create_quotation
list_quotations = cotizaciones_registro.list_quotations
get_quotation = cotizaciones_registro.get_quotation
create_quotation_version = cotizaciones_ciclo_vida.create_quotation_version
accept_quotation = cotizaciones_ciclo_vida.accept_quotation
preview_quotation = cotizaciones_documentos.preview_quotation
download_quotation_pdf = cotizaciones_documentos.download_quotation_pdf
send_quotation = cotizaciones_documentos.send_quotation
convert_quotation_to_order = cotizaciones_ciclo_vida.convert_quotation_to_order
list_orders = pedidos_registro.list_orders
get_order = pedidos_registro.get_order
create_order = pedidos_registro.create_order
approve_order = pedidos_registro.approve_order
confirm_order = pedidos_registro.confirm_order
release_order_reservation = pedidos_reservas_faltantes.release_order_reservation
renew_order_reservation = pedidos_reservas_faltantes.renew_order_reservation
update_order_lines = pedidos_registro.update_order_lines
fulfill_partial_order = pedidos_despacho.fulfill_partial_order
cancel_order = pedidos_registro.cancel_order
get_order_tracking = pedidos_registro.get_order_tracking
clone_order = pedidos_registro.clone_order
get_order_shortages = pedidos_reservas_faltantes.get_order_shortages
resolve_order_shortage = pedidos_reservas_faltantes.resolve_order_shortage
create_order_picking = pedidos_despacho.create_order_picking
scan_order_picking = pedidos_registro.scan_order_picking
complete_order_picking = pedidos_registro.complete_order_picking

quotation_portal_router = APIRouter(tags=["Portal de cotizaciones"])
quotation_portal_router.include_router(portal_cotizaciones.quotation_portal_router)

_quotation_portal_router_order = {
    name: index
    for index, name in enumerate(
        (
            "open_public_quotation",
            "accept_public_quotation",
            "public_quotation_pdf",
        )
    )
}
quotation_portal_router.routes.sort(key=lambda route: _quotation_portal_router_order[route.name])
open_public_quotation = portal_cotizaciones.open_public_quotation
accept_public_quotation = portal_cotizaciones.accept_public_quotation
public_quotation_pdf = portal_cotizaciones.public_quotation_pdf
from salesia.modules.pedidos.presentation.routes.cotizaciones_revision import router as quotation_review_router

router.include_router(quotation_review_router)
from salesia.modules.pedidos.presentation.routes.pedidos_facturacion import router as order_billing_router

router.include_router(order_billing_router)
