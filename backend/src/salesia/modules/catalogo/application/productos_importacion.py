import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_importacion import ImportBatchRequest
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainConflictException
from salesia.shared.infrastructure.models import AuditLogModel, ProductModel


def import_products(req: ImportBatchRequest, current_user: AuthenticatedUser, db: Session):
    errors = []

    seen_skus = set()

    for idx, item in enumerate(req.items, 1):
        if item.sku in seen_skus:
            errors.append({"row": idx, "field": "sku", "error": f"SKU duplicado en el archivo: '{item.sku}'"})

        seen_skus.add(item.sku)

        existing = db.execute(
            select(ProductModel.id).where(
                ProductModel.company_id == current_user.company_id, ProductModel.sku == item.sku
            )
        ).scalar_one_or_none()

        if existing:
            errors.append({"row": idx, "field": "sku", "error": f"SKU ya registrado en el catálogo: '{item.sku}'"})

        if item.unit_price < 0:
            errors.append({"row": idx, "field": "unit_price", "error": "El precio unitario no puede ser negativo."})

        if item.unit_cost < 0:
            errors.append({"row": idx, "field": "unit_cost", "error": "El costo unitario no puede ser negativo."})

    if errors:
        raise DomainConflictException(
            f"El lote de importación contiene {len(errors)} errores de validación. Ningún producto fue guardado."
        )

    created_products = []

    for item in req.items:
        prod = ProductModel(
            id=uuid4(),
            company_id=current_user.company_id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            unit_of_measure=item.unit_of_measure,
            unit_price=item.unit_price,
            unit_cost=item.unit_cost,
            tax_rate=item.tax_rate,
            is_active=True,
        )

        db.add(prod)

        db.flush()

        track_inv = item.track_inventory if item.product_type == "product" else False
        from salesia.modules.organizacion.application.perfil_operativo import require_product_inventory
        require_product_inventory(db, current_user.company_id, track_inv)

        prof = ProductProfileModel(
            id=uuid4(),
            company_id=current_user.company_id,
            product_id=prod.id,
            product_type=item.product_type,
            status="active",
            track_inventory=track_inv,
            barcode=item.barcode,
            warranty_period_months=item.warranty_period_months,
        )

        db.add(prof)

        created_products.append(prod)

    audit = AuditLogModel(
        id=uuid4(),
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CATALOG_IMPORT",
        entity_type="Product",
        entity_id=created_products[0].id if created_products else current_user.user_id,
        trace_id=uuid4().hex,
        payload_diff=json.dumps({"total_imported": len(created_products)}),
    )

    db.add(audit)

    db.commit()

    return {
        "success": True,
        "total_imported": len(created_products),
        "imported_skus": [p.sku for p in created_products],
    }
