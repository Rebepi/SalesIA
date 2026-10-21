from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select

from salesia.modules.inventario.application.gestion_stock.consulta import warehouse
from salesia.modules.inventario.application.gestion_stock.movimientos import move_stock
from salesia.modules.inventario.infrastructure_models import PhysicalCountLine, PhysicalCountSession, WarehouseLocation
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel, ProductModel


def create_physical_count_session(
    db, user, warehouse_id, count_code, scope="FULL", scope_filter=None, is_blind=True, items=None, notes=None
):
    warehouse(db, user.company_id, warehouse_id)
    now = datetime.now(timezone.utc)
    session = PhysicalCountSession(
        id=uuid4(),
        company_id=user.company_id,
        warehouse_id=warehouse_id,
        count_code=count_code,
        scope=scope,
        scope_filter=scope_filter,
        cutoff_date=now,
        is_blind=is_blind,
        status="in_progress",
        version=1,
        created_by=user.user_id,
        notes=notes,
    )
    db.add(session)
    db.flush()
    prod_query = select(ProductModel).where(
        ProductModel.company_id == user.company_id, ProductModel.is_active.is_(True)
    )
    if scope == "LOCATION":
        location = db.scalar(
            select(WarehouseLocation).where(
                WarehouseLocation.id == UUID(scope_filter or "00000000-0000-0000-0000-000000000000"),
                WarehouseLocation.company_id == user.company_id,
                WarehouseLocation.warehouse_id == warehouse_id,
                WarehouseLocation.is_active.is_(True),
            )
        )
        if not location:
            raise HTTPException(422, "Selecciona una ubicación activa del almacén.")
        raise HTTPException(
            422,
            "El conteo por ubicación requiere conciliación de saldos por ubicación. Selecciona productos para contar el almacén.",
        )
    if scope == "CATEGORY":
        prod_query = prod_query.where(ProductModel.category == scope_filter)
    if items:
        prod_query = prod_query.where(ProductModel.id.in_(items))
    products_in_scope = db.scalars(prod_query).all()
    for prod in products_in_scope:
        curr_stock = db.scalar(
            select(InventoryStockModel.physical_quantity).where(
                InventoryStockModel.company_id == user.company_id,
                InventoryStockModel.warehouse_id == warehouse_id,
                InventoryStockModel.product_id == prod.id,
            )
        ) or Decimal("0")
        line = PhysicalCountLine(
            id=uuid4(),
            company_id=user.company_id,
            session_id=session.id,
            product_id=prod.id,
            system_quantity_snapshot=curr_stock,
            counted_quantity=Decimal("0"),
            difference_quantity=-curr_stock,
            unit_cost=prod.unit_cost,
        )
        db.add(line)
    db.flush()
    return session


def approve_physical_count_session(db, user, count_id):
    session = db.scalar(
        select(PhysicalCountSession)
        .where(PhysicalCountSession.id == count_id, PhysicalCountSession.company_id == user.company_id)
        .with_for_update()
    )
    if not session:
        raise HTTPException(404, "Sesión de conteo no encontrada.")
    if session.created_by == user.user_id:
        raise HTTPException(403, "El creador no puede aprobar el conteo.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, user, "stock_count", [session.created_by], "PhysicalCountSession", session.id)
    if session.status == "approved":
        return session
    if session.status not in ("in_progress", "pending_approval"):
        raise HTTPException(409, "El estado de la sesión no permite aprobación.")
    if not session.lines or any(line.counted_at is None for line in session.lines):
        raise HTTPException(
            409,
            "Registra explícitamente el conteo de todos los productos, incluso las cantidades cero, antes de aprobar.",
        )
    for line in session.lines:
        cutoff = session.cutoff_date
        concurrent_delta = db.scalar(
            select(func.coalesce(func.sum(KardexMovementModel.quantity_delta), Decimal("0"))).where(
                KardexMovementModel.company_id == user.company_id,
                KardexMovementModel.warehouse_id == session.warehouse_id,
                KardexMovementModel.product_id == line.product_id,
                KardexMovementModel.occurred_at > cutoff,
            )
        ) or Decimal("0")
        expected_now = line.counted_quantity + concurrent_delta
        current_stock = db.scalar(
            select(InventoryStockModel.physical_quantity).where(
                InventoryStockModel.company_id == user.company_id,
                InventoryStockModel.warehouse_id == session.warehouse_id,
                InventoryStockModel.product_id == line.product_id,
            )
        ) or Decimal("0")
        adjustment_needed = expected_now - current_stock
        if adjustment_needed != 0:
            move_stock(
                db,
                user.company_id,
                session.warehouse_id,
                line.product_id,
                adjustment_needed,
                line.unit_cost,
                session.id,
                "CONTEO_FISICO",
            )
        line.difference_quantity = line.counted_quantity - line.system_quantity_snapshot
    session.status = "approved"
    session.approved_by = user.user_id
    session.approved_at = datetime.now(timezone.utc)
    session.version += 1
    db.flush()
    return session
