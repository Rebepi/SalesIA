import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditAllocationModel, CustomerCreditMovementModel, CustomerCreditReservationModel

ZERO = Decimal("0.000000")


def instant(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def credit_book(db, company_id, customer_id, currency=None, reservation_id=None):
    db.flush()
    query = select(CustomerCreditMovementModel).where(CustomerCreditMovementModel.company_id == company_id, CustomerCreditMovementModel.customer_id == customer_id)
    rows = list(db.scalars(query.order_by(CustomerCreditMovementModel.created_at, CustomerCreditMovementModel.id)).all())
    row_map = {row.id: row for row in rows}
    allocations = db.scalars(select(CustomerCreditAllocationModel).join(CustomerCreditMovementModel, CustomerCreditMovementModel.id == CustomerCreditAllocationModel.debit_id).where(CustomerCreditAllocationModel.company_id == company_id, CustomerCreditMovementModel.company_id == company_id, CustomerCreditMovementModel.customer_id == customer_id)).all()
    by_debit = {}
    for allocation in allocations:
        by_debit.setdefault(allocation.debit_id, []).append(allocation)
    warnings = []
    remaining = {}
    projected = []
    now = datetime.now(timezone.utc)
    selected = [row for row in rows if currency is None or row.currency == currency or row.currency is None]
    for row in selected:
        if row.currency is None:
            warnings.append(f"El movimiento {row.id} requiere identificar su moneda con el documento original.")
            continue
        if row.amount_delta > 0:
            remaining[row.id] = row.amount_delta
            continue
        if row.amount_delta == 0:
            continue
        needed = -row.amount_delta
        saved = by_debit.get(row.id, [])
        if saved:
            for link in saved:
                origin = row_map.get(link.credit_id)
                if origin is None or origin.currency != row.currency or link.currency != row.currency or link.amount <= 0 or remaining.get(link.credit_id, ZERO) < link.amount:
                    warnings.append(f"La aplicación {link.id} tiene un origen o importe incompatible y requiere conciliación.")
                    continue
                remaining[link.credit_id] -= link.amount
                needed -= link.amount
                projected.append({"id": str(link.id), "debit_id": str(row.id), "credit_id": str(link.credit_id), "amount": str(link.amount), "currency": row.currency, "historical": False})
        else:
            for credit_id, balance in list(remaining.items()):
                origin = row_map[credit_id]
                if origin.currency != row.currency or balance <= 0 or (origin.expires_at and instant(origin.expires_at) <= instant(row.created_at)):
                    continue
                amount = min(balance, needed)
                remaining[credit_id] -= amount
                needed -= amount
                projected.append({"id": None, "debit_id": str(row.id), "credit_id": str(credit_id), "amount": str(amount), "currency": row.currency, "historical": True})
                if needed == 0:
                    break
        if needed != 0:
            warnings.append(f"El consumo {row.id} no coincide con los créditos de su moneda; diferencia {needed} {row.currency}.")
    reservations = db.scalars(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == company_id, CustomerCreditReservationModel.customer_id == customer_id).order_by(CustomerCreditReservationModel.created_at, CustomerCreditReservationModel.id)).all()
    held = {}
    reservation_items = []
    for reservation in reservations:
        if currency and reservation.currency != currency:
            continue
        active = reservation.status == "active" and instant(reservation.expires_at) > now
        reservation_items.append({"id": str(reservation.id), "sale_id": str(reservation.sale_id), "payment_id": str(reservation.payment_id) if reservation.payment_id else None, "currency": reservation.currency, "amount": str(reservation.amount), "status": "expired" if reservation.status == "active" and not active else reservation.status, "expires_at": reservation.expires_at.isoformat(), "reason": reservation.reason, "version": reservation.version, "sources": json.loads(reservation.sources_json)})
        if active and reservation.id != reservation_id:
            from uuid import UUID
            for item in json.loads(reservation.sources_json):
                identifier = UUID(item["credit_id"])
                held[identifier] = held.get(identifier, ZERO) + Decimal(item["amount"])
    balances = {}
    sources = []
    for credit_id, amount in remaining.items():
        origin = row_map[credit_id]
        expired = bool(origin.expires_at and instant(origin.expires_at) <= now)
        reserved = held.get(credit_id, ZERO)
        if reserved > amount:
            warnings.append(f"Las reservas del crédito {credit_id} superan su remanente y requieren conciliación.")
        summary = balances.setdefault(origin.currency, {"currency": origin.currency, "available_balance": ZERO, "reserved_balance": ZERO, "expired_balance": ZERO, "ledger_balance": ZERO})
        summary["ledger_balance"] += amount
        summary["expired_balance" if expired else "available_balance"] += amount if expired else max(ZERO, amount - reserved)
        summary["reserved_balance"] += ZERO if expired else reserved
        sources.append({"id": str(origin.id), "currency": origin.currency, "original_amount": str(origin.amount_delta), "remaining_amount": str(amount), "reserved_amount": str(reserved), "available_amount": str(ZERO if expired else max(ZERO, amount - reserved)), "expired": expired, "expires_at": origin.expires_at.isoformat() if origin.expires_at else None, "reference_type": origin.reference_type, "reference_id": str(origin.reference_id) if origin.reference_id else None, "created_at": origin.created_at.isoformat()})
    for row in selected:
        if row.currency:
            balances.setdefault(row.currency, {"currency": row.currency, "available_balance": ZERO, "reserved_balance": ZERO, "expired_balance": ZERO, "ledger_balance": ZERO})
    return {"rows": rows, "balances": [{key: str(value) if isinstance(value, Decimal) else value for key, value in summary.items()} for _, summary in sorted(balances.items())], "sources": sources, "reservations": reservation_items, "allocations": projected, "warnings": list(dict.fromkeys(warnings)), "can_apply": not warnings}


def available_credit(db, company_id, customer_id, currency, require_clean=False):
    book = credit_book(db, company_id, customer_id, currency)
    if require_clean and book["warnings"]:
        raise HTTPException(409, " ".join(book["warnings"]))
    return next((Decimal(row["available_balance"]) for row in book["balances"] if row["currency"] == currency), ZERO)


def accrue_credit(db, company_id, customer_id, currency, amount, reference_type, reference_id, notes, expires_at=None):
    if amount <= 0 or len(currency) != 3 or not currency.isalpha() or currency != currency.upper():
        raise HTTPException(422, "El crédito requiere un importe positivo y una moneda de tres letras mayúsculas.")
    balance = available_credit(db, company_id, customer_id, currency)
    movement = CustomerCreditMovementModel(id=uuid4(), company_id=company_id, customer_id=customer_id, currency=currency, movement_type="ACCRUAL", amount_delta=amount, resulting_balance=balance + amount, reference_type=reference_type, reference_id=reference_id, notes=notes, expires_at=expires_at)
    db.add(movement)
    db.flush()
    return movement


def consume_credit(db, company_id, customer_id, currency, amount, sale_id, payment_id, notes, source_ids=None, reservation_id=None, reference_type="SALE", reference_id=None):
    reservation = None
    if reservation_id:
        reservation = db.scalar(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == company_id, CustomerCreditReservationModel.id == reservation_id, CustomerCreditReservationModel.customer_id == customer_id, CustomerCreditReservationModel.sale_id == sale_id).with_for_update())
        if reservation is None or reservation.payment_id is not None or reservation.currency != currency or reservation.status != "active" or instant(reservation.expires_at) <= datetime.now(timezone.utc) or amount > reservation.amount:
            raise HTTPException(409, "La reserva no está disponible para esta venta, moneda e importe.")
        if source_ids:
            raise HTTPException(422, "Use la reserva o seleccione créditos libres en una aplicación separada.")
    book = credit_book(db, company_id, customer_id, currency, reservation_id)
    if book["warnings"]:
        raise HTTPException(409, " ".join(book["warnings"]))
    sources = [source for source in book["sources"] if source["currency"] == currency and Decimal(source["available_amount"]) > 0]
    if reservation:
        reserved_sources = {item["credit_id"]: Decimal(item["amount"]) for item in json.loads(reservation.sources_json)}
        sources = [{**source, "available_amount": str(min(Decimal(source["available_amount"]), reserved_sources[source["id"]]))} for source in sources if source["id"] in reserved_sources]
    if source_ids:
        selected = {str(identifier) for identifier in source_ids}
        eligible = {source["id"] for source in sources}
        if not selected.issubset(eligible):
            raise HTTPException(409, "Uno de los créditos elegidos no está disponible para el cliente y la moneda de la venta.")
        sources = [source for source in sources if source["id"] in selected]
    sources.sort(key=lambda source: (instant(datetime.fromisoformat(source["expires_at"])) if source["expires_at"] else datetime.max.replace(tzinfo=timezone.utc), instant(datetime.fromisoformat(source["created_at"])), source["id"]))
    if amount <= 0 or sum((Decimal(source["available_amount"]) for source in sources), ZERO) < amount:
        raise HTTPException(409, "Los créditos seleccionados no cubren el importe solicitado en la moneda de la venta.")
    from uuid import UUID
    for link in book["allocations"]:
        if link["historical"]:
            db.add(CustomerCreditAllocationModel(company_id=company_id, debit_id=UUID(link["debit_id"]), credit_id=UUID(link["credit_id"]), currency=link["currency"], amount=Decimal(link["amount"])))
    balance = next((Decimal(row["available_balance"]) for row in book["balances"] if row["currency"] == currency), ZERO)
    movement = CustomerCreditMovementModel(id=uuid4(), company_id=company_id, customer_id=customer_id, currency=currency, payment_id=payment_id, movement_type="REDEMPTION", amount_delta=-amount, resulting_balance=balance - amount, reference_type=reference_type, reference_id=reference_id or sale_id, notes=notes)
    db.add(movement)
    db.flush()
    needed = amount
    consumed = {}
    for source in sources:
        applied = min(needed, Decimal(source["available_amount"]))
        db.add(CustomerCreditAllocationModel(company_id=company_id, debit_id=movement.id, credit_id=UUID(source["id"]), currency=currency, amount=applied))
        consumed[source["id"]] = applied
        needed -= applied
        if needed == 0:
            break
    if reservation:
        reservation.amount -= amount
        reservation.version += 1
        reservation.status = "applied" if reservation.amount == 0 else "active"
        reservation.sources_json = json.dumps([{"credit_id": item["credit_id"], "amount": str(Decimal(item["amount"]) - consumed.get(item["credit_id"], ZERO))} for item in json.loads(reservation.sources_json) if Decimal(item["amount"]) > consumed.get(item["credit_id"], ZERO)])
    db.flush()
    movement.resulting_balance = available_credit(db, company_id, customer_id, currency)
    return movement
