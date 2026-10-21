from salesia.modules.seguridad.domain.roles import (
    SystemRole,
    Permission,
    ROLE_PERMISSIONS_MAP,
    get_role_catalog,
    has_permission
)


def test_system_roles_count():
    catalog = get_role_catalog()
    assert len(catalog) == 9


def test_company_admin_permissions():
    assert has_permission(SystemRole.COMPANY_ADMIN, Permission.USERS_MANAGE)
    assert has_permission(SystemRole.COMPANY_ADMIN, Permission.ORGANIZATION_MANAGE)
    assert has_permission(SystemRole.COMPANY_ADMIN, Permission.SALES_WRITE)


def test_salesperson_restricted_permissions():
    assert has_permission(SystemRole.SALESPERSON, Permission.SALES_WRITE)
    assert has_permission(SystemRole.SALESPERSON, Permission.CUSTOMERS_WRITE)
    assert not has_permission(SystemRole.SALESPERSON, Permission.USERS_MANAGE)
    assert not has_permission(SystemRole.SALESPERSON, Permission.PRODUCTS_COST_READ)


def test_analyst_permissions():
    assert has_permission(SystemRole.ANALYST, Permission.ANALYTICS_CALCULATE)
    assert has_permission(SystemRole.ANALYST, Permission.ANALYTICS_DATASET_READ)
    assert not has_permission(SystemRole.ANALYST, Permission.SALES_WRITE)
    assert not has_permission(SystemRole.ANALYST, Permission.INVENTORY_WRITE)


def test_warehouse_permissions():
    assert has_permission(SystemRole.WAREHOUSE, Permission.INVENTORY_READ)
    assert has_permission(SystemRole.WAREHOUSE, Permission.INVENTORY_WRITE)
    assert not has_permission(SystemRole.WAREHOUSE, Permission.SALES_WRITE)
    assert not has_permission(SystemRole.WAREHOUSE, Permission.PAYMENTS_WRITE)


EXPECTED_ROLE_PERMISSIONS = {
    SystemRole.COMPANY_ADMIN: set(Permission) - {Permission.PLATFORM_MANAGE},
    SystemRole.MANAGER: {
        Permission.CUSTOMERS_READ, Permission.CUSTOMERS_WRITE, Permission.CUSTOMERS_SENSITIVE_READ,
        Permission.PRODUCTS_READ, Permission.PRODUCTS_COST_READ, Permission.QUOTATIONS_READ,
        Permission.QUOTATIONS_WRITE, Permission.SALES_READ, Permission.SALES_WRITE,
        Permission.SALES_CONFIRM, Permission.SALES_CANCEL, Permission.SALES_EXPORT,
        Permission.PAYMENTS_READ, Permission.INVENTORY_READ, Permission.ANALYTICS_DATASET_READ,
        Permission.ANALYTICS_CALCULATE, Permission.REPORTS_READ, Permission.REPORTS_EXPORT,
        Permission.APPROVALS_MANAGE,
    },
    SystemRole.SALESPERSON: {
        Permission.CUSTOMERS_READ, Permission.CUSTOMERS_WRITE, Permission.PRODUCTS_READ,
        Permission.QUOTATIONS_READ, Permission.QUOTATIONS_WRITE, Permission.SALES_READ,
        Permission.SALES_WRITE, Permission.PAYMENTS_READ,
    },
    SystemRole.ANALYST: {
        Permission.CUSTOMERS_READ, Permission.PRODUCTS_READ, Permission.SALES_READ,
        Permission.ANALYTICS_DATASET_READ, Permission.ANALYTICS_CALCULATE,
        Permission.REPORTS_READ, Permission.REPORTS_EXPORT,
    },
    SystemRole.WAREHOUSE: {
        Permission.PRODUCTS_READ, Permission.INVENTORY_READ, Permission.INVENTORY_WRITE,
    },
    SystemRole.CASHIER: {
        Permission.SALES_READ, Permission.PAYMENTS_READ, Permission.PAYMENTS_WRITE,
        Permission.CASH_REGISTER_MANAGE, Permission.REPORTS_READ,
    },
    SystemRole.PURCHASER: {
        Permission.PRODUCTS_READ, Permission.PRODUCTS_COST_READ, Permission.PURCHASES_READ,
        Permission.PURCHASES_WRITE, Permission.INVENTORY_READ,
    },
    SystemRole.AUDITOR: {
        Permission.CUSTOMERS_READ, Permission.PRODUCTS_READ, Permission.SALES_READ,
        Permission.PAYMENTS_READ, Permission.INVENTORY_READ, Permission.PURCHASES_READ,
        Permission.AUDIT_LOGS_READ, Permission.REPORTS_READ,
    },
    SystemRole.PLATFORM_ADMIN: {
        Permission.PLATFORM_MANAGE, Permission.OPERATIONS_MANAGE, Permission.AUDIT_LOGS_READ,
        Permission.USERS_MANAGE, Permission.ORGANIZATION_MANAGE,
    },
}


def test_complete_permission_matrix_for_all_nine_roles():
    assert set(EXPECTED_ROLE_PERMISSIONS) == set(SystemRole)
    for role, expected_permissions in EXPECTED_ROLE_PERMISSIONS.items():
        assert ROLE_PERMISSIONS_MAP[role] == expected_permissions
        for permission in Permission:
            assert has_permission(role, permission) is (permission in expected_permissions)
