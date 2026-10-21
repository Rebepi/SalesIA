from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.fidelizacion import LoyaltyAccrualModel, LoyaltyReversalModel
from salesia.modules.clientes.infrastructure.models import CustomerLoyaltyLedgerModel, CustomerModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def get_customer_loyalty(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    movements = db.scalars(
        select(CustomerLoyaltyLedgerModel)
        .where(
            CustomerLoyaltyLedgerModel.company_id == current_user.company_id,
            CustomerLoyaltyLedgerModel.customer_id == customer_id,
        )
        .order_by(CustomerLoyaltyLedgerModel.created_at.desc())
    ).all()

    current_points = movements[0].balance_after if movements else 0
    tier = "Bronce"
    if current_points >= 5000:
        tier = "Platino"
    elif current_points >= 2000:
        tier = "Oro"
    elif current_points >= 500:
        tier = "Plata"

    return {
        "customer_id": str(customer_id),
        "current_points": current_points,
        "tier": tier,
        "total_movements": len(movements),
        "movements": [
            {
                "id": str(m.id),
                "movement_type": m.movement_type,
                "reference_type": m.reference_type,
                "reference_id": m.reference_id,
                "points": m.points,
                "balance_after": m.balance_after,
                "reason": m.reason,
                "created_at": m.created_at.isoformat(),
            }
            for m in movements
        ],
    }


def accrue_loyalty_points(customer_id: UUID, req: LoyaltyAccrualModel, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    last_mov = db.scalar(
        select(CustomerLoyaltyLedgerModel)
        .where(
            CustomerLoyaltyLedgerModel.company_id == current_user.company_id,
            CustomerLoyaltyLedgerModel.customer_id == customer_id,
        )
        .order_by(CustomerLoyaltyLedgerModel.created_at.desc())
    )
    current_balance = last_mov.balance_after if last_mov else 0
    new_balance = current_balance + req.points

    mov = CustomerLoyaltyLedgerModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        movement_type="accrual",
        reference_type=req.reference_type,
        reference_id=req.reference_id,
        points=req.points,
        balance_after=new_balance,
        reason=req.reason or "Puntos por compra comercial",
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)

    return {
        "customer_id": str(customer_id),
        "accrued_points": req.points,
        "new_balance": new_balance,
        "movement_id": str(mov.id),
    }


def reverse_loyalty_points(customer_id: UUID, req: LoyaltyReversalModel, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    already_reversed = db.scalar(
        select(CustomerLoyaltyLedgerModel).where(
            CustomerLoyaltyLedgerModel.company_id == current_user.company_id,
            CustomerLoyaltyLedgerModel.customer_id == customer_id,
            CustomerLoyaltyLedgerModel.movement_type == "reversal",
            CustomerLoyaltyLedgerModel.reference_id == req.reference_id,
        )
    )
    if already_reversed:
        return {
            "customer_id": str(customer_id),
            "reversed_points": 0,
            "new_balance": already_reversed.balance_after,
            "status": "already_reversed",
        }

    last_mov = db.scalar(
        select(CustomerLoyaltyLedgerModel)
        .where(
            CustomerLoyaltyLedgerModel.company_id == current_user.company_id,
            CustomerLoyaltyLedgerModel.customer_id == customer_id,
        )
        .order_by(CustomerLoyaltyLedgerModel.created_at.desc())
    )
    current_balance = last_mov.balance_after if last_mov else 0
    deduct = min(req.points, current_balance)
    new_balance = max(0, current_balance - deduct)

    mov = CustomerLoyaltyLedgerModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        movement_type="reversal",
        reference_type=req.reference_type,
        reference_id=req.reference_id,
        points=-deduct,
        balance_after=new_balance,
        reason=req.reason or f"Reversión por nota de crédito / devolución ref {req.reference_id}",
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)

    return {
        "customer_id": str(customer_id),
        "reversed_points": deduct,
        "new_balance": new_balance,
        "status": "completed",
    }
