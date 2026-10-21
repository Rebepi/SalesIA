from fastapi import HTTPException
from sqlalchemy import String, cast, func, or_, select
import unicodedata

from salesia.modules.catalogo.infrastructure_models import ProductModel, ProductWarrantyClaimModel
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.modules.finanzas.infrastructure.models import CreditNoteModel, PaymentModel, ReturnModel
from salesia.modules.finanzas.infrastructure.models.obligaciones import ExpenseModel, PayableModel
from salesia.modules.inventario.infrastructure_models import DeliveryShipment, InventoryLot, InventorySerial, Supplier, SupplyDocument
from salesia.modules.operaciones.infrastructure_models import CollaborationTask, SalesRepresentative
from salesia.modules.organizacion.infrastructure.models import BranchModel, WarehouseModel
from salesia.modules.pedidos.infrastructure.models import OrderModel, QuotationModel
from salesia.modules.ventas.infrastructure.models import SaleModel


from salesia.modules.inventario.infrastructure.models.ventanas_entrega import DeliveryWindowModel
from salesia.modules.inventario.infrastructure.models.recorridos import DeliveryRouteModel, DeliveryVehicleModel
from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel

RESOURCES = {
    "delivery_window": (DeliveryWindowModel, "Ventanas de entrega y retiro", "inventory:read", "inventory:write", ("mode", "starts_at", "ends_at", "requirements")),
    "delivery_route": (DeliveryRouteModel, "Recorridos de reparto", "inventory:read", "inventory:write", ("code", "zone", "status")),
    "delivery_vehicle": (DeliveryVehicleModel, "Vehículos de reparto", "inventory:read", "inventory:write", ("code", "name")),
    "supplier_claim": (SupplierClaimModel, "Reclamos de proveedor", "purchases:read", "purchases:write", ("code", "description", "status")),
    "warranty": (ProductWarrantyClaimModel, "Garantías", "sales:read", "sales:write", ("issue_description", "serial_number", "status")),
    "customer": (CustomerModel, "Clientes", "customers:read", "customers:write", ("code", "legal_name", "doc_number")),
    "product": (ProductModel, "Productos", "products:read", "products:write", ("sku", "name")),
    "quotation": (QuotationModel, "Cotizaciones", "quotations:read", "quotations:write", ("quotation_number",)),
    "order": (OrderModel, "Pedidos", "sales:read", "sales:write", ("order_number", "customer_po_number")),
    "sale": (SaleModel, "Ventas", "sales:read", "sales:write", ("series", "number")),
    "supplier": (Supplier, "Proveedores", "purchases:read", "purchases:write", ("tax_id", "legal_name")),
    "purchase_order": (SupplyDocument, "Órdenes de compra", "purchases:read", "purchases:write", ("id", "status")),
    "delivery": (DeliveryShipment, "Entregas", "inventory:read", "inventory:write", ("recipient_name", "tracking_number", "delivery_address")),
    "return": (ReturnModel, "Devoluciones", "payments:read", "payments:write", ("id", "reason")),
    "credit_note": (CreditNoteModel, "Notas de crédito", "payments:read", "payments:write", ("series", "number")),
    "payment": (PaymentModel, "Cobros", "payments:read", "payments:write", ("reference_code", "payment_method")),
    "payable": (PayableModel, "Cuentas por pagar", "payments:read", "payments:write", ("document_number", "notes")),
    "expense": (ExpenseModel, "Gastos", "payments:read", "payments:write", ("title", "category", "document_number")),
    "lot": (InventoryLot, "Lotes", "inventory:read", "inventory:write", ("lot_code",)),
    "serial": (InventorySerial, "Series", "inventory:read", "inventory:write", ("serial_number",)),
    "branch": (BranchModel, "Sedes", "organization:manage", "organization:manage", ("code", "name")),
    "warehouse": (WarehouseModel, "Almacenes", "inventory:read", "organization:manage", ("code", "name")),
    "task": (CollaborationTask, "Tareas", "", "", ("title", "description")),
}

RELATIONS = {
    "supplier_claim_id": "supplier_claim",
    "order_id": "order",
    "customer_id": "customer", "product_id": "product", "supplier_id": "supplier", "sale_id": "sale", "quotation_id": "quotation", "return_id": "return", "payment_id": "payment", "purchase_order_id": "purchase_order", "branch_id": "branch", "warehouse_id": "warehouse", "lot_id": "lot", "converted_order_id": "order", "exchange_sale_id": "sale", "credit_note_id": "credit_note",
}


def definition(kind, user, write=False):
    resource = RESOURCES.get(kind)
    if resource is None:
        raise HTTPException(422, "Tipo de recurso desconocido.")
    permission = resource[3 if write else 2]
    if permission and permission not in user.permissions:
        raise HTTPException(403, f"Falta el permiso {permission}.")
    return resource


def entity_statement(kind, user, write=False):
    model = definition(kind, user, write)[0]
    statement = select(model).where(model.company_id == user.company_id)
    if kind == "purchase_order":
        statement = statement.where(model.kind == "PURCHASE_ORDER")
    if kind == "sale" and user.role == "salesperson":
        statement = statement.where(model.sales_rep_id.in_(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == user.user_id, SalesRepresentative.is_active.is_(True))))
    if kind == "task" and "operations:manage" not in user.permissions:
        statement = statement.where((model.creator_id == user.user_id) | (model.assignee_id == user.user_id))
    return statement


def entity(db, user, kind, identifier, write=False, lock=False):
    model = definition(kind, user, write)[0]
    statement = entity_statement(kind, user, write).where(model.id == identifier)
    row = db.scalar(statement.with_for_update() if lock else statement)
    if row is None:
        raise HTTPException(404, "El recurso no existe o no está disponible en tu alcance de acceso.")
    return row


def summary(kind, row):
    fields = RESOURCES[kind][4]
    title = " · ".join(str(getattr(row, key)) for key in fields if getattr(row, key, None) is not None)
    if kind == "sale":
        title = f"Venta {row.series}-{row.number:08d}"
    if kind == "credit_note":
        title = f"Nota {row.series}-{row.number:08d}"
    amount = next((getattr(row, key) for key in ("total_amount", "amount") if hasattr(row, key)), None)
    return {"type": kind, "id": str(row.id), "title": title or str(row.id), "status": getattr(row, "status", "active" if getattr(row, "is_active", True) else "inactive"), "version": getattr(row, "version", None), "currency": getattr(row, "currency", None), "amount": str(amount) if amount is not None else None, "created_at": row.created_at.isoformat() if getattr(row, "created_at", None) else None}


def normalized(value):
    return "".join(character for character in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(character))


def search_statement(kind, user, query):
    model, _, _, _, fields = definition(kind, user)
    statement = entity_statement(kind, user)
    if not query.strip():
        return statement
    columns = [cast(getattr(model, field), String) for field in fields]
    if kind in ("sale", "credit_note"):
        columns.append(model.series + "-" + cast(model.number, String))
    expressions = []
    for column in columns:
        expression = func.lower(column)
        for source, target in zip("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN"):
            expression = func.replace(expression, source, target.lower())
        expressions.append(expression)
    for token in normalized(query).split():
        escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(or_(*(expression.like(f"%{escaped}%", escape="\\") for expression in expressions)))
    return statement
