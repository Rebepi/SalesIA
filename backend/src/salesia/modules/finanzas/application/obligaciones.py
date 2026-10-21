import json
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure.models.obligaciones import CostBudgetModel, CostCenterModel, ExpenseAllocationModel, ExpenseModel, PayableInstallmentModel, PayableModel, PayablePaymentModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import SupplierBalanceMovementModel
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument
from salesia.modules.organizacion.application.periodos import business_date, require_open_month, require_open_period
from salesia.shared.infrastructure.transactions import claim_request, complete_request
from salesia.modules.finanzas.application.saldos_proveedor import allocate_supplier_credit, refresh_supplier_claims


def scoped(db, model, user, identifier, lock=False):
    statement = select(model).where(model.id == identifier, model.company_id == user.company_id)
    row = db.scalar(statement.with_for_update() if lock else statement)
    if row is None:
        raise HTTPException(404, "Registro no encontrado en la empresa activa.")
    return row


def audit(db, user, action, row, diff):
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type=type(row).__name__, entity_id=row.id, diff=diff, category="FINANCE")


def payable_data(db, row, detailed=False):
    data = {"id": str(row.id), "supplier_id": str(row.supplier_id), "document_number": row.document_number, "purchase_order_id": str(row.purchase_order_id) if row.purchase_order_id else None, "currency": row.currency, "amount": str(row.amount), "paid_amount": str(row.paid_amount), "balance": str(row.amount - row.paid_amount), "issue_date": row.issue_date.isoformat(), "due_date": row.due_date.isoformat(), "status": row.status, "version": row.version, "notes": row.notes}
    supplier = db.scalar(select(Supplier).where(Supplier.id == row.supplier_id, Supplier.company_id == row.company_id))
    data["invoice_match_id"] = str(row.invoice_match_id) if row.invoice_match_id else None
    data["supplier_name"] = supplier.legal_name if supplier else "Proveedor"
    if row.status == "cancelled":
        data["balance"] = "0.000000"
    if detailed:
        data["installments"] = [{"id": str(item.id), "sequence": item.sequence, "due_date": item.due_date.isoformat(), "amount": str(item.amount), "paid_amount": str(item.paid_amount)} for item in db.scalars(select(PayableInstallmentModel).where(PayableInstallmentModel.company_id == row.company_id, PayableInstallmentModel.payable_id == row.id).order_by(PayableInstallmentModel.sequence)).all()]
        data["payments"] = [{"id": str(item.id), "amount": str(item.amount), "date": item.payment_date.isoformat(), "method": item.method, "reference": item.reference, "status": item.status, "reversal_reason": item.reversal_reason} for item in db.scalars(select(PayablePaymentModel).where(PayablePaymentModel.company_id == row.company_id, PayablePaymentModel.payable_id == row.id).order_by(PayablePaymentModel.created_at)).all()]
    return data


def create_payable(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "payables.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.issue_date)
    supplier = scoped(db, Supplier, user, payload.supplier_id)
    if not supplier.is_active:
        raise HTTPException(409, "El proveedor está inactivo.")
    if payload.purchase_order_id and not payload.invoice_match_id:
        raise HTTPException(409, "Concilia la factura por línea antes de generar la obligación de la compra.")
    if payload.invoice_match_id:
        from salesia.modules.inventario.application.compras_costos_conciliacion import validate_match_for_payable
        validate_match_for_payable(db, user, payload)
    if payload.purchase_order_id:
        order = scoped(db, SupplyDocument, user, payload.purchase_order_id)
        if order.supplier_claim_id or json.loads(order.details_json or "{}").get("no_additional_debt"):
            raise HTTPException(409, "Una reposición de proveedor sin nueva deuda no genera una cuenta por pagar.")
        if order.kind != "PURCHASE_ORDER" or order.supplier_id != supplier.id or order.status in ("cancelled", "draft", "submitted"):
            raise HTTPException(409, "Vincula una orden aprobada del mismo proveedor.")
        details = json.loads(order.details_json or "{}")
        if details.get("currency", supplier.currency) != payload.currency:
            raise HTTPException(422, "La moneda debe coincidir con la orden vinculada.")
    number = payload.document_number.strip().upper()
    if not number:
        raise HTTPException(422, "El documento es obligatorio.")
    duplicate = db.scalar(select(PayableModel.id).where(PayableModel.company_id == user.company_id, PayableModel.supplier_id == supplier.id, PayableModel.document_number == number))
    if duplicate:
        raise HTTPException(409, "La obligación de este proveedor ya está registrada.")
    schedule = sorted(payload.installments, key=lambda item: item.due_date)
    row = PayableModel(company_id=user.company_id, supplier_id=supplier.id, purchase_order_id=payload.purchase_order_id, document_number=number, currency=payload.currency, amount=payload.amount, paid_amount=Decimal("0"), issue_date=payload.issue_date, due_date=schedule[-1].due_date if schedule else payload.due_date, created_by=user.user_id, notes=payload.notes, status="open", version=1)
    db.add(row)
    row.invoice_match_id = payload.invoice_match_id
    db.flush()
    for index, item in enumerate(schedule or [payload], 1):
        db.add(PayableInstallmentModel(company_id=user.company_id, payable_id=row.id, sequence=index, due_date=item.due_date, amount=item.amount, paid_amount=Decimal("0")))
    db.flush()
    result = payable_data(db, row, True)
    audit(db, user, "CREATE_PAYABLE", row, result)
    complete_request(record, result)
    db.commit()
    return result


def list_payables(db, user, status=None, supplier_id=None, limit=50, offset=0):
    statement = select(PayableModel).where(PayableModel.company_id == user.company_id)
    if status:
        statement = statement.where(PayableModel.status == status)
    if supplier_id:
        statement = statement.where(PayableModel.supplier_id == supplier_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = db.scalars(statement.order_by(PayableModel.due_date, PayableModel.id).offset(offset).limit(limit)).all()
    totals = db.execute(select(PayableModel.currency, func.sum(PayableModel.amount - PayableModel.paid_amount)).where(PayableModel.company_id == user.company_id, PayableModel.status.in_(("open", "partial"))).group_by(PayableModel.currency)).all()
    return {"items": [payable_data(db, row) for row in rows], "total_count": total, "balances_by_currency": {currency: str(amount) for currency, amount in totals}}


def post_payable_payment(db, user, payable_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"payables.pay:{payable_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.payment_date)
    row = scoped(db, PayableModel, user, payable_id, True)
    if row.version != payload.version or row.status not in ("open", "partial"):
        raise HTTPException(409, "La obligación cambió o no admite pagos.")
    if payload.payment_date > business_date(db, user.company_id):
        raise HTTPException(422, "Registra un pago efectuado; los pagos futuros permanecen como vencimientos pendientes.")
    if payload.payment_date < row.issue_date:
        raise HTTPException(422, "El pago no puede ser anterior a la obligación.")
    if payload.amount > row.amount - row.paid_amount:
        raise HTTPException(422, "El pago supera el saldo pendiente.")
    installments = db.scalars(select(PayableInstallmentModel).where(PayableInstallmentModel.company_id == user.company_id, PayableInstallmentModel.payable_id == row.id).order_by(PayableInstallmentModel.due_date, PayableInstallmentModel.sequence).with_for_update()).all()
    remaining, allocations = payload.amount, []
    for item in installments:
        applied = min(remaining, item.amount - item.paid_amount)
        if applied > 0:
            item.paid_amount += applied
            remaining -= applied
            allocations.append({"installment_id": str(item.id), "amount": str(applied)})
    if remaining:
        raise HTTPException(409, "El cronograma no coincide con el saldo de la obligación.")
    payment = PayablePaymentModel(company_id=user.company_id, payable_id=row.id, amount=payload.amount, payment_date=payload.payment_date, method=payload.method, reference=payload.reference.strip(), created_by=user.user_id, allocations_json=json.dumps(allocations), status="posted")
    db.add(payment)
    db.flush()
    if payload.method == "SUPPLIER_CREDIT":
        balance = supplier_balance(db, user, row.supplier_id, row.currency)
        if payload.amount > balance:
            raise HTTPException(409, "El saldo a favor con el proveedor no cubre este importe.")
        credit_allocations = allocate_supplier_credit(db, user.company_id, row.supplier_id, row.currency, payload.amount, payload.payment_date, row.purchase_order_id, "payment")
        db.add(SupplierBalanceMovementModel(company_id=user.company_id, supplier_id=row.supplier_id, currency=row.currency, amount_delta=-payload.amount, movement_date=payload.payment_date, kind="application", reference=payload.reference.strip(), payment_id=payment.id, source_document_id=row.purchase_order_id, allocations_json=json.dumps(credit_allocations), created_by=user.user_id, notes=f"Aplicado a {row.document_number}"))
    row.paid_amount += payload.amount
    row.status = "paid" if row.paid_amount == row.amount else "partial"
    row.version += 1
    db.flush()
    if payload.method == "SUPPLIER_CREDIT":
        refresh_supplier_claims(db, user, row.supplier_id, row.currency)
    audit(db, user, "PAY_PAYABLE", row, {"payment_id": str(payment.id), "amount": str(payload.amount), "allocations": allocations})
    result = payable_data(db, row, True)
    complete_request(record, result)
    db.commit()
    return result


def reverse_payable_payment(db, user, payable_id, payment_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"payables.reverse:{payment_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = scoped(db, PayableModel, user, payable_id, True)
    payment = scoped(db, PayablePaymentModel, user, payment_id, True)
    if row.version != payload.version or payment.payable_id != row.id or payment.status != "posted":
        raise HTTPException(409, "El pago cambió o ya fue revertido.")
    require_open_period(db, user.company_id, payment.payment_date)
    for item in json.loads(payment.allocations_json):
        installment = scoped(db, PayableInstallmentModel, user, UUID(item["installment_id"]), True)
        installment.paid_amount -= Decimal(item["amount"])
    row.paid_amount -= payment.amount
    row.status = "open" if row.paid_amount == 0 else "partial"
    row.version += 1
    payment.status, payment.reversal_reason = "reversed", payload.reason
    if payment.method == "SUPPLIER_CREDIT":
        original = db.scalar(select(SupplierBalanceMovementModel).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.payment_id == payment.id, SupplierBalanceMovementModel.kind == "application").with_for_update())
        if original is None or -original.amount_delta != payment.amount:
            raise HTTPException(409, "El pago no coincide con su aplicación en el libro de saldos del proveedor.")
        db.add(SupplierBalanceMovementModel(company_id=user.company_id, supplier_id=row.supplier_id, currency=row.currency, amount_delta=payment.amount, movement_date=business_date(db, user.company_id), kind="reversal", reference=str(payment.id), payment_id=payment.id, source_document_id=row.purchase_order_id, reversal_of_id=original.id, allocations_json=original.allocations_json or "[]", created_by=user.user_id, notes=payload.reason))
        refresh_supplier_claims(db, user, row.supplier_id, row.currency)
    audit(db, user, "REVERSE_PAYABLE_PAYMENT", row, {"payment_id": str(payment.id), "reason": payload.reason})
    result = payable_data(db, row, True)
    complete_request(record, result)
    db.commit()
    return result


def cancel_payable(db, user, payable_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"payables.cancel:{payable_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = scoped(db, PayableModel, user, payable_id, True)
    require_open_period(db, user.company_id, row.issue_date)
    if row.version != payload.version or row.status != "open" or row.paid_amount:
        raise HTTPException(409, "Solo se cancela una obligación vigente sin pagos aplicados.")
    row.status, row.version = "cancelled", row.version + 1
    audit(db, user, "CANCEL_PAYABLE", row, {"reason": payload.reason})
    result = payable_data(db, row, True)
    complete_request(record, result)
    db.commit()
    return result


def list_centers(db, user):
    return [{"id": str(row.id), "code": row.code, "name": row.name} for row in db.scalars(select(CostCenterModel).where(CostCenterModel.company_id == user.company_id).order_by(CostCenterModel.code)).all()]


def supplier_balance(db, user, supplier_id, currency):
    return db.scalar(select(func.coalesce(func.sum(SupplierBalanceMovementModel.amount_delta), 0)).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.supplier_id == supplier_id, SupplierBalanceMovementModel.currency == currency)) or Decimal("0")


def create_supplier_balance(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "supplier_balances.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.movement_date)
    scoped(db, Supplier, user, payload.supplier_id, True)
    if payload.movement_date > business_date(db, user.company_id):
        raise HTTPException(422, "Registra un movimiento de saldo ya efectuado, con fecha de hoy o anterior.")
    if not payload.reference.strip():
        raise HTTPException(422, "La referencia del movimiento no puede estar vacía.")
    if payload.kind == "refund" and payload.source_document_id:
        raise HTTPException(422, "El reintegro reconstruye sus créditos de origen; no vincules una compra adicional.")
    if payload.source_document_id:
        source = scoped(db, SupplyDocument, user, payload.source_document_id)
        if source.supplier_claim_id or json.loads(source.details_json or "{}").get("no_additional_debt"):
            raise HTTPException(409, "La reposición sin nueva deuda no admite anticipos ni créditos adicionales.")
        if source.kind != "PURCHASE_ORDER" or source.supplier_id != payload.supplier_id or json.loads(source.details_json or "{}").get("currency", "USD") != payload.currency:
            raise HTTPException(422, "El anticipo o crédito debe vincularse a una compra del mismo proveedor y moneda.")
    balance = supplier_balance(db, user, payload.supplier_id, payload.currency)
    if payload.kind == "refund" and payload.amount > balance:
        raise HTTPException(409, "El reintegro supera el saldo a favor con el proveedor.")
    duplicate = db.scalar(select(SupplierBalanceMovementModel.id).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.supplier_id == payload.supplier_id, SupplierBalanceMovementModel.kind == payload.kind, func.upper(SupplierBalanceMovementModel.reference) == payload.reference.strip().upper(), SupplierBalanceMovementModel.currency == payload.currency))
    if duplicate:
        raise HTTPException(409, "La referencia de este movimiento ya fue registrada.")
    amount_delta = -payload.amount if payload.kind == "refund" else payload.amount
    credit_allocations = allocate_supplier_credit(db, user.company_id, payload.supplier_id, payload.currency, payload.amount, payload.movement_date) if payload.kind == "refund" else []
    row = SupplierBalanceMovementModel(company_id=user.company_id, supplier_id=payload.supplier_id, currency=payload.currency, amount_delta=amount_delta, movement_date=payload.movement_date, kind=payload.kind, reference=payload.reference.strip().upper(), source_document_id=payload.source_document_id, allocations_json=json.dumps(credit_allocations), created_by=user.user_id, notes=payload.notes)
    db.add(row)
    db.flush()
    result = {"id": str(row.id), "balance": str(balance + amount_delta), "currency": row.currency}
    if payload.kind == "refund":
        refresh_supplier_claims(db, user, payload.supplier_id, payload.currency)
    audit(db, user, "SUPPLIER_BALANCE_MOVEMENT", row, result)
    complete_request(record, result)
    db.commit()
    return result


def list_supplier_balances(db, user):
    rows = db.execute(select(SupplierBalanceMovementModel.supplier_id, SupplierBalanceMovementModel.currency, func.sum(SupplierBalanceMovementModel.amount_delta)).where(SupplierBalanceMovementModel.company_id == user.company_id).group_by(SupplierBalanceMovementModel.supplier_id, SupplierBalanceMovementModel.currency)).all()
    suppliers = {str(row.id): row.legal_name for row in db.scalars(select(Supplier).where(Supplier.company_id == user.company_id)).all()}
    return [{"supplier_id": str(supplier_id), "supplier_name": suppliers.get(str(supplier_id), "Proveedor histórico"), "currency": currency, "balance": str(balance)} for supplier_id, currency, balance in rows]


def create_center(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "cost_centers.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    code = payload.code.upper()
    if db.scalar(select(CostCenterModel.id).where(CostCenterModel.company_id == user.company_id, CostCenterModel.code == code)):
        raise HTTPException(409, "El código de centro de costo ya existe.")
    row = CostCenterModel(company_id=user.company_id, code=code, name=payload.name.strip())
    db.add(row)
    db.flush()
    result = {"id": str(row.id), "code": row.code, "name": row.name}
    audit(db, user, "CREATE_COST_CENTER", row, result)
    complete_request(record, result)
    db.commit()
    return result


def expense_data(db, row):
    allocations = db.scalars(select(ExpenseAllocationModel).where(ExpenseAllocationModel.company_id == row.company_id, ExpenseAllocationModel.expense_id == row.id)).all()
    return {"id": str(row.id), "petty_cash_advance_id": str(row.petty_cash_advance_id) if row.petty_cash_advance_id else None, "title": row.title, "category": row.category, "document_number": row.document_number, "expense_date": row.expense_date.isoformat(), "currency": row.currency, "amount": str(row.amount), "status": row.status, "version": row.version, "notes": row.notes, "created_by": str(row.created_by), "approved_by": str(row.approved_by) if row.approved_by else None, "allocations": [{"cost_center_id": str(item.cost_center_id), "amount": str(item.amount)} for item in allocations]}


def create_expense(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "expenses.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.expense_date)
    document_number = payload.document_number.strip().upper() if payload.document_number else None
    if document_number and db.scalar(select(ExpenseModel.id).where(ExpenseModel.company_id == user.company_id, func.upper(func.trim(ExpenseModel.document_number)) == document_number, ExpenseModel.status.notin_(("cancelled", "rejected"))).limit(1)):
        raise HTTPException(409, "El comprobante ya está registrado como gasto.")
    for allocation in payload.allocations:
        scoped(db, CostCenterModel, user, allocation.cost_center_id)
    row = ExpenseModel(company_id=user.company_id, title=payload.title.strip(), category=payload.category.strip(), document_number=document_number, expense_date=payload.expense_date, currency=payload.currency, amount=payload.amount, created_by=user.user_id, notes=payload.notes, status="draft", version=1)
    db.add(row)
    db.flush()
    for allocation in payload.allocations:
        db.add(ExpenseAllocationModel(company_id=user.company_id, expense_id=row.id, **allocation.model_dump()))
    db.flush()
    result = expense_data(db, row)
    audit(db, user, "CREATE_EXPENSE", row, result)
    complete_request(record, result)
    db.commit()
    return result


def list_expenses(db, user, limit=50, offset=0):
    statement = select(ExpenseModel).where(ExpenseModel.company_id == user.company_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    return {"items": [expense_data(db, row) for row in db.scalars(statement.order_by(ExpenseModel.expense_date.desc(), ExpenseModel.id).offset(offset).limit(limit)).all()], "total_count": total}


def expense_action(db, user, expense_id, action, payload, key):
    record, cached = claim_request(db, user.company_id, f"expenses.{action}:{expense_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = scoped(db, ExpenseModel, user, expense_id, True)
    require_open_period(db, user.company_id, row.expense_date)
    transitions = {"submit": ("draft", "pending"), "approve": ("pending", "approved"), "reject": ("pending", "rejected"), "cancel": ("draft", "cancelled")}
    if action not in transitions:
        raise HTTPException(422, "Acción desconocida.")
    initial, target = transitions[action]
    if row.version != payload.version or row.status != initial:
        raise HTTPException(409, "El gasto cambió o no admite esta acción.")
    if action in ("approve", "reject"):
        if "approvals:manage" not in user.permissions:
            raise HTTPException(403, "Se requiere permiso para resolver aprobaciones.")
        from salesia.modules.seguridad.application.separacion_funciones import enforce
        enforce(db, user, "expense", [row.created_by], "Expense", row.id)
        if row.created_by == user.user_id:
            raise HTTPException(403, "El autor no puede resolver la aprobación de su propio gasto.")
        if action == "approve":
            verify_expense_budget(db, user, row)
            row.approved_by = user.user_id
    row.status, row.version = target, row.version + 1
    audit(db, user, f"EXPENSE_{action.upper()}", row, {"reason": payload.reason, "status": target})
    result = expense_data(db, row)
    complete_request(record, result)
    db.commit()
    return result


def budget_consumed(db, user, center_id, period, currency):
    start = date.fromisoformat(period + "-01")
    end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
    return db.scalar(select(func.coalesce(func.sum(ExpenseAllocationModel.amount), 0)).join(ExpenseModel, ExpenseModel.id == ExpenseAllocationModel.expense_id).where(ExpenseAllocationModel.company_id == user.company_id, ExpenseAllocationModel.cost_center_id == center_id, ExpenseModel.company_id == user.company_id, ExpenseModel.status == "approved", ExpenseModel.currency == currency, ExpenseModel.expense_date >= start, ExpenseModel.expense_date < end)) or Decimal("0")


def verify_expense_budget(db, user, expense):
    period = expense.expense_date.strftime("%Y-%m")
    for allocation in db.scalars(select(ExpenseAllocationModel).where(ExpenseAllocationModel.company_id == user.company_id, ExpenseAllocationModel.expense_id == expense.id)).all():
        budget = db.scalar(select(CostBudgetModel).where(CostBudgetModel.company_id == user.company_id, CostBudgetModel.cost_center_id == allocation.cost_center_id, CostBudgetModel.period == period, CostBudgetModel.currency == expense.currency).with_for_update())
        if budget and budget_consumed(db, user, allocation.cost_center_id, period, expense.currency) + allocation.amount > budget.amount:
            raise HTTPException(409, "El gasto supera el presupuesto del centro de costo. Amplía el presupuesto con autorización antes de aprobar.")


def save_budget(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "budgets.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_month(db, user.company_id, payload.period, ["expenses"])
    scoped(db, CostCenterModel, user, payload.cost_center_id)
    row = db.scalar(select(CostBudgetModel).where(CostBudgetModel.company_id == user.company_id, CostBudgetModel.cost_center_id == payload.cost_center_id, CostBudgetModel.period == payload.period, CostBudgetModel.currency == payload.currency).with_for_update())
    if (row.version if row else 0) != payload.version:
        raise HTTPException(409, "El presupuesto cambió; recarga antes de guardarlo.")
    if payload.amount < budget_consumed(db, user, payload.cost_center_id, payload.period, payload.currency):
        raise HTTPException(409, "El presupuesto no puede quedar por debajo de los gastos aprobados.")
    if row:
        row.amount, row.version = payload.amount, row.version + 1
    else:
        row = CostBudgetModel(company_id=user.company_id, cost_center_id=payload.cost_center_id, period=payload.period, currency=payload.currency, amount=payload.amount, version=1)
        db.add(row)
    db.flush()
    result = {"id": str(row.id), "version": row.version, "amount": str(row.amount)}
    audit(db, user, "SAVE_COST_BUDGET", row, result)
    complete_request(record, result)
    db.commit()
    return result


def list_budgets(db, user):
    result = []
    for row in db.scalars(select(CostBudgetModel).where(CostBudgetModel.company_id == user.company_id).order_by(CostBudgetModel.period.desc(), CostBudgetModel.currency)).all():
        consumed = budget_consumed(db, user, row.cost_center_id, row.period, row.currency)
        result.append({"id": str(row.id), "cost_center_id": str(row.cost_center_id), "period": row.period, "currency": row.currency, "amount": str(row.amount), "consumed": str(consumed), "remaining": str(row.amount - consumed), "version": row.version})
    return result
