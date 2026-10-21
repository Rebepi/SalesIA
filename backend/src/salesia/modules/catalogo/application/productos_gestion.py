from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_gestion import (
    ProductCreateModel,
    ProductDuplicateModel,
    ProductUpdateModel,
)
from salesia.modules.catalogo.infrastructure_models import (
    CategoryModel,
    ProductAttachmentModel,
    ProductBarcodeModel,
    ProductPriceHistoryModel,
    ProductProfileModel,
    UnitOfMeasureModel,
)
from salesia.modules.catalogo.service import get_or_create_product_profile
from salesia.modules.inventario.infrastructure_models import StockRule, Supplier
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import (
    DomainConflictException,
    DomainForbiddenException,
    DomainNotFoundException,
)
from salesia.shared.infrastructure.models import AuditLogModel, InventoryStockModel, ProductModel, WarehouseModel


def create_product(req: ProductCreateModel, current_user: AuthenticatedUser, db: Session):
    category_row = None

    if req.category_id:
        category_row = db.scalar(
            select(CategoryModel).where(
                CategoryModel.id == req.category_id,
                CategoryModel.company_id == current_user.company_id,
                CategoryModel.is_active.is_(True),
            )
        )

        if not category_row:
            raise HTTPException(422, "Seleccione una categoría activa de su empresa.")

    if not category_row and not req.category:
        raise HTTPException(422, "Seleccione una categoría.")

    unit_code = req.unit_of_measure.upper()

    unit_row = db.scalar(
        select(UnitOfMeasureModel).where(
            UnitOfMeasureModel.company_id == current_user.company_id,
            UnitOfMeasureModel.code == unit_code,
            UnitOfMeasureModel.is_active.is_(True),
        )
    )

    canonical_units = {"NIU": ("Unidad", False, 0), "KGM": ("Kilogramo", True, 3)}

    if not unit_row and unit_code in canonical_units:
        unit_name, allow_fractions, precision_digits = canonical_units[unit_code]

        unit_row = UnitOfMeasureModel(
            id=uuid4(),
            company_id=current_user.company_id,
            code=unit_code,
            name=unit_name,
            allow_fractions=allow_fractions,
            precision_digits=precision_digits,
            is_active=True,
        )

        db.add(unit_row)

        db.flush()

    if not unit_row:
        raise HTTPException(422, "Seleccione una unidad de medida activa de su empresa.")

    if req.supplier_id:
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.id == req.supplier_id,
                Supplier.company_id == current_user.company_id,
                Supplier.is_active.is_(True),
            )
        )

        if not supplier:
            raise HTTPException(422, "Seleccione un proveedor activo de su empresa.")

    warehouse = None

    if req.initial_stock_quantity > 0 or req.reorder_point > 0 or req.reorder_quantity > 0:
        if not req.warehouse_id:
            raise HTTPException(422, "Seleccione un almacén para las existencias y la reposición.")

        warehouse = db.scalar(
            select(WarehouseModel).where(
                WarehouseModel.id == req.warehouse_id,
                WarehouseModel.company_id == current_user.company_id,
                WarehouseModel.is_active.is_(True),
            )
        )

        if not warehouse:
            raise HTTPException(422, "Seleccione un almacén activo de su empresa.")

    if req.barcode:
        barcode_exists = db.scalar(
            select(ProductBarcodeModel.id).where(
                ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.barcode == req.barcode
            )
        )

        if barcode_exists:
            raise DomainConflictException(f"Ya existe un producto con el código de barras '{req.barcode}'.")

    existing = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.sku == req.sku)
    ).scalar_one_or_none()

    if existing:
        raise DomainConflictException(f"Ya existe un producto con el SKU '{req.sku}' en esta empresa.")

    product = ProductModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sku=req.sku,
        name=req.name,
        category=category_row.name if category_row else req.category,
        unit_of_measure=unit_code,
        unit_price=req.unit_price,
        unit_cost=req.unit_cost,
        tax_rate=req.tax_rate,
        is_active=True,
    )

    db.add(product)

    db.flush()

    track_inv = req.track_inventory if req.product_type == "product" else False

    profile = ProductProfileModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=product.id,
        description=req.description,
        product_type=req.product_type,
        status="active",
        track_inventory=track_inv,
        barcode=req.barcode,
        warranty_period_months=req.warranty_period_months,
        warranty_policy=req.warranty_policy,
        price_includes_tax=req.price_includes_tax,
        is_kit=req.is_kit,
        category_id=category_row.id if category_row else None,
        supplier_id=req.supplier_id,
        brand=req.brand,
        image_url=req.image_url,
        length_cm=req.length_cm,
        width_cm=req.width_cm,
        height_cm=req.height_cm,
        weight_kg=req.weight_kg,
        tracking_mode=req.tracking_mode,
    )

    db.add(profile)

    if req.barcode:
        bc = ProductBarcodeModel(
            id=uuid4(),
            company_id=current_user.company_id,
            product_id=product.id,
            barcode=req.barcode,
            barcode_type="EAN13",
            is_active=True,
        )

        db.add(bc)

    if req.image_url:
        db.add(
            ProductAttachmentModel(
                id=uuid4(),
                company_id=current_user.company_id,
                product_id=product.id,
                file_name=f"{product.sku}-principal",
                file_url=req.image_url,
                content_type="image/external",
                file_size_bytes=1,
                is_primary=True,
                is_private=False,
            )
        )

    if warehouse:
        db.add(
            InventoryStockModel(
                id=uuid4(),
                company_id=current_user.company_id,
                warehouse_id=warehouse.id,
                product_id=product.id,
                average_cost=req.unit_cost,
                physical_quantity=req.initial_stock_quantity,
                reserved_quantity=Decimal("0"),
            )
        )

        if req.reorder_point > 0 or req.reorder_quantity > 0:
            db.add(
                StockRule(
                    id=uuid4(),
                    company_id=current_user.company_id,
                    warehouse_id=warehouse.id,
                    product_id=product.id,
                    min_quantity=req.reorder_point,
                    max_quantity=req.reorder_point + req.reorder_quantity,
                    reorder_point=req.reorder_point,
                    reorder_quantity=req.reorder_quantity,
                )
            )

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="PRODUCT_CREATED",
        entity_type="Product",
        entity_id=product.id,
        trace_id=str(uuid4()),
        payload_diff=f'{{"sku": "{product.sku}", "name": "{product.name}", "price": "{product.unit_price}", "type": "{req.product_type}"}}',
    )

    db.add(audit)

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory, profile.is_kit, product.is_active)
    db.commit()

    db.refresh(product)

    res = {
        "id": str(product.id),
        "product_id": str(product.id),
        "company_id": str(product.company_id),
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "unit_of_measure": product.unit_of_measure,
        "unit_price": str(product.unit_price),
        "tax_rate": str(product.tax_rate),
        "is_active": product.is_active,
        "product_type": profile.product_type,
        "status": profile.status,
        "track_inventory": profile.track_inventory,
        "warranty_period_months": profile.warranty_period_months,
        "is_kit": profile.is_kit,
        "category_id": str(profile.category_id) if profile.category_id else None,
        "supplier_id": str(profile.supplier_id) if profile.supplier_id else None,
        "brand": profile.brand,
        "image_url": profile.image_url,
        "length_cm": str(profile.length_cm) if profile.length_cm is not None else None,
        "width_cm": str(profile.width_cm) if profile.width_cm is not None else None,
        "height_cm": str(profile.height_cm) if profile.height_cm is not None else None,
        "weight_kg": str(profile.weight_kg) if profile.weight_kg is not None else None,
        "tracking_mode": profile.tracking_mode,
        "category_id": str(profile.category_id) if profile.category_id else None,
        "supplier_id": str(profile.supplier_id) if profile.supplier_id else None,
        "brand": profile.brand,
        "image_url": profile.image_url,
        "tracking_mode": profile.tracking_mode,
        "initial_stock_quantity": str(req.initial_stock_quantity),
        "created_at": product.created_at.isoformat(),
    }

    if "products:cost:read" in current_user.permissions:
        res["unit_cost"] = str(product.unit_cost)

    return res


def update_product(product_id: UUID, req: ProductUpdateModel, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        other = db.scalar(select(ProductModel.id).where(ProductModel.id == product_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise DomainNotFoundException("Producto no encontrado.")

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    old_price = product.unit_price

    if req.name is not None:
        product.name = req.name

    if req.category is not None:
        product.category = req.category

    if req.category_id is not None or "category_id" in req.model_fields_set:
        category_row = (
            db.scalar(
                select(CategoryModel).where(
                    CategoryModel.id == req.category_id,
                    CategoryModel.company_id == current_user.company_id,
                    CategoryModel.is_active.is_(True),
                )
            )
            if req.category_id
            else None
        )

        if req.category_id and not category_row:
            raise HTTPException(422, "Seleccione una categoría activa de su empresa.")

        profile.category_id = category_row.id if category_row else None

        if category_row:
            product.category = category_row.name

    if req.unit_of_measure is not None:
        unit_code = req.unit_of_measure.upper()

        if not db.scalar(
            select(UnitOfMeasureModel.id).where(
                UnitOfMeasureModel.company_id == current_user.company_id,
                UnitOfMeasureModel.code == unit_code,
                UnitOfMeasureModel.is_active.is_(True),
            )
        ):
            raise HTTPException(422, "Seleccione una unidad de medida activa de su empresa.")

        product.unit_of_measure = unit_code

    if req.tax_rate is not None:
        product.tax_rate = req.tax_rate

    if req.unit_cost is not None:
        product.unit_cost = req.unit_cost

    if req.is_active is not None:
        product.is_active = req.is_active

        if not req.is_active and profile.status == "active":
            profile.status = "archived"

        elif req.is_active and profile.status == "archived":
            profile.status = "active"

    if req.unit_price is not None and req.unit_price != old_price:
        product.unit_price = req.unit_price

        hist = ProductPriceHistoryModel(
            id=uuid4(),
            company_id=current_user.company_id,
            product_id=product.id,
            old_price=old_price,
            new_price=req.unit_price,
            effective_date=datetime.now(timezone.utc),
            changed_by=current_user.email,
        )

        db.add(hist)

    if req.description is not None:
        profile.description = req.description

    if req.product_type is not None:
        profile.product_type = req.product_type

        if req.product_type == "service":
            profile.track_inventory = False

    if req.track_inventory is not None:
        profile.track_inventory = req.track_inventory

    if req.status is not None:
        profile.status = req.status

        product.is_active = req.status == "active"

    if req.barcode is not None:
        duplicate_barcode = db.scalar(
            select(ProductBarcodeModel.id).where(
                ProductBarcodeModel.company_id == current_user.company_id,
                ProductBarcodeModel.barcode == req.barcode,
                ProductBarcodeModel.product_id != product.id,
            )
        )

        if duplicate_barcode:
            raise DomainConflictException(f"Ya existe un producto con el código de barras '{req.barcode}'.")

        profile.barcode = req.barcode

    if req.warranty_period_months is not None:
        profile.warranty_period_months = req.warranty_period_months

    if req.warranty_policy is not None:
        profile.warranty_policy = req.warranty_policy

    if req.price_includes_tax is not None:
        profile.price_includes_tax = req.price_includes_tax

    if req.is_kit is not None:
        profile.is_kit = req.is_kit

    if req.supplier_id is not None or "supplier_id" in req.model_fields_set:
        if req.supplier_id and not db.scalar(
            select(Supplier.id).where(
                Supplier.id == req.supplier_id,
                Supplier.company_id == current_user.company_id,
                Supplier.is_active.is_(True),
            )
        ):
            raise HTTPException(422, "Seleccione un proveedor activo de su empresa.")

        profile.supplier_id = req.supplier_id

    for field_name in ("brand", "image_url", "length_cm", "width_cm", "height_cm", "weight_kg", "tracking_mode"):
        value = getattr(req, field_name)

        if value is not None:
            setattr(profile, field_name, value)

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory, profile.is_kit, product.is_active)
    db.commit()

    db.refresh(product)

    res = {
        "id": str(product.id),
        "product_id": str(product.id),
        "company_id": str(product.company_id),
        "sku": product.sku,
        "name": product.name,
        "unit_price": str(product.unit_price),
        "is_active": product.is_active,
        "status": profile.status,
        "updated_at": product.updated_at.isoformat(),
    }

    if "products:cost:read" in current_user.permissions:
        res["unit_cost"] = str(product.unit_cost)

    return res


def archive_product(product_id: UUID, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    product.is_active = False

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    profile.status = "archived"

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory, profile.is_kit, product.is_active)
    db.commit()

    return {
        "id": str(product.id),
        "product_id": str(product.id),
        "is_active": False,
        "status": "archived",
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }


def restore_product(product_id: UUID, current_user: AuthenticatedUser, db: Session):
    product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not product:
        raise DomainNotFoundException("Producto no encontrado.")

    product.is_active = True

    profile = get_or_create_product_profile(db, current_user.company_id, product.id)

    profile.status = "active"

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, profile.track_inventory, profile.is_kit, product.is_active)
    db.commit()

    return {
        "id": str(product.id),
        "product_id": str(product.id),
        "is_active": True,
        "status": "active",
        "restored_at": datetime.now(timezone.utc).isoformat(),
    }


def duplicate_product(product_id: UUID, req: ProductDuplicateModel, current_user: AuthenticatedUser, db: Session):
    source = db.scalar(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.company_id == current_user.company_id)
    )

    if not source:
        raise DomainNotFoundException("Producto no encontrado.")

    if db.scalar(
        select(ProductModel.id).where(ProductModel.company_id == current_user.company_id, ProductModel.sku == req.sku)
    ):
        raise DomainConflictException(f"Ya existe un producto con el SKU '{req.sku}'.")

    if req.barcode and db.scalar(
        select(ProductBarcodeModel.id).where(
            ProductBarcodeModel.company_id == current_user.company_id, ProductBarcodeModel.barcode == req.barcode
        )
    ):
        raise DomainConflictException(f"Ya existe un producto con el código de barras '{req.barcode}'.")

    source_profile = get_or_create_product_profile(db, current_user.company_id, source.id)

    duplicate = ProductModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sku=req.sku,
        name=req.name or f"{source.name} copia",
        category=source.category,
        unit_of_measure=source.unit_of_measure,
        unit_price=source.unit_price,
        unit_cost=source.unit_cost,
        tax_rate=source.tax_rate,
        is_active=True,
    )

    db.add(duplicate)

    db.flush()

    duplicate_profile = ProductProfileModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=duplicate.id,
        description=source_profile.description,
        product_type=source_profile.product_type,
        status="active",
        track_inventory=source_profile.track_inventory,
        category_id=source_profile.category_id,
        barcode=req.barcode,
        warranty_period_months=source_profile.warranty_period_months,
        warranty_policy=source_profile.warranty_policy,
        is_kit=source_profile.is_kit,
        price_includes_tax=source_profile.price_includes_tax,
        supplier_id=source_profile.supplier_id,
        brand=source_profile.brand,
        image_url=source_profile.image_url,
        length_cm=source_profile.length_cm,
        width_cm=source_profile.width_cm,
        height_cm=source_profile.height_cm,
        weight_kg=source_profile.weight_kg,
        tracking_mode=source_profile.tracking_mode,
    )

    db.add(duplicate_profile)

    if req.barcode:
        db.add(
            ProductBarcodeModel(
                id=uuid4(),
                company_id=current_user.company_id,
                product_id=duplicate.id,
                barcode=req.barcode,
                barcode_type="EAN13",
                is_active=True,
            )
        )

    from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
    require_product_inventory(db, current_user.company_id, source_profile.track_inventory, source_profile.is_kit)
    db.commit()

    return {
        "id": str(duplicate.id),
        "product_id": str(duplicate.id),
        "sku": duplicate.sku,
        "name": duplicate.name,
        "status": "active",
    }
