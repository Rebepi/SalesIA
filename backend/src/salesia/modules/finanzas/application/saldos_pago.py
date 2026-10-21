from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import func, select

from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentReversalModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditReservationModel
from salesia.shared.infrastructure.transactions import RefundModel


def payment_balances(db, company_id, payment, reservation_id=None):
    allocations = db.execute(select(PaymentAllocationModel.sale_id, func.sum(PaymentAllocationModel.allocated_amount)).where(PaymentAllocationModel.company_id == company_id, PaymentAllocationModel.payment_id == payment.id).group_by(PaymentAllocationModel.sale_id)).all()
    refunded = db.execute(select(RefundModel.unapplied_only, func.sum(RefundModel.amount)).where(RefundModel.company_id == company_id, RefundModel.payment_id == payment.id).group_by(RefundModel.unapplied_only)).all()
    refunds = {bool(scope): amount for scope, amount in refunded}
    reversed_amount = db.scalar(select(func.coalesce(func.sum(PaymentReversalModel.amount), 0)).where(PaymentReversalModel.company_id == company_id, PaymentReversalModel.payment_id == payment.id)) or Decimal("0")
    allocated = sum((amount for _, amount in allocations), Decimal("0"))
    refunded_total = sum(refunds.values(), Decimal("0"))
    remaining = max(Decimal("0"), payment.amount - refunded_total - reversed_amount)
    original_assigned = sum((amount for sale_id, amount in allocations if sale_id == payment.sale_id), Decimal("0"))
    reservation_query = select(func.coalesce(func.sum(CustomerCreditReservationModel.amount), 0)).where(CustomerCreditReservationModel.company_id == company_id, CustomerCreditReservationModel.payment_id == payment.id, CustomerCreditReservationModel.status == "active", CustomerCreditReservationModel.expires_at > datetime.now(timezone.utc))
    if reservation_id:
        reservation_query = reservation_query.where(CustomerCreditReservationModel.id != reservation_id)
    reserved = db.scalar(reservation_query) or Decimal("0")
    return {"allocated": allocated, "refunded": refunded_total, "reversed": reversed_amount, "remaining": remaining, "reserved": reserved, "unapplied": max(Decimal("0"), min(remaining, payment.amount - allocated - refunds.get(True, Decimal("0")) - reversed_amount) - reserved), "original_applied": min(remaining, max(Decimal("0"), original_assigned - refunds.get(False, Decimal("0")) - reversed_amount))}
