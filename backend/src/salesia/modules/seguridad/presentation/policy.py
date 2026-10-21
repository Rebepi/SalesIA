from fastapi import Depends, Request
from sqlalchemy.orm import Session
from salesia.shared.infrastructure.database import get_db

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.errors import DomainForbiddenException


def authorize_business_request(request: Request, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.permissions and user.role != "platform_admin":
        raise DomainForbiddenException("Denegación por defecto: no tiene permisos asignados.")
    module = request.scope["route"].endpoint.__module__.split(".")[2]
    write = request.method not in ("GET", "HEAD", "OPTIONS")
    path = request.url.path
    permissions = {
        "clientes": ("customers:read", "customers:write"),
        "catalogo": ("products:read", "products:write"),
        "ventas": ("sales:read", "sales:write"),
        "finanzas": ("payments:read", "payments:write"),
        "inventario": ("inventory:read", "inventory:write"),
        "pedidos": ("quotations:read", "quotations:write"),
        "analitica": ("analytics:dataset:read", "analytics:calculate"),
        "auditoria": ("audit:logs:read", "audit:logs:export"),
        "organizacion": ("organization:manage", "organization:manage"),
        "operaciones": ("operations:manage", "operations:manage"),
    }
    required = permissions.get(module, ("platform:manage", "platform:manage"))[int(write)]
    if "/insights" in path:
        required = (
            "analytics:dataset:read"
            if "analytics:dataset:read" in user.permissions
            else ("sales:read" if "sales:read" in user.permissions else "products:read")
        )
    if "/prices/preview" in path or "/units/convert" in path or "/coupons/validate" in path:
        required = "products:read" if "products:read" in user.permissions else "sales:read"
    if "/warranty-" in path or "/warranty/" in path or "/eligible-warranty-sales" in path:
        required = "sales:write" if write else "sales:read"
    if "/orders" in path:
        required = "sales:write" if write else "sales:read"
    if any(segment in path for segment in ("/cash-custody", "/petty-cash", "/cash-forecast")):
        required = "cash:register:manage"
    if "/return-policy" in path:
        required = "organization:manage" if write else "sales:read"
    if "/store-credit" in path:
        required = ("sales:read" if path.endswith("/sales") else "customers:read") if not write else "sales:write"
        if path.endswith("/identify-currency"):
            required = "organization:manage" if "organization:manage" in user.permissions else "approvals:manage"
    if "/apply-store-credit" in path:
        required = "sales:write"
    if "/reserve-store-credit" in path or "/customer-credit-reservations/" in path:
        required = "sales:write" if "sales:write" in user.permissions else "payments:write"
    if "/credit-conversions" in path:
        required = "payments:write" if write else "customers:read"
    if "/cash-sessions" in path:
        if "/blind-" in path:
            required = "sales:read" if "sales:read" in user.permissions else "cash:register:manage"
        else:
            required = "cash:register:manage"
    if any(segment in path for segment in ("/purchases", "/suppliers", "/supplier-products", "/purchase-invoice-matches", "/purchase-requisitions", "/supplier-offers", "/purchase-agreements")):
        required = (
            "purchases:write"
            if write
            else ("purchases:read" if "purchases:read" in user.permissions else "inventory:read")
        )
    if "/purchase-orders" in path:
        required = (
            "purchases:write"
            if write
            else ("purchases:read" if "purchases:read" in user.permissions else "inventory:read")
        )
    if "/supplier-claim-sources" in path:
        required = "purchases:read"
    if "/supplier-claims" in path:
        required = ("payments:write" if path.endswith("/credits") else "purchases:write") if write else ("purchases:read" if "purchases:read" in user.permissions else "payments:read")
    if "/goods-receipts" in path:
        required = (
            ("purchases:write" if "purchases:write" in user.permissions else "inventory:write")
            if write
            else ("purchases:read" if "purchases:read" in user.permissions else "inventory:read")
        )
    if any(segment in path for segment in ("/delivery-routes", "/delivery-route-options", "/delivery-vehicles", "/delivery-windows", "/delivery-window-options")):
        required = "inventory:write" if write else ("inventory:read" if "inventory:read" in user.permissions else "sales:read")
    if "/deliveries" in path:
        required = (
            ("sales:write" if "sales:write" in user.permissions else "inventory:write")
            if write
            else ("sales:read" if "sales:read" in user.permissions else "inventory:read")
        )
    if any(segment in path for segment in ("/reports", "/report-runs", "/report-schedules")):
        required = "reports:export" if write else "reports:read"
    if "/organization/operating-calendar" in path and (not write and not path.endswith("/history") or path.endswith("/calculate")):
        required = None
    if path == "/api/v1/organization/operating-profile" and not write:
        required = None
    if "/sales/performance-targets" in path:
        required = "organization:manage" if write or "organization:manage" in user.permissions else "sales:read"
    if "/sales/commission" in path:
        required = "organization:manage" if write or "/commission-policy" in path or "/commission-coverages" in path else ("organization:manage" if "organization:manage" in user.permissions else "sales:read")
        if path.endswith("/observations"):
            required = "organization:manage" if "organization:manage" in user.permissions else "sales:read"
    if "/sales/export" in path:
        required = "sales:export"
    if "/customers/export" in path:
        required = "reports:export" if "reports:export" in user.permissions else "customers:read"
    if "/convert-to-quote" in path:
        required = "quotations:write" if "quotations:write" in user.permissions else "customers:write"
    if not write and path in ("/api/v1/companies/current", "/api/v1/branches", "/api/v1/warehouses"):
        required = None
    if any(segment in path for segment in ("/customers/",)) and path.endswith("/archive"):
        required = "customers:archive" if "customers:archive" in user.permissions else "customers:write"
    if any(segment in path for segment in ("/sales/",)) and path.endswith("/confirm"):
        required = "sales:confirm"
    if any(segment in path for segment in ("/sales/",)) and any(path.endswith(s) for s in ("/cancel", "/annul")):
        required = "sales:cancel"
    if any(segment in path for segment in ("/operations/backup", "/operations/backups", "/operations/restore")):
        required = "platform:manage"
    elif any(
        segment in path
        for segment in (
            "/maintenance",
            "/feature-flags",
            "/degradation",
            "/system/",
            "/metrics",
            "/operations/settings",
        )
    ):
        required = "operations:manage"
    elif any(
        segment in path
        for segment in (
            "/notifications",
            "/events/stream",
            "/search",
            "/collaboration",
            "/help",
            "/business/",
            "/attachments",
            "/imports",
            "/jobs",
        )
    ):
        required = None
    elif module == "operaciones" and not write:
        required = None
    if required and required not in user.permissions:
        raise DomainForbiddenException(f"Falta el permiso {required}.")
    if write:
        db.info["period_actor"] = {"id": user.user_id, "email": user.email}
        db.info["period_request"] = {"method": request.method, "path": path, "parameters": {key: str(value) for key, value in request.path_params.items()}}
        if module in ("organizacion", "pedidos", "catalogo"):
            from sqlalchemy import select
            from salesia.shared.infrastructure.models import CompanyModel
            db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
        if module in ("ventas", "finanzas", "inventario"):
            from salesia.modules.organizacion.application.periodos import business_date, request_period_modules, require_open_period
            db.info["period_modules"] = request_period_modules(module, path)
            require_open_period(db, user.company_id, business_date(db, user.company_id))
        from salesia.modules.organizacion.application.perfil_operativo import area_for_path, require_area
        operating_area = area_for_path(path)
        if operating_area:
            require_area(db, user.company_id, operating_area)
        from salesia.modules.operaciones.application.campos import validate_required_fields
        actions = {"confirm": "confirmed", "approve": "approved", "accept": "accepted", "dispatch": "dispatched", "complete": "completed", "submit": "pending", "close": "closed"}
        action = path.rstrip("/").split("/")[-1]
        state = actions.get(action)
        parameters = request.path_params
        kind = None
        identifier = None
        for parameter, resource in (("sale_id", "sale"), ("quotation_id", "quotation"), ("order_id", "purchase_order" if "purchase-orders" in path else "order"), ("expense_id", "expense"), ("payable_id", "payable"), ("return_id", "return")):
            if parameter in parameters:
                kind, identifier = resource, parameters[parameter]
                break
        if state and kind and identifier:
            validate_required_fields(db, user.company_id, kind, identifier, state)
            from salesia.modules.operaciones.application.politicas_aprobacion import enforce_policies
            enforce_policies(db, user, kind, identifier, action)
    return user
