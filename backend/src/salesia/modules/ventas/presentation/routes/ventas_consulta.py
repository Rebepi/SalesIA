from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, date as date_type

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, case
from sqlalchemy.orm import Session

import salesia.modules.ventas.application.ventas_consulta as service_ventas_consulta
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.models import SaleModel

router = APIRouter(prefix="/sales")


@router.get("/kpis")
def get_sales_kpis(
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    base = [SaleModel.company_id == company_id]

    today_rows = db.execute(
        select(func.count().label("cnt"), func.coalesce(func.sum(SaleModel.total_amount), 0).label("amt"))
        .where(*base, SaleModel.created_at >= today_start, SaleModel.status != "cancelled")
    ).first()

    month_rows = db.execute(
        select(func.count().label("cnt"), func.coalesce(func.sum(SaleModel.total_amount), 0).label("amt"))
        .where(*base, SaleModel.created_at >= month_start, SaleModel.status != "cancelled")
    ).first()

    receivable_rows = db.execute(
        select(func.count().label("cnt"), func.coalesce(func.sum(SaleModel.total_amount - SaleModel.paid_amount), 0).label("amt"))
        .where(*base, SaleModel.status.in_(["confirmed"]), SaleModel.paid_amount < SaleModel.total_amount)
    ).first()

    draft_count = db.scalar(
        select(func.count()).where(*base, SaleModel.status == "draft")
    ) or 0

    return {
        "today_count": int(today_rows.cnt) if today_rows else 0,
        "today_amount": float(today_rows.amt) if today_rows else 0.0,
        "month_count": int(month_rows.cnt) if month_rows else 0,
        "month_amount": float(month_rows.amt) if month_rows else 0.0,
        "receivable_count": int(receivable_rows.cnt) if receivable_rows else 0,
        "receivable_amount": float(receivable_rows.amt) if receivable_rows else 0.0,
        "overdue_count": 0,
        "overdue_amount": 0.0,
        "pending_delivery_count": 0,
        "sunat_rejected_count": 0,
        "old_drafts_count": int(draft_count),
    }


@router.get("")
def list_sales(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sale_status: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    sales_rep_id: Optional[UUID] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):
    qp = request.query_params
    return service_ventas_consulta.list_sales(
        page=page,
        page_size=page_size,
        sale_status=sale_status or qp.get("document_status"),
        customer_id=customer_id,
        branch_id=branch_id,
        sales_rep_id=sales_rep_id,
        currency=currency,
        current_user=current_user,
        db=db,
        warehouse_id=qp.get("warehouse_id"),
        search=qp.get("q") or qp.get("search"),
        date_shortcut=qp.get("date_shortcut"),
        date_from=qp.get("date_from"),
        date_to=qp.get("date_to"),
        document_type=qp.get("document_type"),
        payment_status=qp.get("payment_status"),
        delivery_status=qp.get("delivery_status"),
        sunat_status=qp.get("sunat_status"),
        return_status=qp.get("return_status"),
        min_amount=qp.get("min_amount"),
        max_amount=qp.get("max_amount"),
        only_with_balance=qp.get("only_with_balance"),
        only_overdue=qp.get("only_overdue"),
        only_with_returns=qp.get("only_with_returns"),
        origin=qp.get("origin"),
        only_zero_cost=qp.get("only_zero_cost", "").lower() in ("true", "1"),
        only_unassigned=qp.get("only_unassigned", "").lower() in ("true", "1"),
        only_with_lines=qp.get("only_with_lines", "").lower() in ("true", "1"),
        category=qp.get("category"),
        date_basis=qp.get("date_basis", "created"),
        dashboard_period=qp.get("dashboard_period"),
        dashboard_as_of=qp.get("dashboard_as_of"),
    )


@router.get("/export")
def export_sales(
    current_user: AuthenticatedUser = Depends(require_permission("sales:export")), db: Session = Depends(get_db)
):

    return service_ventas_consulta.export_sales(current_user=current_user, db=db)


@router.get("/lookup")
def lookup_sales(
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_ventas_consulta.lookup_sales(
        search=search, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.get("/by-idempotency-key/{key}")
def get_sale_by_idempotency_key(
    key: str,
    operation: str = Query("sales.confirm"),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_ventas_consulta.get_sale_by_idempotency_key(
        key=key, operation=operation, current_user=current_user, db=db
    )


@router.get("/{sale_id}")
def get_sale(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_ventas_consulta.get_sale(sale_id=sale_id, current_user=current_user, db=db)
