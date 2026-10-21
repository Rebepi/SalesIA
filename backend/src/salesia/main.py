from contextlib import asynccontextmanager
from sqlalchemy import text
from salesia.shared.infrastructure.tenant_scope import current_company
from fastapi import FastAPI, Depends
from salesia.modules.seguridad.presentation.policy import authorize_business_request
from fastapi.middleware.cors import CORSMiddleware
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import engine
from salesia.shared.infrastructure.errors import register_exception_handlers
from uuid import uuid4
from salesia.modules.estado.presentation.router import router as health_router
from salesia.modules.seguridad.presentation.router import router as auth_router
from salesia.modules.organizacion.presentation.router import router as organization_router
from salesia.modules.clientes.presentation.router import (
    router as customers_router,
    crm_router,
    customer_portal_router
)
from salesia.modules.catalogo.presentation.router import router as catalog_router
from salesia.modules.pedidos.presentation.router import router as orders_router
from salesia.modules.pedidos.presentation.router import quotation_portal_router
from salesia.modules.finanzas.presentation.router import router as finance_router
from salesia.modules.finanzas.presentation.router import webhook_router as payment_webhook_router
from salesia.modules.inventario.presentation.router import router as inventory_router
from salesia.modules.analitica.presentation.router import router as analytics_router
from salesia.modules.operaciones.presentation.router import router as operations_router
from salesia.modules.operaciones.presentation.selector_options import router as selector_options_router
from salesia.modules.ventas.presentation.router import router as sales_router
from salesia.modules.auditoria.presentation.router import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment == "production":
        async with engine.connect() as connection:
            unsafe = await connection.scalar(text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"))
            owns = await connection.scalar(text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tableowner = current_user"))
            if unsafe or owns:
                raise RuntimeError("El rol de aplicación no puede ser superusuario, BYPASSRLS ni propietario de tablas.")
    yield
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Plataforma empresarial de gestión comercial, inventario y analítica estadística",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_and_correlation_middleware(request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or uuid4().hex
        token = current_company.set(None)
        try:
            response = await call_next(request)
        finally:
            current_company.reset(token)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    register_exception_handlers(app)

    api_prefix = "/api/v1"
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(organization_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(customers_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(catalog_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(orders_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(quotation_portal_router, prefix=api_prefix)
    app.include_router(finance_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(payment_webhook_router, prefix=api_prefix)
    app.include_router(inventory_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(analytics_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(selector_options_router, prefix=api_prefix)
    app.include_router(operations_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(sales_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(audit_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(crm_router, prefix=api_prefix, dependencies=[Depends(authorize_business_request)])
    app.include_router(customer_portal_router, prefix=api_prefix)

    @app.get("/", tags=["Raíz"])
    async def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs": "/docs",
            "api_prefix": api_prefix
        }

    return app


app = create_application()
