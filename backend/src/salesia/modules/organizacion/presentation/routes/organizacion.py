from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.organizacion.application.organizacion as service_organizacion
from salesia.modules.organizacion.application.contracts.organizacion import (
    BrandingPreviewModel,
    ContextSwitchModel,
    OnboardingSetupModel,
    PeriodCloseModel,
    PeriodReopenModel,
    PreferenceResetModel,
    QuotaCheckModel,
    TaxRuleModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/organization/onboarding/status")
def get_onboarding_status(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.get_onboarding_status(current_user=current_user, db=db)


@router.post("/organization/onboarding/setup")
def run_onboarding_setup(
    req: OnboardingSetupModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.run_onboarding_setup(req=req, current_user=current_user, db=db)


@router.post("/organization/context/switch")
def switch_branch_context(
    req: ContextSwitchModel, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_organizacion.switch_branch_context(req=req, current_user=current_user, db=db)


@router.get("/organization/preferences")
def get_preferences_hierarchy(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_organizacion.get_preferences_hierarchy(current_user=current_user, db=db)


@router.post("/organization/preferences/reset")
def reset_preference(
    req: PreferenceResetModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.reset_preference(req=req, current_user=current_user, db=db)


@router.get("/organization/sequences")
def list_sequences(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.list_sequences(current_user=current_user, db=db)


@router.post("/organization/sequences/reserve")
def reserve_next_sequence_number(
    series: str = Query(min_length=1, max_length=16),
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.reserve_next_sequence_number(series=series, current_user=current_user, db=db)


@router.get("/organization/tax-rules")
def list_tax_rules(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.list_tax_rules(current_user=current_user, db=db)


@router.post("/organization/tax-rules")
def update_tax_rule(
    req: TaxRuleModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.update_tax_rule(req=req, current_user=current_user, db=db)


@router.get("/organization/business-hours")
def get_business_hours(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.get_business_hours(current_user=current_user, db=db)


@router.post("/organization/periods/close")
def close_accounting_period(
    req: PeriodCloseModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.close_accounting_period(req=req, current_user=current_user, db=db)


@router.post("/organization/periods/reopen")
def reopen_accounting_period(
    req: PeriodReopenModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_organizacion.reopen_accounting_period(req=req, current_user=current_user, db=db)


@router.get("/organization/branding")
def get_branding(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.get_branding(current_user=current_user, db=db)


@router.post("/organization/branding/preview")
def preview_branding(req: BrandingPreviewModel, current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_organizacion.preview_branding(req=req, current_user=current_user)


@router.get("/organization/quotas")
def get_quotas(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_organizacion.get_quotas(current_user=current_user, db=db)


@router.post("/organization/quotas/check")
def check_quota(
    req: QuotaCheckModel, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_organizacion.check_quota(req=req, current_user=current_user, db=db)


@router.post("/organization/test-mode/verify")
def verify_test_mode(
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)
):
    return service_organizacion.verify_test_mode(current_user=current_user, db=db)
