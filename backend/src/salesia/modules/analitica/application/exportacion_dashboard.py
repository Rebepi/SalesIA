import csv
import io
import re
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select

from salesia.modules.analitica.application.analitica_clientes import get_customer_analytics
from salesia.modules.analitica.application.analitica_productos import get_product_analytics
from salesia.modules.analitica.application.analitica_sellers import get_seller_analytics
from salesia.modules.analitica.application.analitica_ventas import get_sales_analytics
from salesia.modules.analitica.application.dashboard import get_dashboard_summary
from salesia.modules.analitica.application.resumen_ejecutivo import sale_scope
from salesia.modules.catalogo.infrastructure.models.productos import ProductProfileModel
from salesia.modules.catalogo.infrastructure.models.clasificacion import UnitOfMeasureModel
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.shared.infrastructure.models import BranchModel, CustomerModel, InventoryStockModel, ProductModel, SaleLineModel, SaleModel, UserModel, WarehouseModel


LIMA = ZoneInfo("America/Lima")
LABELS = {"available": "Disponible", "review": "Por revisar", "restricted": "Restringido", "empty": "Sin registros", "unavailable": "No disponible", "inactive": "Área desactivada", "not_applicable": "No aplicable", "confirmed": "Confirmada", "paid": "Pagada", "new": "Nuevo", "recurring": "Recurrente", "final_consumer": "Consumidor final", "active": "Activo", "unassigned": "Sin asignar", "unidentifiable": "Vendedor no identificable", "recorded": "Con ventas", "zero_sales": "Sin ventas", "out_of_stock": "Sin disponibilidad", "warning": "Advertencia", "danger": "Atención prioritaria"}
DEFAULT_PRECISION = {"NIU": 0, "BX": 0, "KGM": 3, "LTR": 2, "MTR": 2}


def decimal(value):
    return Decimal(str(value))


class CsvNumber(str):
    pass


def number(value, digits=2):
    if value is None:
        return ""
    return CsvNumber(format(decimal(value).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_EVEN), f".{digits}f"))


def local_iso(value):
    if not value:
        return ""
    moment = datetime.fromisoformat(value) if isinstance(value, str) else value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(LIMA).isoformat(timespec="microseconds")


def safe_cell(value):
    if isinstance(value, (int, float, Decimal, CsvNumber)):
        return str(value)
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").replace("\x00", "")
    return "'" + text if re.match(r"^[\s\ufeff]*[=+\-@]", text) else text


def csv_bytes(headers, rows):
    target = io.StringIO(newline="")
    writer = csv.writer(target, lineterminator="\r\n", quoting=csv.QUOTE_ALL)
    writer.writerow([safe_cell(value) for value in headers])
    writer.writerows([safe_cell(value) for value in row] for row in rows)
    return target.getvalue().encode("utf-8-sig")


def build_export(db, user, period, branch_id, currency, category, as_of, granularity="day", visible_panels=None, expected_revenue=None, expected_documents=None):
    query = dict(period=period, branch_id=branch_id, currency=currency, seller_id=None, category=category, zone=None, current_user=user, db=db, as_of=as_of)
    summary = get_dashboard_summary(**query)
    executive = summary["executive"]
    currency = summary["currency"]
    cutoff = datetime.fromisoformat(executive["as_of"])
    start = datetime.fromisoformat(summary["measurement_context"]["from"]) if summary["measurement_context"]["from"] else None
    if expected_revenue is not None and decimal(expected_revenue) != decimal(summary["total_revenue"]) or expected_documents is not None and expected_documents != summary["orders_count"]:
        raise HTTPException(409, "Los datos cambiaron desde la consulta del dashboard. Actualice el tablero antes de exportar.")
    visible = set(("summary,trend,products,customers,sellers,inventory" if visible_panels is None else visible_panels).split(",")) - {""}
    permissions = executive["export_permissions"]
    filters = [*sale_scope(user, currency, branch_id, category), SaleModel.status.in_(["confirmed", "paid"]), (SaleModel.confirmed_at <= cutoff) | SaleModel.confirmed_at.is_(None)]
    if start:
        filters.append(SaleModel.confirmed_at >= start)
    sales = db.scalars(select(SaleModel).where(*filters).order_by(SaleModel.confirmed_at, SaleModel.id)).all()
    sale_ids = [sale.id for sale in sales]
    branch_names = {str(row.id): row.name for row in db.scalars(select(BranchModel).where(BranchModel.company_id == user.company_id)).all()}
    sale_by_id = {str(sale.id): sale for sale in sales}
    products = get_product_analytics(period, category, branch_id, currency, None, "revenue", user, db, as_of=cutoff)
    customers = get_customer_analytics(period, branch_id, category, None, currency, None, user, db, as_of=cutoff)
    sellers = get_seller_analytics(period, branch_id, currency, category, user, db, as_of=cutoff) if permissions["sales"] else None
    trend = get_sales_analytics(period, granularity, branch_id, currency, category, user, db, as_of=cutoff)
    units = {unit.code: unit.precision_digits if unit.allow_fractions else 0 for unit in db.scalars(select(UnitOfMeasureModel).where(UnitOfMeasureModel.company_id == user.company_id)).all()}
    catalog = {str(product.id): product for product in db.scalars(select(ProductModel).where(ProductModel.company_id == user.company_id)).all()}
    profiles = {str(row.product_id): row for row in db.scalars(select(ProductProfileModel).where(ProductProfileModel.company_id == user.company_id)).all()}
    representatives = {str(rep.id): rep.full_name for rep in db.scalars(select(SalesRepresentative).where(SalesRepresentative.company_id == user.company_id)).all()} if permissions["sales"] else {}
    legacy_users = {str(person.id): person.full_name or "Vendedor sin nombre registrado" for person in db.scalars(select(UserModel).where(UserModel.company_id == user.company_id)).all()} if permissions["sales"] else {}
    customers_by_id = {str(row.id): row for row in db.scalars(select(CustomerModel).where(CustomerModel.company_id == user.company_id, CustomerModel.id.in_([sale.customer_id for sale in sales]))).all()}
    lines_by_id = {str(row.id): row for row in db.scalars(select(SaleLineModel).where(SaleLineModel.company_id == user.company_id, SaleLineModel.sale_id.in_(sale_ids))).all()} if permissions["costs"] and permissions["sales"] else {}
    quantity = lambda value, unit: number(value, units.get(unit, DEFAULT_PRECISION.get(unit, max(0, min(6, -decimal(value).normalize().as_tuple().exponent)))))
    seller_name = lambda seller_id: representatives.get(str(seller_id), legacy_users.get(str(seller_id), "Vendedor no identificable")) if seller_id else "Sin vendedor asignado"
    tables = {}
    indicator_headers = ["Indicador_id", "Indicador", "Valor", "Unidad", "Moneda", "Tipo", "Estado_codigo", "Estado", "Visible_en_pantalla", "Valor_en_pantalla", "Diferencia_con_pantalla", "Observacion"]
    indicators = []

    def indicator(key, label, value, unit="importe", kind="durante el período", state="available", panel="summary", note="", screen=None):
        formatted = CsvNumber(str(value)) if unit == "documentos" or unit == "clientes" else number(value)
        original = formatted if screen is None else CsvNumber(str(screen)) if unit in ("documentos", "clientes") else number(screen)
        delta = "" if value is None or original == "" else number(decimal(formatted) - decimal(original))
        indicators.append([key, label, formatted, unit, currency if unit == "importe" else "", kind, state, LABELS.get(state, state), "Sí" if panel in visible else "No", original, delta, note])

    indicator("revenue", "Facturación confirmada (con IGV)", summary["total_revenue"])
    indicator("documents", "Documentos confirmados", summary["orders_count"], "documentos")
    indicator("buyers", "Clientes con compras", summary["active_purchasing_customers"], "clientes")
    indicator("average_ticket", "Ticket promedio", summary["average_ticket"], state="available" if summary["average_ticket"] is not None else "empty")
    indicator("median_ticket", "Ticket mediano", summary["median_ticket"], state="available" if summary["median_ticket"] is not None else "empty")
    for key, label, allowed, kind in [("margin", "Margen comercial con costo histórico", permissions["costs"], "durante el período"), ("collections", "Cobros recibidos brutos", permissions["payments"], "durante el período"), ("receivables", "Por cobrar vencido", permissions["payments"], "saldo actual"), ("payables", "Por pagar vencido", permissions["payments"], "saldo actual"), ("funds", "Fondos en custodia", permissions["cash"], "saldo actual")]:
        if allowed:
            metric = executive[key]
            indicator(key, label, metric["amount"], kind=kind, state=metric["status"], note=metric["note"])
    if permissions["costs"] and executive["margin"].get("percent") is not None:
        indicator("margin_pct", "Margen comercial con costo histórico", executive["margin"]["percent"], "%", state=executive["margin"]["status"])
    if permissions["costs"] and executive["margin"].get("partial"):
        partial = executive["margin"]["partial"]
        indicator("margin_partial_pct", "Margen parcial con costo histórico positivo", partial["percent"], "%", state="review", note=partial["definition"])
        indicator("margin_partial_coverage", "Cobertura del margen parcial sobre facturación", partial["coverage_pct"], "%", state="review")
    if permissions["payments"] and "total_open" in executive["receivables"]:
        indicator("receivables_total", "Por cobrar total", executive["receivables"]["total_open"], kind="saldo actual", state=executive["receivables"]["status"])
        indicator("receivables_current", "Por cobrar vigente", executive["receivables"].get("current_open"), kind="saldo actual", state="available" if "current_open" in executive["receivables"] else "review")
    coverage = products["coverage"]
    indicator("product_coverage", "Cobertura del detalle sobre facturación", coverage["percent"], "%", panel="products", state="available" if coverage["percent"] is not None else "empty", note=coverage["definition"])
    indicator("documents_without_detail", "Documentos sin detalle de productos", coverage["documents_without_detail"], "documentos", panel="products")
    indicator("amount_without_detail", "Facturación de documentos sin detalle (con IGV)", coverage["amount_without_detail"], panel="products")
    tables["indicadores.csv"] = (indicator_headers, indicators)

    document_headers = ["Documento_id", "Fecha_confirmacion", "Fecha_creacion", "Documento", "Cliente", "Cliente_codigo", "Vendedor", "Vendedor_id", "Facturado (con IGV)", "Moneda", "Estado_codigo", "Estado", "Sede_id", "Tipo", "Sede"]
    documents = []
    if permissions["sales"]:
        for sale in sales:
            customer = customers_by_id.get(str(sale.customer_id))
            documents.append([str(sale.id), local_iso(sale.confirmed_at), local_iso(sale.created_at), f"{sale.series}-{sale.number}", customer.legal_name if customer else "", customer.code if customer else "", seller_name(sale.sales_rep_id), str(sale.sales_rep_id) if sale.sales_rep_id else "", number(sale.total_amount), sale.currency, sale.status, LABELS.get(sale.status, sale.status), str(sale.branch_id), "durante el período", branch_names.get(str(sale.branch_id), "")])
    tables["documentos.csv"] = (document_headers, documents)
    document_by_id = {row[0]: row for row in documents}

    product_headers = ["Producto_id", "SKU", "Producto", "Categoria", "Unidad", "Cantidad", "Precio unitario vigente (sin IGV)", "Facturado (con IGV)", "Participacion % (del detalle de productos)", "Moneda"]
    if permissions["costs"]:
        product_headers += ["Costo historico total", "Costo unitario vigente del catalogo", "Margen % (costo historico)", "Estado_codigo", "Estado", "Observacion"]
    if not permissions["costs"]:
        product_headers += ["Estado_codigo", "Estado"]
    product_rows = []
    for item in products["items"]:
        product = catalog[item["product_id"]]
        row = [item["product_id"], item["sku"], item["name"], item["category"], product.unit_of_measure, quantity(item["units"], product.unit_of_measure), number(decimal(item["unit_price"]) / (1 + product.tax_rate) if profiles.get(item["product_id"]) and profiles[item["product_id"]].price_includes_tax else item["unit_price"]), number(item["revenue"]), number(item["share_pct"]), currency]
        if permissions["costs"]:
            state = "review" if item["has_zero_cost"] or decimal(item["margin_pct"]) == 100 else "unavailable" if currency != executive["inventory_currency"] else "available"
            row += [number(item["historical_cost"]), number(item["unit_cost"]), number(item["margin_pct"]) if state == "available" else "", state, LABELS[state], "Líneas con costo cero o margen redondeado a 100%; no se publica rentabilidad." if state == "review" else "Sin equivalencia histórica entre moneda de venta y costos." if state == "unavailable" else "Base sin IGV menos costo histórico de las líneas."]
        else:
            row += ["available", "Disponible"]
        product_rows.append(row)
    tables["productos.csv"] = (product_headers, product_rows)

    customer_headers = ["Cliente_id", "Codigo", "Cliente", "Documentos", "Facturado (con IGV)", "Participacion % (de la facturacion)", "Clasificacion_codigo", "Clasificacion", "Estado_codigo", "Estado", "Ultima_compra", "Moneda"]
    customer_rows = []
    excluded_new = 0
    for item in customers["items"]:
        final_consumer = item["code"].upper() == "CONSUMIDOR_FINAL" or item["legal_name"].strip().upper() == "CONSUMIDOR FINAL"
        classification = "final_consumer" if final_consumer else item["customer_type"]
        excluded_new += int(final_consumer and item["customer_type"] == "new")
        customer_rows.append([item["customer_id"], item["code"], item["legal_name"], item["orders_count"], number(item["total_revenue"]), number(item["revenue_share_pct"]), classification, LABELS[classification], "not_applicable" if final_consumer else "available", "No aplicable" if final_consumer else "Disponible", local_iso(item["last_order_date"]), currency])
    tables["clientes.csv"] = (customer_headers, customer_rows)
    customer_summary = customers["summary"]
    indicator("new_customers", "Clientes nuevos identificados", customer_summary["new_customers_count"], "clientes", panel="customers", state="available", note="Consumidor final se muestra aparte y no cuenta como nuevo ni recurrente.")
    indicator("final_consumers", "Consumidor final", customer_summary["final_consumers_count"], "clientes", panel="customers", note="No cuenta como cliente nuevo ni recurrente.")
    indicator("recurring_customers", "Clientes recurrentes", customer_summary["recurring_customers_count"], "clientes", panel="customers")
    indicator("customer_concentration", "Concentración de ventas en el 20% de compradores", customer_summary["top_20_concentration_pct"], "%", panel="customers")

    seller_headers = ["Vendedor_id", "Vendedor", "Documentos", "Facturado (con IGV)", "Tiene_ventas_en_periodo", "Estado_codigo", "Estado", "Moneda"]
    seller_rows = []
    if sellers:
        for item in sellers["items"]:
            if item["sales_count"]:
                state = "active" if item["is_active"] else "inactive"
                seller_rows.append([item["seller_id"], seller_name(item["seller_id"]), item["sales_count"], number(item["total_revenue"]), "Sí", state, "Activo" if state == "active" else "Inactivo", currency])
        for key in ["unassigned", "unidentifiable"]:
            item = sellers[key]
            if item["sales_count"]:
                seller_rows.append(["", LABELS[key], item["sales_count"], number(item["total_revenue"]), "Sí", key, LABELS[key], currency])
    tables["vendedores.csv"] = (seller_headers, seller_rows)
    tables["tendencia.csv"] = (["Fecha_periodo", "Agrupacion", "Facturado (con IGV)", "Documentos", "Moneda", "Tipo", "Estado_codigo", "Estado", "Zona_agrupacion"], [[item["date"] + "-01" if granularity == "month" else item["date"], {"day": "Día", "week": "Semana", "month": "Mes"}[granularity], number(item["revenue"]), item["orders_count"], currency, "durante el período", item["status"], LABELS.get(item["status"], item["status"]), trend.get("measurement_context", summary["measurement_context"])["timezone"]] for item in trend["series"]])

    inventory_headers = ["Producto_id", "SKU", "Producto", "Unidad", "Stock_fisico", "Stock_reservado", "Stock_disponible", "Estado_codigo", "Estado", "Moneda_costos", "Tipo", "Incluido_en_alerta_sin_disponibilidad"]
    if permissions["costs"]:
        inventory_headers += ["Valuacion (costo promedio ponderado)"]
    cost_coverage = executive["inventory"].get("cost_coverage")
    missing_cost_ids = set()
    if cost_coverage:
        from salesia.modules.analitica.application.cobertura_costo_inventario import cost_coverage as inventory_cost_coverage
        missing_cost_ids = {row["id"] for row in inventory_cost_coverage(db, user, branch_id, category)["items"]}
    inventory_rows = []
    inventory_by_id = {}
    if permissions["inventory"] and executive["inventory"]["status"] == "available":
        stock_filters = [InventoryStockModel.company_id == user.company_id, ProductModel.company_id == user.company_id]
        if branch_id:
            stock_filters.append(InventoryStockModel.warehouse_id.in_(select(WarehouseModel.id).where(WarehouseModel.company_id == user.company_id, WarehouseModel.branch_id == branch_id)))
        if category:
            stock_filters.append(ProductModel.category == category)
        stock = db.execute(select(ProductModel.id, func.sum(InventoryStockModel.physical_quantity), func.sum(InventoryStockModel.reserved_quantity), func.sum(InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity), func.sum(InventoryStockModel.physical_quantity * InventoryStockModel.average_cost)).join(ProductModel, ProductModel.id == InventoryStockModel.product_id).where(*stock_filters).group_by(ProductModel.id).order_by(ProductModel.id)).all()
        for product_id, physical, reserved, available, valuation in stock:
            product = catalog[str(product_id)]
            state = "review" if str(product_id) in missing_cost_ids else "out_of_stock" if available <= 0 else "available"
            row = [str(product_id), product.sku, product.name, product.unit_of_measure, quantity(physical, product.unit_of_measure), quantity(reserved, product.unit_of_measure), quantity(available, product.unit_of_measure), state, "Por revisar" if state == "review" else "Sin disponibilidad" if available <= 0 else "Disponible", executive["inventory_currency"] if permissions["costs"] else "", "saldo actual", "Sí" if available <= 0 and product.is_active and (not profiles.get(str(product_id)) or profiles[str(product_id)].track_inventory) else "No"]
            if permissions["costs"]:
                row.append(number(valuation))
            inventory_rows.append(row)
            inventory_by_id[str(product_id)] = row
        if permissions["costs"]:
            indicator("inventory_valuation", "Valor actual de existencias al costo promedio ponderado", summary["inventory_summary"]["valuation_total"], kind="saldo actual", state=cost_coverage["status"] if cost_coverage else "available", panel="inventory", note=f"Valorado en {cost_coverage['valued_products']} de {cost_coverage['products_with_stock']} productos con stock. Moneda base de costos." if cost_coverage else "Moneda base de costos.")
            indicators[-1][4] = executive["inventory_currency"]
        indicator("inventory_unavailable", "Productos sin disponibilidad", executive["inventory"]["out_of_stock"], "documentos", kind="saldo actual", panel="inventory")
        indicators[-1][3] = "productos"
    tables["inventario.csv"] = (inventory_headers, inventory_rows)

    alert_headers = ["Alerta_id", "Alerta", "Cantidad", "Severidad_codigo", "Severidad", "Moneda", "Tipo", "Observacion"]
    tables["alertas.csv"] = (alert_headers, [[item["key"], item["title"], item.get("count", ""), item["severity"], LABELS[item["severity"]], currency if item["key"] != "inventory" else "", "durante el período" if item["key"] in ("costs", "unassigned") else "saldo actual", item["description"]] for item in executive["alerts"]])
    costs_headers = ["Linea_id", "Documento_id", "Documento", "Fecha_confirmacion", "Producto", "SKU", "Unidad", "Cantidad", "Costo unitario historico", "Facturado (con IGV)", "Moneda", "Estado_codigo", "Estado"] if permissions["costs"] and permissions["sales"] else ["Linea_id", "Estado_codigo", "Estado"]
    costs_rows, unavailable_rows, unassigned_rows, financial_rows, missing_cost_rows = [], [], [], [], []
    for alert in executive["alerts"]:
        key = alert["key"]
        if not executive["drilldowns"].get(key):
            continue
        backing = get_dashboard_summary(**query, evidence_key=key)
        if backing["total_count"] != alert.get("count", backing["total_count"]):
            raise HTTPException(409, "Las alertas cambiaron durante la exportación. Actualice el dashboard.")
        for item in backing["items"]:
            if key == "costs":
                line = lines_by_id[item["id"]]
                sale = sale_by_id[item["venta_id"]]
                costs_rows.append([item["id"], str(sale.id), item["documento"], local_iso(sale.confirmed_at), item["producto"], item["sku"], line.unit_of_measure_snapshot, quantity(line.quantity, line.unit_of_measure_snapshot), number(item["costo_unitario"]), number(item["importe"]), currency, "review", "Por revisar"])
            elif key == "inventory_cost":
                missing_cost_rows.append(inventory_by_id[item["id"]])
            elif key == "inventory":
                unavailable_rows.append(inventory_by_id[item["id"]])
            elif key == "unassigned":
                unassigned_rows.append(document_by_id[item["id"]])
            else:
                financial_rows.append([key, item["id"], item.get("documento", ""), number(item.get("importe")), item.get("moneda", currency), "review" if key in ("installments", "payable_origins") else "available", "Por revisar" if key in ("installments", "payable_origins") else "Disponible", "saldo actual"])
    tables["alertas_lineas_costo_cero.csv"] = (costs_headers, costs_rows)
    tables["alertas_productos_sin_disponibilidad.csv"] = (inventory_headers, unavailable_rows)
    tables["alertas_existencias_sin_costo_promedio.csv"] = (inventory_headers, missing_cost_rows)
    tables["alertas_ventas_sin_vendedor.csv"] = (document_headers, unassigned_rows)
    tables["alertas_documentos_financieros.csv"] = (["Alerta_id", "Documento_id", "Documento", "Importe", "Moneda", "Estado_codigo", "Estado", "Tipo"], financial_rows)

    checks = {
        "documentos": "Sin permiso de ventas" if not permissions["sales"] else "Coincide" if sum((decimal(row[8]) for row in documents), Decimal(0)) == decimal(number(summary["total_revenue"])) and len(documents) == summary["orders_count"] else "Revisar diferencias de redondeo o cambios de datos",
        "productos": "Coincide" if sum((decimal(row[7]) for row in product_rows), Decimal(0)) == decimal(number(products["total_revenue"])) else "Revisar diferencias de redondeo",
        "clientes": "Coincide" if sum((decimal(row[4]) for row in customer_rows), Decimal(0)) == decimal(number(summary["total_revenue"])) else "Revisar diferencias de redondeo",
        "vendedores": "Sin permiso de ventas" if not permissions["sales"] else "Coincide" if sum((decimal(row[3]) for row in seller_rows), Decimal(0)) == decimal(number(summary["total_revenue"])) else "Revisar diferencias de atribución o redondeo",
        "tendencia": "Coincide" if sum((decimal(row[2]) for row in tables["tendencia.csv"][1]), Decimal(0)) == decimal(number(summary["total_revenue"])) else "Revisar fechas sin confirmación o redondeo",
        "inventario": "Sin permiso de inventario o costos" if not permissions["inventory"] or not permissions["costs"] else "Coincide" if sum((decimal(row[-1]) for row in inventory_rows), Decimal(0)) == decimal(number(summary["inventory_summary"]["valuation_total"])) else "Revisar redondeo o estado del área",
    }
    branch = db.scalar(select(BranchModel).where(BranchModel.company_id == user.company_id, BranchModel.id == branch_id)) if branch_id else None
    if branch_id and branch is None:
        raise HTTPException(422, "La sede no pertenece a la empresa.")
    exclusions = []
    for permission, message in [("costs", "Costos, márgenes y detalle de alertas de costo cero"), ("payments", "Cobros, deudas y documentos financieros"), ("cash", "Fondos en custodia"), ("inventory", "Existencias, valuación y alertas de inventario"), ("sales", "Documentos, vendedores y detalle de alertas de ventas")]:
        if not permissions[permission]:
            exclusions.append(message)
    panels = {"summary": "Indicadores", "trend": "Tendencia", "products": "Productos", "customers": "Clientes", "sellers": "Equipo comercial", "inventory": "Inventario"}
    branch_label = f"{branch.name} ({branch.code})" if branch else "Todas las sedes (comparativo)"
    context_headers = ["Periodo_desde", "Periodo_hasta", "Periodo", "Corte", "Generado", "Zona_fechas", "Sede_id", "Sede", "Moneda_ventas", "Moneda_costos", "Categoria", "Agrupacion_tendencia", "Zona_agrupacion_tendencia", "Paneles_visibles", "Excluido_por_permisos", *[f"Conciliacion_{key}" for key in checks], "Notas"]
    tables["contexto.csv"] = (context_headers, [[local_iso(start), local_iso(cutoff), f"{local_iso(start) or 'Inicio del historial'} a {local_iso(cutoff)}", local_iso(cutoff), local_iso(datetime.now(timezone.utc)), "America/Lima", str(branch_id) if branch_id else "", branch_label, currency, executive["inventory_currency"] if permissions["costs"] else "", category or "Todas las categorías", {"day": "Día", "week": "Semana", "month": "Mes"}[granularity], trend.get("measurement_context", summary["measurement_context"])["timezone"], ", ".join(panels[key] for key in panels if key in visible), "; ".join(exclusions) or "Ninguno", *checks.values(), "Listas completas. Alcances y formatos en LEEME.txt."]])
    current_sede = branch_label
    for name, (headers, rows) in tables.items():
        if not name.startswith("alertas") or name == "alertas_ventas_sin_vendedor.csv":
            continue
        headers = list(headers)
        rows = [list(row) for row in rows]
        tables[name] = (headers, rows)
        headers.append("Sede")
        for row in rows:
            if name == "alertas_lineas_costo_cero.csv":
                sede = branch_names.get(str(sale_by_id[row[1]].branch_id), "")
            elif name == "alertas_documentos_financieros.csv" and row[0] == "payable_origins":
                sede = "Sin sede identificada"
            else:
                sede = current_sede
            row.append(sede)
    readme = """INICIO EJECUTIVO: EXPORTACIÓN DE DATOS
Cada CSV contiene una sola tabla, sin filas Otros ni resúmenes dentro del detalle.
Las listas de productos, clientes y vendedores son completas; la pantalla muestra rankings.
Los paneles ocultos se identifican en contexto. No se incluyen emails, metas, cumplimiento ni facturación menos reembolsos.
La participación de productos usa el detalle de líneas; la de clientes usa la facturación de documentos.
Consumidor final se muestra aparte y no cuenta como cliente nuevo ni recurrente.
El margen usa costos históricos; queda vacío y Por revisar si hay líneas con costo cero.
El precio unitario proviene del catálogo vigente y se presenta sin IGV.
Los saldos y existencias son actuales y pueden cambiar después del corte comercial.
Valor de existencias conserva la suma registrada; Por revisar indica productos con stock sin costo promedio en uno o más almacenes.
La cobertura cuenta productos con stock físico agregado positivo y costo positivo en todos sus registros con existencias.
La valuación y sus alertas se omiten sin permiso de costos; custodia se omite sin permiso de caja.
Las cantidades se presentan por producto y unidad sin total empresarial de unidades diferentes.
Los importes tienen dos decimales. Las cantidades siguen la precisión configurada de su unidad.
Las conciliaciones de contexto comparan importes exportados y servicios de pantalla; el redondeo por fila puede producir diferencias informadas.
Las fechas completas usan America/Lima (-05:00); la tendencia conserva su zona de agrupación efectiva.
Solo los textos con prefijos =, +, - o @ se neutralizan con apóstrofo. Los campos numéricos, incluidos negativos, siguen siendo números.
Una sede sin filtro se rotula Todas las sedes (comparativo). Las obligaciones sin sede no se atribuyen artificialmente a una sede.
"""
    def slug(value):
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "sede"
    period_slug = f"{start.astimezone(LIMA).date().isoformat()}-a-{cutoff.astimezone(LIMA).date().isoformat()}" if start else f"historial-hasta-{cutoff.astimezone(LIMA).date().isoformat()}"
    filename = f"inicio-ejecutivo_{slug(branch_label)}_{period_slug}_{datetime.now(LIMA).date().isoformat()}.zip"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("LEEME.txt", readme.encode("utf-8-sig"))
        for name, (headers, rows) in tables.items():
            archive.writestr(name, csv_bytes(headers, rows))
    return output.getvalue(), {"summary": summary, "checks": checks, "tables": tables, "excluded_new_consumers": excluded_new, "filename": filename}
