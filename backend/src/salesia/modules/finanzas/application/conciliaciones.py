from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.contracts.conciliaciones import (
    ReconciliationCreateRequest,
    ReconciliationResolveRequest,
)
from salesia.modules.finanzas.infrastructure_models import FinanceReconciliationItemModel, FinanceReconciliationModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import PaymentModel


def create_reconciliation(payload: ReconciliationCreateRequest, current_user: AuthenticatedUser, db: Session):
    recon = FinanceReconciliationModel(
        id=uuid4(),
        company_id=current_user.company_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="open",
        created_by=current_user.user_id,
    )

    db.add(recon)

    db.flush()

    local_payments = db.scalars(
        select(PaymentModel).where(
            PaymentModel.company_id == current_user.company_id, PaymentModel.status == "confirmed"
        )
    ).all()

    local_by_ref = {p.reference_code: p for p in local_payments if p.reference_code}

    items = []

    matched_refs = set()

    for ext in payload.external_lines:
        p = local_by_ref.get(ext.reference_code)

        if p:
            matched_refs.add(ext.reference_code)

            diff = (p.amount - ext.amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

            classification = "MATCH" if diff == 0 else "AMOUNT_MISMATCH"

            item = FinanceReconciliationItemModel(
                id=uuid4(),
                company_id=current_user.company_id,
                reconciliation_id=recon.id,
                classification=classification,
                payment_id=p.id,
                external_reference=ext.reference_code,
                local_amount=p.amount,
                external_amount=ext.amount,
                difference_amount=diff,
                is_resolved=(diff == 0),
            )

        else:
            item = FinanceReconciliationItemModel(
                id=uuid4(),
                company_id=current_user.company_id,
                reconciliation_id=recon.id,
                classification="LOCAL_MISSING",
                external_reference=ext.reference_code,
                external_amount=ext.amount,
                difference_amount=ext.amount,
                is_resolved=False,
            )

        db.add(item)

        items.append(item)

    for ref, p in local_by_ref.items():
        if ref not in matched_refs:
            item = FinanceReconciliationItemModel(
                id=uuid4(),
                company_id=current_user.company_id,
                reconciliation_id=recon.id,
                classification="EXTERNAL_MISSING",
                payment_id=p.id,
                external_reference=ref,
                local_amount=p.amount,
                difference_amount=p.amount,
                is_resolved=False,
            )

            db.add(item)

            items.append(item)

    db.commit()

    return {
        "id": str(recon.id),
        "status": recon.status,
        "items": [
            {
                "id": str(i.id),
                "classification": i.classification,
                "external_reference": i.external_reference,
                "local_amount": str(i.local_amount) if i.local_amount is not None else None,
                "external_amount": str(i.external_amount) if i.external_amount is not None else None,
                "difference_amount": str(i.difference_amount) if i.difference_amount is not None else None,
                "is_resolved": i.is_resolved,
            }
            for i in items
        ],
    }


def get_reconciliation(reconciliation_id: UUID, current_user: AuthenticatedUser, db: Session):
    recon = db.scalar(
        select(FinanceReconciliationModel).where(
            FinanceReconciliationModel.id == reconciliation_id,
            FinanceReconciliationModel.company_id == current_user.company_id,
        )
    )

    if not recon:
        raise HTTPException(404, "Conciliación no encontrada.")

    items = db.scalars(
        select(FinanceReconciliationItemModel).where(
            FinanceReconciliationItemModel.reconciliation_id == recon.id,
            FinanceReconciliationItemModel.company_id == current_user.company_id,
        )
    ).all()

    return {
        "id": str(recon.id),
        "status": recon.status,
        "items": [
            {
                "id": str(i.id),
                "classification": i.classification,
                "external_reference": i.external_reference,
                "local_amount": str(i.local_amount) if i.local_amount is not None else None,
                "external_amount": str(i.external_amount) if i.external_amount is not None else None,
                "difference_amount": str(i.difference_amount) if i.difference_amount is not None else None,
                "is_resolved": i.is_resolved,
            }
            for i in items
        ],
    }


def resolve_reconciliation_item(
    reconciliation_id: UUID,
    item_id: UUID,
    payload: ReconciliationResolveRequest,
    current_user: AuthenticatedUser,
    db: Session,
):
    item = db.scalar(
        select(FinanceReconciliationItemModel)
        .where(
            FinanceReconciliationItemModel.id == item_id,
            FinanceReconciliationItemModel.reconciliation_id == reconciliation_id,
            FinanceReconciliationItemModel.company_id == current_user.company_id,
        )
        .with_for_update()
    )

    if not item:
        raise HTTPException(404, "Item de conciliación no encontrado.")

    item.is_resolved = True

    item.resolved_by = current_user.user_id

    item.resolution_action = payload.resolution_action

    db.commit()

    return {"id": str(item.id), "is_resolved": True, "resolution_action": item.resolution_action}
