import json
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.finanzas.infrastructure.models.obligaciones import SupplierBalanceMovementModel


def supplier_credit_lots(db, company_id, supplier_id, currency):
    db.flush()
    rows = db.scalars(select(SupplierBalanceMovementModel).where(SupplierBalanceMovementModel.company_id == company_id, SupplierBalanceMovementModel.supplier_id == supplier_id, SupplierBalanceMovementModel.currency == currency).order_by(SupplierBalanceMovementModel.created_at, SupplierBalanceMovementModel.id)).all()
    lots, order, pending_legacy = {}, [], Decimal("0")
    for row in rows:
        allocations = json.loads(row.allocations_json or "[]")
        if row.amount_delta > 0 and row.kind == "reversal" and allocations:
            if sum((Decimal(item["amount"]) for item in allocations), Decimal("0")) != row.amount_delta:
                raise HTTPException(409, "La reversión de saldo no coincide con las aplicaciones originales.")
            for item in allocations:
                identifier, amount = item["movement_id"], Decimal(item["amount"])
                if identifier not in lots or lots[identifier]["remaining"] + amount > lots[identifier]["amount"]:
                    raise HTTPException(409, "No se pudo reconstruir el crédito de origen de la reversión.")
                lots[identifier]["remaining"] += amount
            continue
        if row.amount_delta > 0:
            identifier = str(row.id)
            covered = min(pending_legacy, row.amount_delta)
            pending_legacy -= covered
            lots[identifier] = {"movement_id": identifier, "amount": row.amount_delta, "remaining": row.amount_delta - covered, "claim_id": str(row.source_claim_id) if row.source_claim_id else None, "date": row.movement_date, "reference": row.reference, "kind": row.kind, "source_document_id": str(row.source_document_id) if row.source_document_id else None}
            order.append(identifier)
            continue
        needed = -row.amount_delta
        if allocations:
            if sum((Decimal(item["amount"]) for item in allocations), Decimal("0")) != needed:
                raise HTTPException(409, "La aplicación no coincide con el importe descontado del saldo.")
            for item in allocations:
                identifier, amount = item["movement_id"], Decimal(item["amount"])
                if amount <= 0 or identifier not in lots or lots[identifier]["remaining"] < amount:
                    raise HTTPException(409, "El libro de créditos no coincide con sus aplicaciones; revisa los movimientos de origen.")
                lots[identifier]["remaining"] -= amount
        else:
            for identifier in order:
                applied = min(needed, lots[identifier]["remaining"])
                lots[identifier]["remaining"] -= applied
                needed -= applied
            pending_legacy += needed
    if pending_legacy > 0:
        raise HTTPException(409, "El historial de saldos del proveedor contiene un saldo negativo sin crédito de origen.")
    return [lots[identifier] for identifier in order]


def allocate_supplier_credit(db, company_id, supplier_id, currency, amount, on_date, purchase_order_id=None, purpose="refund"):
    lots = supplier_credit_lots(db, company_id, supplier_id, currency)
    remaining, allocations = amount, []
    for lot in lots:
        if lot["date"] > on_date:
            continue
        if purpose == "payment" and lot["kind"] == "advance" and lot["source_document_id"] and lot["source_document_id"] != str(purchase_order_id):
            continue
        applied = min(remaining, lot["remaining"])
        if applied > 0:
            allocations.append({"movement_id": lot["movement_id"], "claim_id": lot["claim_id"], "amount": str(applied)})
            remaining -= applied
        if remaining == 0:
            break
    if remaining > 0:
        raise HTTPException(409, "El saldo a favor disponible en la fecha del movimiento no cubre el importe.")
    return allocations


def supplier_claim_credit_totals(db, company_id, supplier_id, currency, claim_id):
    lots = supplier_credit_lots(db, company_id, supplier_id, currency)
    selected = [item for item in lots if item["claim_id"] == str(claim_id)]
    issued = sum((item["amount"] for item in selected), Decimal("0"))
    available = sum((item["remaining"] for item in selected), Decimal("0"))
    return {"issued": issued, "available": available, "applied": issued - available}


def refresh_supplier_claims(db, user, supplier_id, currency):
    from salesia.modules.inventario.application.reclamos_proveedor import synchronize_claim
    from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
    db.flush()
    rows = db.scalars(select(SupplierClaimModel).where(SupplierClaimModel.company_id == user.company_id, SupplierClaimModel.supplier_id == supplier_id, SupplierClaimModel.currency == currency, SupplierClaimModel.status.notin_(("open", "cancelled", "rejected")), SupplierClaimModel.resolution.in_(("credit", "discount")))).all()
    for row in rows:
        synchronize_claim(db, user, row)


def supplier_credit_detail(db, user, supplier_id, currency):
    from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
    from salesia.modules.inventario.infrastructure_models import Supplier
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == supplier_id))
    if supplier is None:
        raise HTTPException(404, "Proveedor no encontrado en la empresa activa.")
    lots = supplier_credit_lots(db, user.company_id, supplier_id, currency)
    claim_ids = [item["claim_id"] for item in lots if item["claim_id"]]
    from uuid import UUID
    claims = {str(row.id): row.code for row in db.scalars(select(SupplierClaimModel).where(SupplierClaimModel.company_id == user.company_id, SupplierClaimModel.id.in_([UUID(identifier) for identifier in claim_ids]))).all()} if claim_ids else {}
    rows = db.scalars(select(SupplierBalanceMovementModel).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.supplier_id == supplier_id, SupplierBalanceMovementModel.currency == currency).order_by(SupplierBalanceMovementModel.created_at.desc(), SupplierBalanceMovementModel.id)).all()
    references = {item["movement_id"]: item["reference"] for item in lots}
    return {"supplier_id": str(supplier_id), "supplier_name": supplier.legal_name, "currency": currency, "available": str(sum((item["remaining"] for item in lots), Decimal("0"))), "lots": [{**item, "amount": str(item["amount"]), "remaining": str(item["remaining"]), "date": item["date"].isoformat(), "claim_code": claims.get(item["claim_id"])} for item in lots], "movements": [{"id": str(row.id), "kind": row.kind, "date": row.movement_date.isoformat(), "amount": str(row.amount_delta), "reference": row.reference, "notes": row.notes, "payment_id": str(row.payment_id) if row.payment_id else None, "reversal_of_id": str(row.reversal_of_id) if row.reversal_of_id else None, "allocations": [{**item, "reference": references.get(item["movement_id"], "Crédito histórico"), "claim_code": claims.get(item.get("claim_id"))} for item in json.loads(row.allocations_json or "[]")]} for row in rows]}
