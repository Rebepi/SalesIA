from fastapi import APIRouter

from salesia.modules.ventas.application.auxiliares.period_bounds import period_bounds as period_bounds
from salesia.modules.ventas.application.auxiliares.prepare_lines import prepare_lines as prepare_lines
from salesia.modules.ventas.application.auxiliares.rep_detail_response import rep_detail_response as rep_detail_response
from salesia.modules.ventas.application.auxiliares.response_for import response_for as response_for
from salesia.modules.ventas.application.auxiliares.scoped_sale import scoped_sale as scoped_sale
from salesia.modules.ventas.application.auxiliares.settlement_response import settlement_response as settlement_response
from salesia.modules.ventas.application.auxiliares.validate_context import validate_context as validate_context
from salesia.modules.ventas.application.contracts.comisiones import (
    CommissionCalculateRequest as CommissionCalculateRequest,
)
from salesia.modules.ventas.application.contracts.comunes import SaleResponse as SaleResponse
from salesia.modules.ventas.application.contracts.metas import SalesTargetCreateRequest as SalesTargetCreateRequest
from salesia.modules.ventas.application.contracts.vendedores import ReassignPortfolioRequest as ReassignPortfolioRequest
from salesia.modules.ventas.application.contracts.vendedores import SalesRepCreateRequest as SalesRepCreateRequest
from salesia.modules.ventas.application.contracts.vendedores import SalesRepUpdateRequest as SalesRepUpdateRequest
from salesia.modules.ventas.application.contracts.ventas_operaciones import AnnulSaleRequest as AnnulSaleRequest
from salesia.modules.ventas.application.contracts.ventas_operaciones import ConfirmSaleRequest as ConfirmSaleRequest
from salesia.modules.ventas.application.contracts.ventas_operaciones import CorrectSaleRequest as CorrectSaleRequest
from salesia.modules.ventas.application.contracts.ventas_operaciones import (
    CreateSaleDraftRequest as CreateSaleDraftRequest,
)
from salesia.modules.ventas.application.contracts.ventas_operaciones import LineItemRequest as LineItemRequest
from salesia.modules.ventas.application.contracts.ventas_operaciones import (
    UpdateSaleDraftRequest as UpdateSaleDraftRequest,
)
from salesia.modules.ventas.presentation.routes import (
    comisiones,
    metas,
    vendedores,
    ventas_consulta,
    ventas_operaciones,
)

router = APIRouter(tags=["Ventas y Casos de Uso"])
router.include_router(ventas_operaciones.router)
router.include_router(ventas_consulta.router)
router.include_router(vendedores.router)
router.include_router(metas.router)
router.include_router(comisiones.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "create_draft",
            "get_sales_kpis",
            "list_sales",
            "export_sales",
            "lookup_sales",
            "update_draft",
            "confirm_sale",
            "annul_sale",
            "clone_sale_as_draft",
            "list_sales_reps",
            "create_sales_rep",
            "get_sales_rep",
            "update_sales_rep",
            "list_performance_targets",
            "save_performance_target",
            "create_sales_target",
            "list_sales_targets",
            "preview_sales_rep_portfolio",
            "reassign_sales_rep_portfolio",
            "commission_sale_options",
            "list_commissions",
            "get_commission_policy",
            "commission_policy_history",
            "save_commission_policy",
            "list_commission_coverages",
            "save_commission_coverage",
            "get_commission",
            "observe_commission",
            "resolve_commission_observation",
            "get_sale_participation",
            "save_sale_participation",
            "calculate_commissions",
            "approve_commission_settlement",
            "pay_commission_settlement",
            "get_sale_by_idempotency_key",
            "prevalidate_sale",
            "get_sale_document",
            "correct_sale",
            "get_sale",
        )
    )
}
router.routes.sort(key=lambda route: _router_order.get(route.name, 999))
create_draft = ventas_operaciones.create_draft
get_sales_kpis = ventas_consulta.get_sales_kpis
list_sales = ventas_consulta.list_sales
export_sales = ventas_consulta.export_sales
lookup_sales = ventas_consulta.lookup_sales
update_draft = ventas_operaciones.update_draft
confirm_sale = ventas_operaciones.confirm_sale
annul_sale = ventas_operaciones.annul_sale
clone_sale_as_draft = ventas_operaciones.clone_sale_as_draft
list_sales_reps = vendedores.list_sales_reps
create_sales_rep = vendedores.create_sales_rep
get_sales_rep = vendedores.get_sales_rep
update_sales_rep = vendedores.update_sales_rep
create_sales_target = metas.create_sales_target
list_sales_targets = metas.list_sales_targets
preview_sales_rep_portfolio = vendedores.preview_sales_rep_portfolio
reassign_sales_rep_portfolio = vendedores.reassign_sales_rep_portfolio
calculate_commissions = comisiones.calculate_commissions
approve_commission_settlement = comisiones.approve_commission_settlement
pay_commission_settlement = comisiones.pay_commission_settlement
get_sale_by_idempotency_key = ventas_consulta.get_sale_by_idempotency_key
prevalidate_sale = ventas_operaciones.prevalidate_sale
get_sale_document = ventas_operaciones.get_sale_document
correct_sale = ventas_operaciones.correct_sale
get_sale = ventas_consulta.get_sale
