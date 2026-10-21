import json
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.contracts.cuentas_cobrar import CollectionActivityRequest
from salesia.modules.finanzas.infrastructure_models import CreditNoteModel, PaymentDisputeModel
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact, CollaborationTask
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CustomerModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def get_receivables(current_user: AuthenticatedUser, db: Session):
    sales = (
        db.execute(
            select(SaleModel).where(
                SaleModel.company_id == current_user.company_id, SaleModel.status.in_(["confirmed"])
            )
        )
        .scalars()
        .all()
    )

    totals_by_currency = {}
    from salesia.modules.organizacion.application.periodos import business_date
    today = business_date(db, current_user.company_id)
    from zoneinfo import ZoneInfo
    from salesia.shared.infrastructure.transactions import CompanySettings
    settings = db.get(CompanySettings, current_user.company_id)
    zone = ZoneInfo(json.loads(settings.values_json or "{}").get("timezone", "America/Lima")) if settings else ZoneInfo("America/Lima")

    items = []

    for s in sales:
        pending = (s.total_amount - s.paid_amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        if pending > Decimal("0.000000"):
            totals_by_currency[s.currency] = totals_by_currency.get(s.currency, Decimal("0")) + pending

            created = s.created_at.replace(tzinfo=timezone.utc) if s.created_at.tzinfo is None else s.created_at

            due_date = s.due_at or (s.confirmed_at or created) + timedelta(days=s.payment_terms_days)

            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)

            age_days = (today - due_date.astimezone(zone).date()).days

            if age_days <= 0:
                aging_bucket = "not_due"

            elif age_days <= 30:
                aging_bucket = "0-30"

            elif age_days <= 60:
                aging_bucket = "31-60"

            elif age_days <= 90:
                aging_bucket = "61-90"

            else:
                aging_bucket = "90+"

            aging_balances = {key: "0" for key in ("not_due", "0-30", "31-60", "61-90", "90+")}
            aging_balances[aging_bucket] = str(pending)
            from salesia.modules.finanzas.application.cuotas_cobranza import schedule_data
            scheduled = schedule_data(db, current_user, s)
            if scheduled and Decimal(scheduled["balance_difference"]) == 0 and Decimal(scheduled["unassigned_applications"]) == 0:
                aging_values = {key: Decimal("0") for key in aging_balances}
                outstanding = [line for line in scheduled["items"] if Decimal(line["balance"]) > 0]
                for line in outstanding:
                    days = line["overdue_days"]
                    bucket = "not_due" if days <= 0 else "0-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
                    aging_values[bucket] += Decimal(line["balance"])
                aging_balances = {key: str(value) for key, value in aging_values.items()}
                if outstanding:
                    due_date = datetime.fromisoformat(min(line["due_date"] for line in outstanding)).replace(tzinfo=zone)
                    age_days = max(line["overdue_days"] for line in outstanding)
                    aging_bucket = "not_due" if age_days <= 0 else "0-30" if age_days <= 30 else "31-60" if age_days <= 60 else "61-90" if age_days <= 90 else "90+"
            items.append(
                {
                    "sale_id": str(s.id),
                    "customer_id": str(s.customer_id),
                    "customer_name": (
                        db.get(CustomerModel, s.customer_id).legal_name
                        if db.get(CustomerModel, s.customer_id)
                        else "Cliente no disponible"
                    ),
                    "currency": s.currency,
                    "branch_id": str(s.branch_id),
                    "series_number": f"{s.series}-{s.number:06d}",
                    "total_amount": str(s.total_amount),
                    "paid_amount": str(s.paid_amount),
                    "balance_due": str(pending),
                    "due_date": due_date.isoformat(),
                    "aging_bucket": aging_bucket,
                    "aging_balances": aging_balances,
                    "has_installments": scheduled is not None,
                    "schedule_needs_review": bool(scheduled and (Decimal(scheduled["balance_difference"]) != 0 or Decimal(scheduled["unassigned_applications"]) > 0)),
                    "overdue_days": max(0, age_days),
                    "payment_terms_days": s.payment_terms_days,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                }
            )

    disputes = db.execute(select(SaleModel.currency, func.coalesce(func.sum(PaymentDisputeModel.amount), Decimal("0"))).join(SaleModel, SaleModel.id == PaymentDisputeModel.sale_id).where(PaymentDisputeModel.company_id == current_user.company_id, SaleModel.company_id == current_user.company_id, PaymentDisputeModel.status == "under_review").group_by(SaleModel.currency)).all()
    disputed_by_currency = {currency: amount for currency, amount in disputes}
    currencies = sorted(set(totals_by_currency) | set(disputed_by_currency))
    summaries = {currency: {"total_receivable": str(totals_by_currency.get(currency, Decimal("0"))), "total_disputed": str(disputed_by_currency.get(currency, Decimal("0"))), "not_due": str(sum((Decimal(item["aging_balances"]["not_due"]) for item in items if item["currency"] == currency), Decimal("0")))} for currency in currencies}
    return {
        "company_id": str(current_user.company_id),
        "currency": currencies[0] if len(currencies) == 1 else None,
        "total_receivable": summaries[currencies[0]]["total_receivable"] if len(currencies) == 1 else "0.000000" if not currencies else None,
        "total_disputed": summaries[currencies[0]]["total_disputed"] if len(currencies) == 1 else "0.000000" if not currencies else None,
        "totals_by_currency": summaries,
        "count": len(items),
        "items": items,
    }


def receivable_context(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    from salesia.modules.finanzas.application.cuotas_cobranza import schedule_data
    from salesia.modules.finanzas.application.acuerdos_cobranza import all_agreements
    sale = db.scalar(select(SaleModel).where(SaleModel.id == sale_id, SaleModel.company_id == current_user.company_id))

    if not sale:
        raise HTTPException(404, "Cuenta por cobrar no encontrada.")

    customer = db.scalar(
        select(CustomerModel).where(
            CustomerModel.id == sale.customer_id, CustomerModel.company_id == current_user.company_id
        )
    )

    payments = db.scalars(
        select(PaymentModel)
        .where(PaymentModel.sale_id == sale.id, PaymentModel.company_id == current_user.company_id)
        .order_by(PaymentModel.created_at)
    ).all()

    notes = db.scalars(
        select(CreditNoteModel).where(
            CreditNoteModel.sale_id == sale.id, CreditNoteModel.company_id == current_user.company_id
        )
    ).all()

    activities = db.scalars(
        select(AnalyticsArtifact)
        .where(
            AnalyticsArtifact.company_id == current_user.company_id,
            AnalyticsArtifact.kind == "collection_activity",
            AnalyticsArtifact.artifact_key == str(sale.id),
        )
        .order_by(AnalyticsArtifact.created_at.desc())
    ).all()

    return {
        "sale_id": str(sale.id),
        "document": f"{sale.series}-{sale.number:08d}",
        "customer_name": customer.legal_name if customer else "Cliente registrado",
        "customer_code": customer.code if customer else "",
        "currency": sale.currency,
        "branch_id": str(sale.branch_id),
        "total_amount": str(sale.total_amount),
        "paid_amount": str(sale.paid_amount),
        "balance_due": str(max(Decimal("0"), sale.total_amount - sale.paid_amount)),
        "payment_terms_days": sale.payment_terms_days,
        "due_at": sale.due_at.isoformat() if sale.due_at else None,
        "payments": [
            {
                "date": row.created_at.isoformat(),
                "amount": str(row.amount),
                "method": row.payment_method,
                "reference": row.reference_code,
                "status": row.status,
            }
            for row in payments
        ],
        "credit_notes": [
            {"document": f"{row.series}-{row.number:08d}", "amount": str(row.total_amount), "status": row.status}
            for row in notes
        ],
        "activities": [json.loads(row.data_json) for row in activities],
        "agreements": all_agreements(db, current_user, sale),
        "installment_schedule": schedule_data(db, current_user, sale),
        "sale_version": sale.version,
    }


def create_collection_activity(
    sale_id: UUID,
    payload: CollectionActivityRequest,
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "collection.activity",
        idempotency_key,
        {"sale_id": str(sale_id), **payload.model_dump(mode="json")},
    )

    if cached is not None:
        return cached

    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not sale:
        raise HTTPException(404, "Cuenta por cobrar no encontrada.")

    balance = sale.total_amount - sale.paid_amount

    if sale.status not in ("confirmed", "paid"):
        raise HTTPException(409, "Registra gestiones sobre una venta confirmada y vigente.")
    if balance <= 0:
        raise HTTPException(409, "La venta ya no tiene saldo pendiente.")

    if payload.promised_amount and payload.promised_amount > balance:
        raise HTTPException(422, "El compromiso supera el saldo pendiente.")

    if payload.kind in ("promise", "agreement") and (not payload.promised_amount or not payload.next_action_at):
        raise HTTPException(422, "Indica el importe comprometido y la fecha de seguimiento.")

    if payload.next_action_at and (
        payload.next_action_at.tzinfo is None or payload.next_action_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(422, "El seguimiento debe tener una fecha futura con zona horaria.")

    calendar_adjustment = None
    if payload.adjust_to_operating_calendar and payload.next_action_at:
        from salesia.modules.organizacion.application.calendario_operativo import DateRequest, calculate_date, effective_calendar
        calendar_adjustment = calculate_date(effective_calendar(db, current_user.company_id, sale.branch_id), DateRequest(start_at=payload.next_action_at, purpose="reminder", respect_cutoff=True))
        payload.next_action_at = datetime.fromisoformat(calendar_adjustment["utc_at"])
        if payload.next_action_at <= datetime.now(timezone.utc):
            raise HTTPException(422, "La fecha ajustada del seguimiento debe quedar en el futuro.")

    activity_id = uuid4()

    data = {
        "id": str(activity_id),
        **payload.model_dump(mode="json"),
        "responsible": current_user.email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "balance_at_creation": str(balance),
        "calendar_adjustment": calendar_adjustment,
    }

    if payload.kind in ("promise", "agreement"):
        from salesia.modules.finanzas.application.acuerdos_cobranza import register_activity_agreement
        register_activity_agreement(db, current_user, sale, data)

    version = (
        db.scalar(
            select(func.max(AnalyticsArtifact.version)).where(
                AnalyticsArtifact.company_id == current_user.company_id,
                AnalyticsArtifact.kind == "collection_activity",
                AnalyticsArtifact.artifact_key == str(sale.id),
            )
        )
        or 0
    ) + 1

    db.add(
        AnalyticsArtifact(
            id=activity_id,
            company_id=current_user.company_id,
            kind="collection_activity",
            artifact_key=str(sale.id),
            version=version,
            status="active",
            data_json=json.dumps(data),
            created_by=current_user.user_id,
        )
    )

    if payload.next_action_at and payload.kind not in ("promise", "agreement"):
        db.add(
            CollaborationTask(
                company_id=current_user.company_id,
                creator_id=current_user.user_id,
                assignee_id=current_user.user_id,
                title=f"Cobranza {sale.series}-{sale.number:08d}",
                description=payload.notes,
                due_date=payload.next_action_at,
                priority="high",
                resource_type="sale",
                resource_id=sale.id,
                status="pending",
            )
        )

    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="COLLECTION_ACTIVITY",
        entity_type="Sale",
        entity_id=sale.id,
        diff=data,
        category="FINANCE",
        fail_critical=True,
    )

    complete_request(record, data)

    db.commit()

    return data
