from dataclasses import dataclass
from enum import Enum


class SystemRole(str, Enum):
    COMPANY_ADMIN = "company_admin"
    MANAGER = "manager"
    SALESPERSON = "salesperson"
    ANALYST = "analyst"
    WAREHOUSE = "warehouse"
    CASHIER = "cashier"
    PURCHASER = "purchaser"
    AUDITOR = "auditor"
    PLATFORM_ADMIN = "platform_admin"


class Permission(str, Enum):
    USERS_MANAGE = "users:manage"
    ORGANIZATION_MANAGE = "organization:manage"
    CUSTOMERS_READ = "customers:read"
    CUSTOMERS_WRITE = "customers:write"
    PRODUCTS_READ = "products:read"
    PRODUCTS_WRITE = "products:write"
    PRODUCTS_COST_READ = "products:cost:read"
    QUOTATIONS_READ = "quotations:read"
    QUOTATIONS_WRITE = "quotations:write"
    SALES_READ = "sales:read"
    SALES_WRITE = "sales:write"
    SALES_CANCEL = "sales:cancel"
    PAYMENTS_READ = "payments:read"
    PAYMENTS_WRITE = "payments:write"
    CASH_REGISTER_MANAGE = "cash:register:manage"
    INVENTORY_READ = "inventory:read"
    INVENTORY_WRITE = "inventory:write"
    PURCHASES_READ = "purchases:read"
    PURCHASES_WRITE = "purchases:write"
    ANALYTICS_DATASET_READ = "analytics:dataset:read"
    ANALYTICS_CALCULATE = "analytics:calculate"
    REPORTS_READ = "reports:read"
    REPORTS_EXPORT = "reports:export"
    AUDIT_LOGS_READ = "audit:logs:read"
    AUDIT_LOGS_EXPORT = "audit:logs:export"
    OPERATIONS_MANAGE = "operations:manage"
    PLATFORM_MANAGE = "platform:manage"
    SALES_CONFIRM = "sales:confirm"
    SALES_EXPORT = "sales:export"
    CUSTOMERS_ARCHIVE = "customers:archive"
    CUSTOMERS_SENSITIVE_READ = "customers:sensitive:read"
    PRODUCTS_ARCHIVE = "products:archive"
    APPROVALS_MANAGE = "approvals:manage"
    SUPPORT_TEMPORARY = "support:temporary"


ROLE_PERMISSIONS_MAP: dict[SystemRole, set[Permission]] = {
    SystemRole.COMPANY_ADMIN: {
        Permission.USERS_MANAGE,
        Permission.ORGANIZATION_MANAGE,
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CUSTOMERS_ARCHIVE,
        Permission.CUSTOMERS_SENSITIVE_READ,
        Permission.PRODUCTS_READ,
        Permission.PRODUCTS_WRITE,
        Permission.PRODUCTS_ARCHIVE,
        Permission.PRODUCTS_COST_READ,
        Permission.QUOTATIONS_READ,
        Permission.QUOTATIONS_WRITE,
        Permission.SALES_READ,
        Permission.SALES_WRITE,
        Permission.SALES_CONFIRM,
        Permission.SALES_CANCEL,
        Permission.SALES_EXPORT,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_WRITE,
        Permission.CASH_REGISTER_MANAGE,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_WRITE,
        Permission.PURCHASES_READ,
        Permission.PURCHASES_WRITE,
        Permission.ANALYTICS_DATASET_READ,
        Permission.ANALYTICS_CALCULATE,
        Permission.REPORTS_READ,
        Permission.REPORTS_EXPORT,
        Permission.AUDIT_LOGS_READ,
        Permission.AUDIT_LOGS_EXPORT,
        Permission.OPERATIONS_MANAGE,
        Permission.APPROVALS_MANAGE,
        Permission.SUPPORT_TEMPORARY,
    },
    SystemRole.MANAGER: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.CUSTOMERS_SENSITIVE_READ,
        Permission.PRODUCTS_READ,
        Permission.PRODUCTS_COST_READ,
        Permission.QUOTATIONS_READ,
        Permission.QUOTATIONS_WRITE,
        Permission.SALES_READ,
        Permission.SALES_WRITE,
        Permission.SALES_CONFIRM,
        Permission.SALES_CANCEL,
        Permission.SALES_EXPORT,
        Permission.PAYMENTS_READ,
        Permission.INVENTORY_READ,
        Permission.ANALYTICS_DATASET_READ,
        Permission.ANALYTICS_CALCULATE,
        Permission.REPORTS_READ,
        Permission.REPORTS_EXPORT,
        Permission.APPROVALS_MANAGE,
    },
    SystemRole.SALESPERSON: {
        Permission.CUSTOMERS_READ,
        Permission.CUSTOMERS_WRITE,
        Permission.PRODUCTS_READ,
        Permission.QUOTATIONS_READ,
        Permission.QUOTATIONS_WRITE,
        Permission.SALES_READ,
        Permission.SALES_WRITE,
        Permission.PAYMENTS_READ,
    },
    SystemRole.ANALYST: {
        Permission.CUSTOMERS_READ,
        Permission.PRODUCTS_READ,
        Permission.SALES_READ,
        Permission.ANALYTICS_DATASET_READ,
        Permission.ANALYTICS_CALCULATE,
        Permission.REPORTS_READ,
        Permission.REPORTS_EXPORT,
    },
    SystemRole.WAREHOUSE: {
        Permission.PRODUCTS_READ,
        Permission.INVENTORY_READ,
        Permission.INVENTORY_WRITE,
    },
    SystemRole.CASHIER: {
        Permission.SALES_READ,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_WRITE,
        Permission.CASH_REGISTER_MANAGE,
        Permission.REPORTS_READ,
    },
    SystemRole.PURCHASER: {
        Permission.PRODUCTS_READ,
        Permission.PRODUCTS_COST_READ,
        Permission.PURCHASES_READ,
        Permission.PURCHASES_WRITE,
        Permission.INVENTORY_READ,
    },
    SystemRole.AUDITOR: {
        Permission.CUSTOMERS_READ,
        Permission.PRODUCTS_READ,
        Permission.SALES_READ,
        Permission.PAYMENTS_READ,
        Permission.INVENTORY_READ,
        Permission.PURCHASES_READ,
        Permission.AUDIT_LOGS_READ,
        Permission.REPORTS_READ,
    },
    SystemRole.PLATFORM_ADMIN: {
        Permission.PLATFORM_MANAGE,
        Permission.OPERATIONS_MANAGE,
        Permission.AUDIT_LOGS_READ,
        Permission.USERS_MANAGE,
        Permission.ORGANIZATION_MANAGE,
    },
}


@dataclass(frozen=True)
class RoleDefinition:
    role: SystemRole
    title: str
    description: str
    permissions: list[str]


def get_role_catalog() -> list[RoleDefinition]:
    role_titles = {
        SystemRole.COMPANY_ADMIN: (
            "Administrador de Empresa",
            "Gestión integral de usuarios, configuración y políticas.",
        ),
        SystemRole.MANAGER: ("Gerente Comercial", "Supervisión de metas, sucursales, autorizaciones y márgenes."),
        SystemRole.SALESPERSON: ("Vendedor", "Gestión de cartera de clientes, cotizaciones y ventas."),
        SystemRole.ANALYST: (
            "Analista de Datos",
            "Ejecución de datasets, estadísticas, Bayes y generación de insights.",
        ),
        SystemRole.WAREHOUSE: (
            "Responsable de Almacén",
            "Control físico de inventario, transferencias, entradas y salidas.",
        ),
        SystemRole.CASHIER: ("Cajero / Finanzas", "Apertura y cierre de caja, cobros, liquidaciones y conciliación."),
        SystemRole.PURCHASER: ("Encargado de Compras", "Gestión de proveedores, cotizaciones de compra y órdenes."),
        SystemRole.AUDITOR: ("Auditor", "Inspección inmutable de pistas de auditoría y transacciones históricas."),
        SystemRole.PLATFORM_ADMIN: (
            "Administrador de Plataforma",
            "Monitoreo técnico de tenants, infraestructura y despliegue.",
        ),
    }

    catalog = []
    for role, (title, desc) in role_titles.items():
        perms = [p.value for p in ROLE_PERMISSIONS_MAP.get(role, set())]
        catalog.append(RoleDefinition(role=role, title=title, description=desc, permissions=sorted(perms)))
    return catalog


def has_permission(role: SystemRole, permission: Permission) -> bool:
    granted = ROLE_PERMISSIONS_MAP.get(role, set())
    return permission in granted
