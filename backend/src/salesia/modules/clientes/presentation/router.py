from fastapi import APIRouter

from salesia.modules.clientes.presentation.routes import (
    actividades,
    asignaciones,
    calidad,
    condiciones,
    consulta,
    contactos,
    creacion,
    direcciones,
    duplicados,
    edicion,
    estado_cuenta,
    estados,
    exportacion,
    fidelizacion,
    fusion,
    historial,
    importacion,
    notas,
    oportunidades,
    portal,
    segmentos,
)

router = APIRouter(tags=["Clientes y CRM"])

crm_router = APIRouter(tags=["CRM Avanzado"])

customer_portal_router = APIRouter(tags=["Portal de Cliente"])

router.include_router(consulta.router)

router.include_router(creacion.router)

router.include_router(edicion.router)

router.include_router(estados.router)

router.include_router(duplicados.router)

router.include_router(fusion.router)

router.include_router(contactos.router)

router.include_router(direcciones.router)

router.include_router(estado_cuenta.router)

router.include_router(historial.router)

router.include_router(condiciones.router)

router.include_router(asignaciones.router)

router.include_router(segmentos.router)

router.include_router(notas.router)

router.include_router(importacion.router)

router.include_router(exportacion.router)

router.include_router(calidad.router)

crm_router.include_router(oportunidades.crm_router)

router.include_router(oportunidades.router)

crm_router.include_router(actividades.crm_router)

router.include_router(actividades.router)

router.include_router(fidelizacion.router)

customer_portal_router.include_router(portal.customer_portal_router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_customers",
            "detect_duplicates",
            "check_duplicate_candidate",
            "validate_fiscal_identity",
            "create_customer",
            "ensure_walk_in_customer",
            "get_customer",
            "update_customer",
            "archive_customer",
            "restore_customer",
            "preview_customer_merge",
            "merge_customers",
            "list_customer_contacts",
            "create_customer_contact",
            "delete_customer_contact",
            "list_customer_addresses",
            "create_customer_address",
            "delete_customer_address",
            "get_customer_statement",
            "get_customer_history",
            "get_customer_commercial_terms",
            "update_customer_commercial_terms",
            "check_customer_credit",
            "get_customer_assignment",
            "update_customer_assignment",
            "list_customer_segments",
            "create_customer_segment",
            "evaluate_customer_segments",
            "list_customer_notes",
            "create_customer_note",
            "delete_customer_note",
            "update_customer_status",
            "get_import_template",
            "import_customers",
            "export_customers",
            "get_customer_quality",
            "list_customer_opportunities",
            "create_customer_opportunity",
            "list_customer_activities",
            "create_customer_activity",
            "get_customer_loyalty",
            "accrue_loyalty_points",
            "reverse_loyalty_points",
        )
    )
}

router.routes.sort(key=lambda route: _router_order.get(route.name, len(_router_order)))

_crm_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_all_crm_opportunities",
            "update_crm_opportunity",
            "convert_opportunity_to_quote",
            "list_crm_activities",
            "update_crm_activity",
        )
    )
}

crm_router.routes.sort(key=lambda route: _crm_router_order[route.name])

_customer_portal_router_order = {
    name: index
    for index, name in enumerate(
        (
            "portal_get_my_profile",
            "portal_get_my_invoices",
            "portal_get_my_orders",
            "portal_get_my_statement",
        )
    )
}

customer_portal_router.routes.sort(key=lambda route: _customer_portal_router_order[route.name])
