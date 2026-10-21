from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument

from salesia.modules.finanzas.application import obligaciones as service
from salesia.modules.finanzas.application.contracts.obligaciones import BudgetSave, CostCenterCreate, ExpenseCreate, PayableCreate, PayablePaymentCreate, VersionReason
from salesia.modules.finanzas.application.contracts.obligaciones import SupplierBalanceCreate
from salesia.modules.finanzas.infrastructure.models.obligaciones import PayableModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Obligaciones, gastos y presupuestos"])


@router.get("/payable-options")
def payable_options(user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    suppliers = db.scalars(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.is_active.is_(True)).order_by(Supplier.legal_name)).all()
    orders = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "PURCHASE_ORDER", SupplyDocument.supplier_claim_id.is_(None), SupplyDocument.status.notin_(("cancelled", "draft", "submitted"))).order_by(SupplyDocument.created_at.desc())).all()
    from salesia.modules.inventario.infrastructure_models import PurchaseInvoiceMatch
    matches = db.execute(select(PurchaseInvoiceMatch, SupplyDocument).join(SupplyDocument, SupplyDocument.id == PurchaseInvoiceMatch.purchase_order_id).where(PurchaseInvoiceMatch.company_id == user.company_id, SupplyDocument.company_id == user.company_id, PurchaseInvoiceMatch.status.in_(("MATCHED", "APPROVED_OVERRIDE")), PurchaseInvoiceMatch.lines_snapshot_json != "[]", ~select(PayableModel.id).where(PayableModel.company_id == user.company_id, PayableModel.invoice_match_id == PurchaseInvoiceMatch.id).exists()).order_by(PurchaseInvoiceMatch.created_at.desc())).all()
    import json
    invoice_matches = [{"id": str(match.id), "purchase_order_id": str(order.id), "supplier_id": str(order.supplier_id), "document_number": match.invoice_number, "amount": str(match.invoice_amount), "currency": json.loads(order.details_json or "{}").get("currency", "USD"), "payment_terms_days": json.loads(order.details_json or "{}").get("payment_terms_days", 30)} for match, order in matches]
    return {"suppliers": [{"id": str(row.id), "legal_name": row.legal_name, "currency": row.currency} for row in suppliers], "purchase_orders": [{"id": str(row.id), "supplier_id": str(row.supplier_id), "label": f"Compra {str(row.id)[:8].upper()} · {row.created_at.date().isoformat()}"} for row in orders], "invoice_matches": invoice_matches}


@router.get("/payables")
def list_payables(status: Optional[Literal["open", "partial", "paid", "cancelled"]] = None, supplier_id: Optional[UUID] = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_payables(db, user, status, supplier_id, limit, offset)


@router.post("/payables", status_code=201)
def create_payable(payload: PayableCreate, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_payable(db, user, payload, key)


@router.get("/payables/{payable_id}")
def get_payable(payable_id: UUID, user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.payable_data(db, service.scoped(db, PayableModel, user, payable_id), True)


@router.post("/payables/{payable_id}/payments", status_code=201)
def pay_payable(payable_id: UUID, payload: PayablePaymentCreate, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.post_payable_payment(db, user, payable_id, payload, key)


@router.post("/payables/{payable_id}/payments/{payment_id}/reverse")
def reverse_payable_payment(payable_id: UUID, payment_id: UUID, payload: VersionReason, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.reverse_payable_payment(db, user, payable_id, payment_id, payload, key)


@router.post("/payables/{payable_id}/cancel")
def cancel_payable(payable_id: UUID, payload: VersionReason, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.cancel_payable(db, user, payable_id, payload, key)


@router.get("/cost-centers")
def list_cost_centers(user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_centers(db, user)


@router.get("/supplier-balances")
def list_supplier_balances(user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_supplier_balances(db, user)


@router.post("/supplier-balances", status_code=201)
def create_supplier_balance(payload: SupplierBalanceCreate, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_supplier_balance(db, user, payload, key)


@router.get("/supplier-balances/{supplier_id}/{currency}")
def supplier_balance_detail(supplier_id: UUID, currency: str, user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    from salesia.modules.finanzas.application.saldos_proveedor import supplier_credit_detail
    return supplier_credit_detail(db, user, supplier_id, currency)


@router.post("/cost-centers", status_code=201)
def create_cost_center(payload: CostCenterCreate, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_center(db, user, payload, key)


@router.get("/expenses")
def list_expenses(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_expenses(db, user, limit, offset)


@router.post("/expenses", status_code=201)
def create_expense(payload: ExpenseCreate, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.create_expense(db, user, payload, key)


@router.post("/expenses/{expense_id}/{action}")
def expense_action(expense_id: UUID, action: Literal["submit", "approve", "reject", "cancel"], payload: VersionReason, user: AuthenticatedUser = Depends(require_permission("payments:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.expense_action(db, user, expense_id, action, payload, key)


@router.get("/cost-budgets")
def list_cost_budgets(user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)):
    return service.list_budgets(db, user)


@router.put("/cost-budgets")
def save_cost_budget(payload: BudgetSave, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_budget(db, user, payload, key)
