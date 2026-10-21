import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.comercial import CustomerSegmentCreateModel
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel, CustomerModel, CustomerSegmentModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import SaleModel


def list_customer_segments(current_user: AuthenticatedUser, db: Session):
    segs = db.scalars(
        select(CustomerSegmentModel).where(
            CustomerSegmentModel.company_id == current_user.company_id, CustomerSegmentModel.is_active.is_(True)
        )
    ).all()
    return [
        {"id": str(s.id), "name": s.name, "description": s.description, "criteria": json.loads(s.criteria_json)}
        for s in segs
    ]


def create_customer_segment(req: CustomerSegmentCreateModel, current_user: AuthenticatedUser, db: Session):
    criteria = {
        "min_frequency": req.min_frequency,
        "min_spend": str(req.min_spend),
        "max_recency_days": req.max_recency_days,
        "zone": req.zone,
    }
    seg = CustomerSegmentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        name=req.name.strip(),
        description=req.description,
        criteria_json=json.dumps(criteria),
        is_active=True,
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return {"id": str(seg.id), "name": seg.name, "criteria": criteria}


def evaluate_customer_segments(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    sales = db.scalars(
        select(SaleModel)
        .where(
            SaleModel.company_id == current_user.company_id,
            SaleModel.customer_id == customer_id,
            SaleModel.status.in_(("confirmed", "paid")),
        )
        .order_by(SaleModel.created_at.desc())
    ).all()

    frequency = len(sales)
    total_spend = sum((s.total_amount for s in sales), Decimal("0.000000"))
    recency_days = 9999
    if sales:
        latest = sales[0].created_at
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        recency_days = (datetime.now(timezone.utc) - latest).days

    addr = db.scalar(
        select(CustomerAddressModel)
        .where(
            CustomerAddressModel.company_id == current_user.company_id, CustomerAddressModel.customer_id == customer_id
        )
        .order_by(CustomerAddressModel.is_primary.desc())
    )
    zone = addr.city if addr else ""

    segs = db.scalars(
        select(CustomerSegmentModel).where(
            CustomerSegmentModel.company_id == current_user.company_id, CustomerSegmentModel.is_active.is_(True)
        )
    ).all()
    matched = []
    breakdown = []
    for s in segs:
        crit = json.loads(s.criteria_json)
        match_freq = frequency >= crit.get("min_frequency", 0)
        match_spend = total_spend >= Decimal(crit.get("min_spend", "0"))
        match_rec = recency_days <= crit.get("max_recency_days", 9999)
        match_zone = not crit.get("zone") or (crit.get("zone").lower() in zone.lower())

        is_match = match_freq and match_spend and match_rec and match_zone
        item = {
            "segment_id": str(s.id),
            "name": s.name,
            "matched": is_match,
            "conditions": {
                "frequency": {"actual": frequency, "required": crit.get("min_frequency", 0), "met": match_freq},
                "spend": {"actual": str(total_spend), "required": crit.get("min_spend", "0"), "met": match_spend},
                "recency_days": {
                    "actual": recency_days,
                    "required": crit.get("max_recency_days", 9999),
                    "met": match_rec,
                },
                "zone": {"actual": zone, "required": crit.get("zone"), "met": match_zone},
            },
        }
        breakdown.append(item)
        if is_match:
            matched.append({"id": str(s.id), "name": s.name})

    return {
        "customer_id": str(customer_id),
        "actual_metrics": {
            "frequency": frequency,
            "total_spend": str(total_spend),
            "recency_days": recency_days,
            "zone": zone,
        },
        "matched_segments": matched,
        "evaluation_breakdown": breakdown,
    }
