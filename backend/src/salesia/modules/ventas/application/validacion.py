import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from salesia.modules.catalogo.infrastructure_models import ProductKitItemModel, ProductProfileModel
from salesia.modules.clientes.infrastructure.models import CustomerModel, CustomerProfileModel
from salesia.modules.inventario.infrastructure_models import InventorySerial
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def credit_block_active(profile, at=None):
    if profile is None:
        return False
    current = at or datetime.now(timezone.utc)
    until = aware(profile.credit_block_until)
    return (profile.is_credit_blocked and (until is None or until > current)) or (until is not None and until > current)


def sale_validation(db, sale, user, allow_exception=False):
    errors, warnings = [], []
    if sale.status != "draft":
        warnings.append(f"La venta se encuentra en estado {sale.status}.")
    if not sale.lines:
        errors.append("La venta requiere al menos una línea.")
    customer = db.scalar(select(CustomerModel).where(CustomerModel.id == sale.customer_id, CustomerModel.company_id == sale.company_id))
    profile = db.scalar(select(CustomerProfileModel).where(CustomerProfileModel.customer_id == sale.customer_id, CustomerProfileModel.company_id == sale.company_id))
    if customer is None or not customer.is_active:
        errors.append("El cliente no existe o está inactivo.")
    if profile and profile.status == "blocked":
        (warnings if allow_exception else errors).append("El cliente tiene un bloqueo comercial que requiere excepción autorizada.")
    if sale.is_credit:
        if credit_block_active(profile):
            (warnings if allow_exception else errors).append("El cliente está bloqueado para compras a crédito.")
        if customer and customer.current_balance + sale.total_amount > customer.credit_limit:
            errors.append("El importe excede el crédito disponible del cliente.")
    quantities = defaultdict(lambda: Decimal("0"))
    seen_serials = set()
    for line in sale.lines:
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == sale.company_id, ProductModel.id == line.product_id))
        if product is None or not product.is_active:
            errors.append(f"El producto {line.sku_snapshot} está inactivo o no existe.")
            continue
        product_profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == sale.company_id, ProductProfileModel.product_id == line.product_id))
        if product_profile and product_profile.status in ("archived", "suspended", "discontinued"):
            errors.append(f"El producto {line.sku_snapshot} no admite ventas en su estado actual.")
        if product_profile and (product_profile.product_type == "service" or not product_profile.track_inventory):
            continue
        if sale.order_id:
            continue
        if product_profile and product_profile.is_kit:
            components = db.scalars(select(ProductKitItemModel).where(ProductKitItemModel.company_id == sale.company_id, ProductKitItemModel.kit_product_id == line.product_id)).all()
            if not components:
                errors.append(f"El kit {line.sku_snapshot} no tiene componentes.")
            for item in components:
                quantities[item.component_product_id] += item.quantity * line.quantity
        else:
            quantities[line.product_id] += line.quantity
        selected = json.loads(line.serial_numbers_json or "[]")
        serial_query = select(InventorySerial).where(InventorySerial.company_id == sale.company_id, InventorySerial.product_id == line.product_id, InventorySerial.warehouse_id == sale.warehouse_id, InventorySerial.status == "IN_STOCK")
        serials = db.scalars(serial_query).all()
        serial_required = bool(product_profile and product_profile.tracking_mode == "SERIAL")
        if serial_required or selected or serials:
            available = {item.serial_number for item in serials}
            if line.quantity != line.quantity.to_integral_value() or len(selected) != int(line.quantity) or len(set(selected)) != len(selected):
                errors.append(f"Selecciona una serie distinta por cada unidad de {line.sku_snapshot}.")
            if set(selected) - available:
                errors.append(f"Hay series de {line.sku_snapshot} que no están disponibles en el almacén.")
            keys = {(line.product_id, number) for number in selected}
            if keys & seen_serials:
                errors.append(f"Se repite una serie de {line.sku_snapshot} en varias líneas.")
            seen_serials |= keys
    for product_id, quantity in quantities.items():
        stock = db.scalar(select(InventoryStockModel).where(InventoryStockModel.company_id == sale.company_id, InventoryStockModel.warehouse_id == sale.warehouse_id, InventoryStockModel.product_id == product_id))
        available = stock.physical_quantity - stock.reserved_quantity if stock else Decimal("0")
        if available < quantity:
            product = db.get(ProductModel, product_id)
            errors.append(f"Stock insuficiente para {product.sku if product else product_id}: solicitado {quantity}, disponible {available}.")
    return {"sale_id": str(sale.id), "valid": not errors, "errors": errors, "warnings": warnings, "summary": {"status": sale.status, "lines_count": len(sale.lines), "total_amount": str(sale.total_amount), "is_credit": sale.is_credit, "payment_terms_days": sale.payment_terms_days, "due_at": (datetime.now(timezone.utc) + timedelta(days=sale.payment_terms_days)).isoformat() if sale.is_credit else None}}
