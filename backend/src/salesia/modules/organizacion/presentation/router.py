from fastapi import APIRouter

from salesia.modules.organizacion.application.auxiliares.branch_dict import branch_dict as branch_dict
from salesia.modules.organizacion.application.auxiliares.company_dict import company_dict as company_dict
from salesia.modules.organizacion.application.auxiliares.default_settings_dict import (
    default_settings_dict as default_settings_dict,
)
from salesia.modules.organizacion.application.auxiliares.quota_usage import quota_usage as quota_usage
from salesia.modules.organizacion.application.contracts.almacenes import WarehouseCreateModel as WarehouseCreateModel
from salesia.modules.organizacion.application.contracts.configuracion import SettingsUpdateModel as SettingsUpdateModel
from salesia.modules.organizacion.application.contracts.empresas import CompanyUpdateModel as CompanyUpdateModel
from salesia.modules.organizacion.application.contracts.organizacion import BrandingPreviewModel as BrandingPreviewModel
from salesia.modules.organizacion.application.contracts.organizacion import ContextSwitchModel as ContextSwitchModel
from salesia.modules.organizacion.application.contracts.organizacion import OnboardingSetupModel as OnboardingSetupModel
from salesia.modules.organizacion.application.contracts.organizacion import PeriodCloseModel as PeriodCloseModel
from salesia.modules.organizacion.application.contracts.organizacion import PeriodReopenModel as PeriodReopenModel
from salesia.modules.organizacion.application.contracts.organizacion import PreferenceResetModel as PreferenceResetModel
from salesia.modules.organizacion.application.contracts.organizacion import QuotaCheckModel as QuotaCheckModel
from salesia.modules.organizacion.application.contracts.organizacion import TaxRuleModel as TaxRuleModel
from salesia.modules.organizacion.application.contracts.sedes import BranchCreateModel as BranchCreateModel
from salesia.modules.organizacion.application.contracts.sedes import BranchUpdateModel as BranchUpdateModel
from salesia.modules.organizacion.presentation.routes import almacenes, configuracion, empresas, organizacion, sedes

router = APIRouter(tags=["Organización, Sedes y Configuración"])
router.include_router(empresas.router)
router.include_router(sedes.router)
router.include_router(almacenes.router)
router.include_router(configuracion.router)
router.include_router(organizacion.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "get_current_company",
            "update_current_company",
            "list_branches",
            "create_branch",
            "update_branch",
            "list_warehouses",
            "create_warehouse",
            "get_settings",
            "update_settings",
            "get_onboarding_status",
            "run_onboarding_setup",
            "switch_branch_context",
            "get_preferences_hierarchy",
            "reset_preference",
            "list_sequences",
            "reserve_next_sequence_number",
            "list_tax_rules",
            "update_tax_rule",
            "get_business_hours",
            "close_accounting_period",
            "reopen_accounting_period",
            "get_branding",
            "preview_branding",
            "get_quotas",
            "check_quota",
            "verify_test_mode",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
get_current_company = empresas.get_current_company
update_current_company = empresas.update_current_company
list_branches = sedes.list_branches
create_branch = sedes.create_branch
update_branch = sedes.update_branch
list_warehouses = almacenes.list_warehouses
create_warehouse = almacenes.create_warehouse
get_settings = configuracion.get_settings
update_settings = configuracion.update_settings
get_onboarding_status = organizacion.get_onboarding_status
run_onboarding_setup = organizacion.run_onboarding_setup
switch_branch_context = organizacion.switch_branch_context
get_preferences_hierarchy = organizacion.get_preferences_hierarchy
reset_preference = organizacion.reset_preference
list_sequences = organizacion.list_sequences
reserve_next_sequence_number = organizacion.reserve_next_sequence_number
list_tax_rules = organizacion.list_tax_rules
update_tax_rule = organizacion.update_tax_rule
get_business_hours = organizacion.get_business_hours
close_accounting_period = organizacion.close_accounting_period
reopen_accounting_period = organizacion.reopen_accounting_period
get_branding = organizacion.get_branding
preview_branding = organizacion.preview_branding
get_quotas = organizacion.get_quotas
check_quota = organizacion.check_quota
verify_test_mode = organizacion.verify_test_mode

from salesia.modules.organizacion.presentation.routes.calendario_operativo import router as operating_calendar_router

router.include_router(operating_calendar_router)

from salesia.modules.organizacion.presentation.routes.cierre_ubicaciones import router as location_retirement_router

router.include_router(location_retirement_router)

from salesia.modules.organizacion.presentation.routes.perfil_operativo import router as operating_profile_router

router.include_router(operating_profile_router)

from salesia.modules.organizacion.presentation.routes.periodos_funcionales import router as functional_period_router

router.include_router(functional_period_router)
