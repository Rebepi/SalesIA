import json
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.modules.ventas.application import comisiones as service
from salesia.modules.ventas.application import conciliacion_comisiones as corrections
from salesia.modules.ventas.application import participacion_comercial as participation
from salesia.modules.ventas.application import politicas_comision as policies
from salesia.modules.ventas.application.auxiliares.scoped_sale import scoped_sale
from salesia.modules.ventas.application.contracts.comisiones import CommissionActionRequest, CommissionCalculateRequest, CommissionObservationRequest, CommissionObservationResolution
from salesia.shared.infrastructure.database import get_db
from salesia.modules.organizacion.application.periodos import business_date

router = APIRouter(prefix="/sales")


@router.post("/commissions/calculate")
def calculate_commissions(req: CommissionCalculateRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.calculate_commissions(req, current_user, db)


@router.get("/commissions")
def list_commissions(representative_id: UUID | None = None, period: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"), currency: str | None = Query(None, pattern=r"^[A-Z]{3}$"), limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), current_user: AuthenticatedUser = Depends(require_permission("sales:read", "organization:manage")), db: Session = Depends(get_db)):
    return service.list_settlements(db, current_user, representative_id, period, currency, limit, offset)


@router.get("/commission-sale-options")
def commission_sale_options(search: str | None = Query(None, max_length=128), status: str | None = Query(None, pattern="^(draft|confirmed|paid|cancelled|refunded)$"), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), current_user: AuthenticatedUser = Depends(require_permission("sales:read", "organization:manage")), db: Session = Depends(get_db)):
    return service.sale_options(db, current_user, search, status, limit, offset)


@router.get("/commissions/{settlement_id}")
def get_commission(settlement_id: UUID, current_user: AuthenticatedUser = Depends(require_permission("sales:read", "organization:manage")), db: Session = Depends(get_db)):
    return service.get_settlement(db, current_user, settlement_id)


@router.post("/commissions/{settlement_id}/approve")
def approve_commission_settlement(settlement_id: UUID, payload: CommissionActionRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.approve_commission_settlement(settlement_id, payload, current_user, db, idempotency_key)


@router.post("/commissions/{settlement_id}/pay")
def pay_commission_settlement(settlement_id: UUID, payload: CommissionActionRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.pay_commission_settlement(settlement_id, payload, current_user, db, idempotency_key)


@router.post("/commissions/{settlement_id}/discard")
def discard_commission(settlement_id: UUID, payload: CommissionActionRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.discard_settlement(db, current_user, settlement_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/observations")
def observe_commission(settlement_id: UUID, payload: CommissionObservationRequest, current_user: AuthenticatedUser = Depends(require_permission("sales:read", "organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.observe(db, current_user, settlement_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/observations/{observation_id}/resolve")
def resolve_commission_observation(settlement_id: UUID, observation_id: UUID, payload: CommissionObservationResolution, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.resolve_observation(db, current_user, settlement_id, observation_id, payload, idempotency_key)


@router.get("/commission-policy")
def get_commission_policy(current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return {**policies.current_policy(db, current_user.company_id), "business_date": business_date(db, current_user.company_id).isoformat()}


@router.put("/commission-policy")
def save_commission_policy(payload: policies.CommissionPolicySave, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return policies.save_policy(db, current_user, payload, idempotency_key)


@router.get("/commission-policy/history")
def commission_policy_history(current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return policies.history(db, current_user.company_id)


@router.get("/{sale_id}/commission-participation")
def get_sale_participation(sale_id: UUID, current_user: AuthenticatedUser = Depends(require_permission("sales:read")), db: Session = Depends(get_db)):
    sale = scoped_sale(db, sale_id, current_user)
    return {"sale_id": str(sale.id), "document_number": f"{sale.series}-{sale.number:08d}", "original_representative_id": str(sale.sales_rep_id) if sale.sales_rep_id else None, "sale_version": sale.version, "status": sale.status, **json.loads(sale.commission_snapshot_json or "{}")}


@router.put("/{sale_id}/commission-participation")
def save_sale_participation(sale_id: UUID, payload: participation.ParticipationSave, current_user: AuthenticatedUser = Depends(require_permission("sales:write")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return participation.save_participation(db, current_user, sale_id, payload, idempotency_key)


@router.get("/commission-coverages")
def list_commission_coverages(current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return participation.coverage_rows(db, current_user.company_id)


@router.post("/commission-coverages")
def save_commission_coverage(payload: participation.CoverageSave, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return participation.save_coverage(db, current_user, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/adjustments")
def propose_commission_adjustment(settlement_id: UUID, payload: corrections.ManualAdjustmentRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return corrections.propose_adjustment(db, current_user, settlement_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/reconciliations")
def propose_commission_reconciliation(settlement_id: UUID, payload: corrections.HistoricalReconciliationRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return corrections.propose_reconciliation(db, current_user, settlement_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/corrections/{case_id}/review")
def review_commission_correction(settlement_id: UUID, case_id: UUID, payload: corrections.CaseReviewRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return corrections.review_case(db, current_user, settlement_id, case_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/returns/{return_id}/acceptance-date")
def identify_commission_return_date(settlement_id: UUID, return_id: UUID, payload: corrections.AcceptanceDateRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return corrections.identify_acceptance_date(db, current_user, settlement_id, return_id, payload, idempotency_key)


@router.post("/commissions/{settlement_id}/returns/{return_id}/line-origins")
def identify_commission_return_lines(settlement_id: UUID, return_id: UUID, payload: corrections.ReturnOriginRequest, current_user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return corrections.identify_return_lines(db, current_user, settlement_id, return_id, payload, idempotency_key)
