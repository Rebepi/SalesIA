from datetime import timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, or_, select

from salesia.modules.analitica.application import dashboard_evidence as evidence
from salesia.modules.catalogo.infrastructure.models.productos import ProductProfileModel
from salesia.modules.finanzas.application.cuotas_cobranza import schedule_data
from salesia.modules.finanzas.infrastructure.models.cuotas_cobranza import ReceivableScheduleModel
from salesia.modules.finanzas.infrastructure.models.custodia import CashCustodyAccountModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import PayableInstallmentModel, PayableModel
from salesia.modules.finanzas.infrastructure.models.pagos import TransferProofModel
from salesia.modules.inventario.infrastructure.models.compras import SupplyDocument
from salesia.modules.organizacion.application.perfil_operativo import current as operating_profile
from salesia.modules.organizacion.application.calendario_operativo import effective_calendar
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, InventoryStockModel, PaymentModel, ProductModel, SaleLineModel, SaleModel, WarehouseModel


ZERO = Decimal("0")


def amount(value):
    return str(Decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN))


def metric(value=None, status="available", note="", count=None):
    return {"amount": amount(value) if value is not None else None, "status": status, "note": note, "count": count}


def sale_scope(user, currency, branch_id, category):
    filters = [SaleModel.company_id == user.company_id, SaleModel.currency == currency]
    if branch_id:
        filters.append(SaleModel.branch_id == branch_id)
    if category:
        filters.append(SaleModel.id.in_(select(SaleLineModel.sale_id).join(ProductModel, ProductModel.id == SaleLineModel.product_id).where(SaleLineModel.company_id == user.company_id, ProductModel.company_id == user.company_id, ProductModel.category == category)))
    return filters


def build(db, user, filters, currency, branch_id, category, seller_id, zone, start, now, evidence_key=None):
    calendar = effective_calendar(db, user.company_id)
    today = now.astimezone(ZoneInfo(calendar["timezone"])).date()
    enabled = set(operating_profile(db, user.company_id)["enabled"])
    permissions = set(user.permissions)
    alerts = []
    company = db.get(CompanyModel, user.company_id)
    result = {"currency": currency, "inventory_currency": company.base_currency if company else currency, "as_of": now.isoformat(), "business_date": today.isoformat(), "timezone": calendar["timezone"], "alerts": alerts, "allowed_views": ["sales_analytics", "customer_analytics"], "scope_note": "Facturación y margen: período seleccionado. Cobros: fecha de recepción o verificación. Deudas, existencias y fondos: situación actual; vencimientos según la fecha de la empresa. Una sola moneda por indicador, sin conversión automática."}
    result["export_permissions"] = {"costs": "products:cost:read" in permissions, "payments": "payments:read" in permissions, "cash": "cash:register:manage" in permissions, "inventory": "inventory:read" in permissions, "sales": "sales:read" in permissions}
    evidence_rows = []
    commercial_ids = select(SaleModel.id).where(*filters)
    if evidence_key == "revenue" and "sales:read" in permissions:
        evidence_rows = evidence.sales(db, user, filters)
    if evidence_key == "unassigned" and "sales:read" in permissions:
        evidence_rows = evidence.sales(db, user, [*filters, SaleModel.sales_rep_id.is_(None)])
    if "sales:read" in permissions:
        result["allowed_views"].extend(["sales", "team"])
    if "products:cost:read" in permissions and company and currency != company.base_currency:
        result["margin"] = metric(status="unavailable", note="La moneda de venta difiere de la moneda base de costos y no hay una equivalencia histórica verificada para consolidar el margen.")
    elif "products:cost:read" in permissions:
        line_count, zero_cost, base, cost, partial_base, partial_cost, partial_revenue = db.execute(select(func.count(SaleLineModel.id), func.coalesce(func.sum(case((SaleLineModel.unit_cost_snapshot <= 0, 1), else_=0)), 0), func.coalesce(func.sum(SaleLineModel.subtotal_amount), 0), func.coalesce(func.sum(SaleLineModel.quantity * SaleLineModel.unit_cost_snapshot), 0), func.coalesce(func.sum(case((SaleLineModel.unit_cost_snapshot > 0, SaleLineModel.subtotal_amount), else_=0)), 0), func.coalesce(func.sum(case((SaleLineModel.unit_cost_snapshot > 0, SaleLineModel.quantity * SaleLineModel.unit_cost_snapshot), else_=0)), 0), func.coalesce(func.sum(case((SaleLineModel.unit_cost_snapshot > 0, SaleLineModel.total_amount), else_=0)), 0)).where(SaleLineModel.company_id == user.company_id, SaleLineModel.sale_id.in_(commercial_ids))).one()
        result["margin"] = metric(base - cost if line_count and not zero_cost else None, "review" if zero_cost else "available" if line_count else "empty", "Margen comercial antes de gastos, logística, comisiones y devoluciones; costo histórico. Las líneas con costo cero requieren confirmar su origen antes de publicar un margen consolidado.", int(zero_cost))
        if evidence_key in ("margin", "costs") and "sales:read" in permissions:
            evidence_rows = evidence.lines(db, user, commercial_ids, evidence_key == "costs")
        result["margin"]["percent"] = amount((base - cost) / base * 100) if base > 0 and not zero_cost else None
        if zero_cost:
            period_revenue = db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*filters)) or ZERO
            result["margin"]["partial"] = {"amount": amount(partial_base - partial_cost), "percent": amount((partial_base - partial_cost) / partial_base * 100) if partial_base > 0 else None, "commercial_base": amount(partial_base), "revenue": amount(partial_revenue), "coverage_pct": amount(partial_revenue / period_revenue * 100) if period_revenue > 0 else None, "definition": "Solo líneas con costo registrado positivo, no verificado. Cobertura sobre el total de facturación del mismo período y filtros. No representa el margen del negocio."}
            alerts.append({"key": "costs", "count": zero_cost, "severity": "warning", "title": f"{zero_cost} líneas de venta con costo cero por revisar", "description": "El margen consolidado queda pendiente para evitar mostrar una rentabilidad sin respaldo.", "view": "sales" if "sales:read" in permissions else "sales_analytics"})
    else:
        result["margin"] = metric(status="restricted", note="Requiere permiso para consultar costos.")
    scope = sale_scope(user, currency, branch_id, category)
    if seller_id:
        scope.append(SaleModel.sales_rep_id == seller_id)
    if zone:
        scope.append(SaleModel.branch_id.in_(select(BranchModel.id).where(BranchModel.company_id == user.company_id, or_(BranchModel.code.ilike(f"%{zone}%"), BranchModel.name.ilike(f"%{zone}%")))))
    result["collections"] = metric(status="restricted", note="Requiere permiso de lectura de pagos.")
    result["receivables"] = metric(status="restricted", note="Requiere permiso de lectura de pagos.")
    if "payments:read" in permissions:
        result["allowed_views"].extend(["receivables", "refunds"])
        origin_sales = select(SaleModel.id).where(*scope)
        proofs = select(TransferProofModel.payment_id, func.max(case((TransferProofModel.verified.is_(True), 1), else_=0)).label("verified"), func.min(case((TransferProofModel.verified.is_(True), TransferProofModel.verified_at), else_=None)).label("verified_at")).where(TransferProofModel.company_id == user.company_id).group_by(TransferProofModel.payment_id).subquery()
        verified_at = func.coalesce(proofs.c.verified_at, PaymentModel.created_at)
        payment_filters = [PaymentModel.company_id == user.company_id, PaymentModel.currency == currency, PaymentModel.sale_id.in_(origin_sales), PaymentModel.status.in_(["confirmed", "refunded"]), PaymentModel.payment_method.not_in(["STORE_CREDIT", "RETURN_CREDIT", "EXCHANGE_CREDIT"]), or_(proofs.c.payment_id.is_(None), proofs.c.verified == 1), verified_at <= now]
        if start:
            payment_filters.append(verified_at >= start)
        received = db.scalar(select(func.coalesce(func.sum(PaymentModel.amount), 0)).outerjoin(proofs, proofs.c.payment_id == PaymentModel.id).where(*payment_filters)) or ZERO
        if evidence_key == "collections":
            evidence_rows = [{"id": str(payment.id), "venta_id": str(payment.sale_id), "importe": str(payment.amount), "moneda": payment.currency, "estado": payment.status, "fecha_recepcion": verified.isoformat()} for payment, verified in db.execute(select(PaymentModel, verified_at).outerjoin(proofs, proofs.c.payment_id == PaymentModel.id).where(*payment_filters).order_by(PaymentModel.id)).all()]
        result["collections"] = metric(received, note="Cobros monetarios brutos recibidos o verificados en el período, por sede y categoría de la venta de origen. Incluye anticipos; excluye medios virtuales. No deduce reembolsos ni reversiones.")
        if "credit" not in enabled:
            result["receivables"] = metric(status="inactive", note="El área de crédito está desactivada.")
        else:
            debt_query = select(SaleModel).where(*scope, SaleModel.status == "confirmed", SaleModel.total_amount > SaleModel.paid_amount)
            debt_count = db.scalar(select(func.count()).select_from(debt_query.subquery())) or 0
            total_open = db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount - SaleModel.paid_amount), 0)).where(SaleModel.id.in_(select(SaleModel.id).where(*scope, SaleModel.status == "confirmed", SaleModel.total_amount > SaleModel.paid_amount)))) or ZERO
            if debt_count > 500:
                result["receivables"] = metric(status="unavailable", note="El vencido consolidado requiere revisar una cartera extensa. Consulte Cuentas por cobrar para revisar la información completa; aquí no se publica una suma parcial.")
            else:
                overdue, total, overdue_count, needs_review = ZERO, ZERO, 0, 0
                debts = db.scalars(debt_query).all()
                schedules = {row.sale_id: row for row in db.scalars(select(ReceivableScheduleModel).where(ReceivableScheduleModel.company_id == user.company_id, ReceivableScheduleModel.sale_id.in_([sale.id for sale in debts]))).all()} if debts else {}
                for sale in debts:
                    balance = max(ZERO, sale.total_amount - sale.paid_amount)
                    total += balance
                    schedule = schedule_data(db, user, sale, schedules[sale.id]) if sale.id in schedules else None
                    if schedule:
                        if Decimal(schedule["balance_difference"]) != 0 or Decimal(schedule["unassigned_applications"]) != 0:
                            needs_review += 1
                            if evidence_key == "installments":
                                evidence_rows.append(evidence.sale_row(sale, balance, diferencia=str(schedule["balance_difference"]), aplicaciones_sin_asignar=str(schedule["unassigned_applications"])))
                            continue
                        due = sum((Decimal(row["balance"]) for row in schedule["items"] if row["overdue_days"] > 0), ZERO)
                    else:
                        due_at = sale.due_at or (sale.confirmed_at or sale.created_at) + timedelta(days=sale.payment_terms_days)
                        from salesia.modules.ventas.application.motor_comisiones import aware
                        due = balance if aware(due_at).astimezone(ZoneInfo(calendar["timezone"])).date() < today else ZERO
                    if evidence_key == "receivables" and due > 0:
                        evidence_rows.append(evidence.sale_row(sale, due, saldo_total=str(balance)))
                    overdue += due
                    overdue_count += int(due > 0)
                result["receivables"] = metric(overdue if not needs_review else None, "review" if needs_review else "available", "Deuda vencida actual, incluyendo cuotas conciliadas. No se limita a ventas del período.", overdue_count)
                result["receivables"]["total_open"] = amount(total)
                if needs_review:
                    alerts.append({"key": "installments", "count": needs_review, "severity": "warning", "title": f"{needs_review} cronogramas requieren conciliación", "description": "No se publica una deuda vencida consolidada mientras sus cuotas no coincidan con el saldo.", "view": "receivables"})
                if overdue_count and not needs_review:
                    alerts.append({"key": "receivables", "count": overdue_count, "severity": "danger", "title": f"{overdue_count} cuentas con importes vencidos", "description": "Priorice el seguimiento de cobros y revise sus compromisos.", "view": "receivables"})
    if "payments:read" in permissions and "credit" in enabled:
        result["receivables"]["total_open"] = amount(total_open)
        if result["receivables"]["status"] == "available" and result["receivables"]["amount"] is not None:
            result["receivables"]["current_open"] = amount(max(ZERO, total_open - Decimal(result["receivables"]["amount"])))
        result["receivables"]["note"] += " Sin cronograma ni vencimiento guardado, se usa confirmación o creación más los días de pago. Total, vigente y vencido son cartera actual; no equivalen a facturación menos cobros del período."
    result["payables"] = metric(status="restricted", note="Requiere permiso de lectura de pagos.")
    result["funds"] = metric(status="restricted", note="Requiere permiso de gestión de caja.")
    unrelated = bool(category or seller_id or zone)
    if "payments:read" in permissions:
        result["allowed_views"].append("payables")
        if "payables" not in enabled:
            result["payables"] = metric(status="inactive", note="El área de cuentas por pagar está desactivada.")
        elif unrelated:
            result["payables"] = metric(status="not_applicable", note="Las obligaciones de proveedores no se pueden atribuir a estos filtros comerciales. Quite categoría, vendedor o zona para consultarlas.")
        else:
            payable_filters = [PayableModel.company_id == user.company_id, PayableModel.currency == currency, PayableModel.status.in_(["open", "partial"]), PayableModel.amount > PayableModel.paid_amount]
            if branch_id:
                payable_filters.append(PayableModel.purchase_order_id.in_(select(SupplyDocument.id).join(WarehouseModel, WarehouseModel.id == SupplyDocument.warehouse_id).where(SupplyDocument.company_id == user.company_id, WarehouseModel.company_id == user.company_id, WarehouseModel.branch_id == branch_id)))
            installments = select(PayableInstallmentModel.payable_id).where(PayableInstallmentModel.company_id == user.company_id)
            direct = db.execute(select(func.coalesce(func.sum(PayableModel.amount - PayableModel.paid_amount), 0), func.count(PayableModel.id)).where(*payable_filters, PayableModel.due_date < today, PayableModel.id.not_in(installments))).one()
            scheduled = db.execute(select(func.coalesce(func.sum(PayableInstallmentModel.amount - PayableInstallmentModel.paid_amount), 0), func.count(func.distinct(PayableInstallmentModel.payable_id))).join(PayableModel, PayableModel.id == PayableInstallmentModel.payable_id).where(*payable_filters, PayableInstallmentModel.company_id == user.company_id, PayableInstallmentModel.due_date < today, PayableInstallmentModel.amount > PayableInstallmentModel.paid_amount)).one()
            if evidence_key == "payables":
                for payable in db.scalars(select(PayableModel).where(*payable_filters, PayableModel.due_date < today, PayableModel.id.not_in(installments)).order_by(PayableModel.id)).all():
                    evidence_rows.append({"id": str(payable.id), "documento": payable.document_number, "importe": str(payable.amount - payable.paid_amount), "moneda": payable.currency, "estado": payable.status, "vencimiento": payable.due_date.isoformat()})
                scheduled_rows = db.execute(select(PayableModel.id, PayableModel.document_number, PayableModel.currency, PayableModel.status, func.sum(PayableInstallmentModel.amount - PayableInstallmentModel.paid_amount)).join(PayableModel, PayableModel.id == PayableInstallmentModel.payable_id).where(*payable_filters, PayableInstallmentModel.company_id == user.company_id, PayableInstallmentModel.due_date < today, PayableInstallmentModel.amount > PayableInstallmentModel.paid_amount).group_by(PayableModel.id, PayableModel.document_number, PayableModel.currency, PayableModel.status)).all()
                evidence_rows.extend({"id": str(row[0]), "documento": row[1], "moneda": row[2], "estado": row[3], "importe": str(row[4])} for row in scheduled_rows)
            result["payables"] = metric(direct[0] + scheduled[0], note="Obligaciones vencidas actuales y cuotas pendientes. La sede se determina por el almacén de la compra; documentos sin origen de sede no se incluyen al filtrar una sede.", count=direct[1] + scheduled[1])
            if branch_id:
                scoped_origins = select(SupplyDocument.id).join(WarehouseModel, WarehouseModel.id == SupplyDocument.warehouse_id).where(SupplyDocument.company_id == user.company_id, WarehouseModel.company_id == user.company_id)
                unknown_origins = db.scalar(select(func.count(PayableModel.id)).where(PayableModel.company_id == user.company_id, PayableModel.currency == currency, PayableModel.status.in_(["open", "partial"]), PayableModel.amount > PayableModel.paid_amount, or_(PayableModel.purchase_order_id.is_(None), PayableModel.purchase_order_id.not_in(scoped_origins)))) or 0
                if evidence_key == "payable_origins":
                    evidence_rows = [{"id": str(row.id), "documento": row.document_number, "importe": str(row.amount - row.paid_amount), "moneda": row.currency, "estado": row.status, "compra_id": str(row.purchase_order_id) if row.purchase_order_id else "Sin origen"} for row in db.scalars(select(PayableModel).where(PayableModel.company_id == user.company_id, PayableModel.currency == currency, PayableModel.status.in_(["open", "partial"]), PayableModel.amount > PayableModel.paid_amount, or_(PayableModel.purchase_order_id.is_(None), PayableModel.purchase_order_id.not_in(scoped_origins)))).all()]
                if unknown_origins:
                    result["payables"] = metric(status="review", note=f"Hay {unknown_origins} obligaciones pendientes sin sede de origen identificada. Consulte todas las sedes o concilie su origen antes de consolidar el vencido por sede.")
                    alerts.append({"key": "payable_origins", "count": unknown_origins, "severity": "warning", "title": f"{unknown_origins} obligaciones sin sede de origen identificada", "description": "El vencido por sede queda pendiente; consulte el total de la empresa o complete su atribución.", "view": "payables"})
            if direct[1] + scheduled[1]:
                alerts.append({"key": "payables", "count": direct[1] + scheduled[1], "severity": "danger", "title": f"{direct[1] + scheduled[1]} obligaciones vencidas", "description": "Revise pagos pendientes y acuerdos con proveedores.", "view": "payables"})
    if "cash:register:manage" in permissions:
        result["allowed_views"].append("cash")
        if "cash" not in enabled:
            result["funds"] = metric(status="inactive", note="El área de caja está desactivada.")
        elif unrelated:
            result["funds"] = metric(status="not_applicable", note="Los fondos en custodia no se distribuyen por estos filtros comerciales.")
        else:
            custody = [CashCustodyAccountModel.company_id == user.company_id, CashCustodyAccountModel.currency == currency]
            if branch_id:
                custody.append(CashCustodyAccountModel.branch_id == branch_id)
            balance, accounts = db.execute(select(func.coalesce(func.sum(CashCustodyAccountModel.balance), 0), func.count(CashCustodyAccountModel.id)).where(*custody)).one()
            if evidence_key == "funds":
                evidence_rows = [{"id": str(row.id), "codigo": row.code, "cuenta": row.name, "importe": str(row.balance), "moneda": row.currency, "sede": str(row.branch_id), "estado": "Activa" if row.is_active else "Inactiva"} for row in db.scalars(select(CashCustodyAccountModel).where(*custody).order_by(CashCustodyAccountModel.id)).all()]
            result["funds"] = metric(balance if accounts else None, "available" if accounts else "empty", "Saldo actual de cuentas de custodia registradas. No representa la liquidez total ni incluye saldos de cajas abiertas, fondos de caja chica o dinero en tránsito.", accounts)
    result["inventory"] = {"status": "restricted", "out_of_stock": None, "view": "inventory"}
    if "inventory:read" in permissions:
        result["allowed_views"].append("inventory")
        if "inventory" not in enabled:
            result["inventory"] = {"status": "inactive", "out_of_stock": None, "view": "inventory"}
        else:
            stock_filters = [InventoryStockModel.company_id == user.company_id, ProductModel.company_id == user.company_id, ProductModel.is_active.is_(True), or_(ProductProfileModel.product_id.is_(None), ProductProfileModel.track_inventory.is_(True))]
            if branch_id:
                stock_filters.append(InventoryStockModel.warehouse_id.in_(select(WarehouseModel.id).where(WarehouseModel.company_id == user.company_id, WarehouseModel.branch_id == branch_id)))
            if category:
                stock_filters.append(ProductModel.category == category)
            empty = select(InventoryStockModel.product_id).join(ProductModel, ProductModel.id == InventoryStockModel.product_id).outerjoin(ProductProfileModel, (ProductProfileModel.product_id == ProductModel.id) & (ProductProfileModel.company_id == user.company_id)).where(*stock_filters).group_by(InventoryStockModel.product_id).having(func.sum(InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity) <= 0).subquery()
            missing = db.scalar(select(func.count()).select_from(empty)) or 0
            result["inventory"] = {"status": "available", "out_of_stock": missing, "view": "inventory", "note": "Productos activos con registros de stock y disponibilidad agregada cero en la sede o empresa. No incluye productos sin registro de existencias ni equivale a nivel de servicio."}
            preview = [{"id": str(row.id), "nombre": row.name, "sku": row.sku} for row in db.scalars(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id.in_(select(empty.c.product_id))).order_by(ProductModel.sku, ProductModel.id).limit(3)).all()]
            result["inventory"]["preview"] = preview
            if evidence_key == "inventory":
                evidence_rows = [{"id": str(row.id), "producto": row.name, "sku": row.sku, "estado": "Sin disponibilidad"} for row in db.scalars(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id.in_(select(empty.c.product_id))).order_by(ProductModel.sku, ProductModel.id)).all()]
            if missing:
                alerts.append({"key": "inventory", "count": missing, "severity": "warning", "title": f"{missing} productos sin disponibilidad", "description": "Revise reservas y reposición antes de comprometer nuevas entregas.", "view": "inventory"})
    if "inventory:read" in permissions and "products:cost:read" in permissions and result["inventory"]["status"] == "available":
        from salesia.modules.analitica.application.cobertura_costo_inventario import cost_coverage
        coverage = cost_coverage(db, user, branch_id, category)
        result["inventory"]["cost_coverage"] = {key: value for key, value in coverage.items() if key != "items"}
        if coverage["missing_count"]:
            alerts.append({"key": "inventory_cost", "count": coverage["missing_count"], "severity": "warning", "title": f'{coverage["missing_count"]} productos con existencias sin costo promedio', "description": "La valuación registrada no cubre todos los productos con existencias. Revise el costo promedio de sus almacenes.", "view": "inventory"})
        if evidence_key == "inventory_cost":
            evidence_rows = coverage["items"]
    if "team" in result["allowed_views"]:
        unassigned_count = db.scalar(select(func.count(SaleModel.id)).where(*filters, SaleModel.sales_rep_id.is_(None))) or 0
        if unassigned_count:
            alerts.append({"key": "unassigned", "count": unassigned_count, "severity": "warning", "title": f"{unassigned_count} " + ("venta sin vendedor asignado" if unassigned_count == 1 else "ventas sin vendedor asignado"), "description": "Solo operaciones sin referencia de vendedor; las de vendedores inactivos conservan su atribución.", "view": "sales"})
    available = lambda name: result[name]["status"] not in ("restricted", "inactive", "not_applicable", "unavailable")
    result["drilldowns"] = {"revenue": "sales:read" in permissions, "margin": "sales:read" in permissions and "products:cost:read" in permissions and available("margin"), "costs": "sales:read" in permissions and "products:cost:read" in permissions and available("margin"), "unassigned": "sales:read" in permissions, "collections": available("collections"), "receivables": available("receivables") and result["receivables"]["status"] != "review", "installments": available("receivables"), "payables": available("payables"), "payable_origins": available("payables") and bool(branch_id), "funds": available("funds"), "inventory": result["inventory"]["status"] == "available"}
    result["drilldowns"]["inventory_cost"] = "inventory:read" in permissions and "products:cost:read" in permissions and result["inventory"]["status"] == "available"
    if evidence_key:
        from fastapi import HTTPException
        if not result["drilldowns"].get(evidence_key):
            raise HTTPException(403, "El respaldo solicitado no está disponible para los permisos, filtros o estado del indicador.")
        evidence_scope = result["scope_note"]
        if evidence_key == "payable_origins":
            evidence_scope += " Este respaldo muestra obligaciones pendientes de la empresa sin sede identificable: no se atribuyen artificialmente a la sede seleccionada. Son los documentos que impiden consolidar ese indicador por sede."
        if evidence_key == "inventory":
            evidence_scope += " La disponibilidad agrupa todos los almacenes de la sede; se cuentan productos, no filas de almacén. La moneda comercial no filtra cantidades de existencias."
        result["evidence"] = {"items": evidence_rows, "total_count": len(evidence_rows), "as_of": now.isoformat(), "timezone": calendar["timezone"], "scope_note": evidence_scope, "key": evidence_key}
    result["alerts"] = sorted(alerts, key=lambda row: (row["severity"] != "danger", row["key"]))
    return result
