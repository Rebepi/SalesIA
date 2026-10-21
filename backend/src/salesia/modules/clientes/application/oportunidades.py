import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.crm import (
    CustomerOpportunityCreateModel,
    CustomerOpportunityUpdateModel,
)
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerModel, CustomerOpportunityModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import QuotationModel


def list_customer_opportunities(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    opps = db.scalars(
        select(CustomerOpportunityModel)
        .where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.customer_id == customer_id,
        )
        .order_by(CustomerOpportunityModel.created_at.desc())
    ).all()
    return [
        {
            "id": str(o.id),
            "title": o.title,
            "stage": o.stage,
            "estimated_amount": str(o.estimated_amount),
            "probability": str(o.probability),
            "currency": o.currency,
            "assigned_to_id": str(o.assigned_to_id) if o.assigned_to_id else None,
            "next_action": o.next_action,
            "loss_reason": o.loss_reason,
            "converted_quotation_id": str(o.converted_quotation_id) if o.converted_quotation_id else None,
            "created_at": o.created_at.isoformat(),
        }
        for o in opps
    ]


def create_customer_opportunity(
    customer_id: UUID, req: CustomerOpportunityCreateModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    history = [
        {"stage": req.stage, "changed_by": current_user.email, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]
    opp = CustomerOpportunityModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        title=sanitize_text(req.title) or "Oportunidad",
        stage=req.stage,
        estimated_amount=req.estimated_amount,
        probability=req.probability,
        currency=req.currency.upper(),
        assigned_to_id=req.assigned_to_id,
        next_action=sanitize_text(req.next_action),
        next_action_date=req.next_action_date,
        stage_history_json=json.dumps(history),
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)

    return {
        "id": str(opp.id),
        "customer_id": str(customer_id),
        "title": opp.title,
        "stage": opp.stage,
        "estimated_amount": str(opp.estimated_amount),
    }


def list_all_crm_opportunities(stage: Optional[str], current_user: AuthenticatedUser, db: Session):
    query = select(CustomerOpportunityModel).where(CustomerOpportunityModel.company_id == current_user.company_id)
    if stage:
        query = query.where(CustomerOpportunityModel.stage == stage)
    opps = db.scalars(query.order_by(CustomerOpportunityModel.created_at.desc())).all()
    return [
        {
            "id": str(o.id),
            "customer_id": str(o.customer_id),
            "title": o.title,
            "stage": o.stage,
            "estimated_amount": str(o.estimated_amount),
            "probability": str(o.probability),
            "converted_quotation_id": str(o.converted_quotation_id) if o.converted_quotation_id else None,
        }
        for o in opps
    ]


def update_crm_opportunity(
    opportunity_id: UUID, req: CustomerOpportunityUpdateModel, current_user: AuthenticatedUser, db: Session
):
    opp = db.scalar(
        select(CustomerOpportunityModel).where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.id == opportunity_id,
        )
    )
    if not opp:
        raise DomainNotFoundException("Oportunidad no encontrada.")

    if req.stage and req.stage != opp.stage:
        if req.stage == "lost" and not req.loss_reason:
            raise HTTPException(422, {"field": "loss_reason", "rule": "Motivo de pérdida requerido para etapa 'lost'"})
        history = json.loads(opp.stage_history_json)
        history.append(
            {
                "previous_stage": opp.stage,
                "new_stage": req.stage,
                "changed_by": current_user.email,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        opp.stage_history_json = json.dumps(history)
        opp.stage = req.stage

    if req.title is not None:
        opp.title = sanitize_text(req.title) or opp.title
    if req.estimated_amount is not None:
        opp.estimated_amount = req.estimated_amount
    if req.probability is not None:
        opp.probability = req.probability
    if req.assigned_to_id is not None:
        opp.assigned_to_id = req.assigned_to_id
    if req.next_action is not None:
        opp.next_action = sanitize_text(req.next_action)
    if req.next_action_date is not None:
        opp.next_action_date = req.next_action_date
    if req.loss_reason is not None:
        opp.loss_reason = sanitize_text(req.loss_reason)

    db.commit()
    db.refresh(opp)
    return {
        "id": str(opp.id),
        "stage": opp.stage,
        "estimated_amount": str(opp.estimated_amount),
        "loss_reason": opp.loss_reason,
    }


def convert_opportunity_to_quote(opportunity_id: UUID, current_user: AuthenticatedUser, db: Session):
    opp = db.scalar(
        select(CustomerOpportunityModel).where(
            CustomerOpportunityModel.company_id == current_user.company_id,
            CustomerOpportunityModel.id == opportunity_id,
        )
    )
    if not opp:
        raise DomainNotFoundException("Oportunidad no encontrada.")

    if opp.converted_quotation_id:
        existing_quote = db.scalar(select(QuotationModel).where(QuotationModel.id == opp.converted_quotation_id))
        if existing_quote:
            return {
                "opportunity_id": str(opp.id),
                "quotation_id": str(existing_quote.id),
                "quotation_number": existing_quote.quotation_number,
                "already_converted": True,
            }

    quote_number = f"COT-{uuid4().hex[:6].upper()}"
    quote = QuotationModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=opp.customer_id,
        quotation_number=quote_number,
        version=1,
        status="pending",
        currency=opp.currency,
        subtotal_amount=opp.estimated_amount,
        tax_amount=Decimal("0.000000"),
        total_amount=opp.estimated_amount,
        payment_terms_days=30,
        lines_json="[]",
    )
    db.add(quote)
    opp.converted_quotation_id = quote.id
    opp.stage = "won"
    db.commit()

    return {
        "opportunity_id": str(opp.id),
        "quotation_id": str(quote.id),
        "quotation_number": quote.quotation_number,
        "already_converted": False,
    }
