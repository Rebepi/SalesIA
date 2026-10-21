import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_bulk_update import BulkUpdateRequest
from salesia.modules.catalogo.infrastructure_models import ProductPriceHistoryModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel, ProductModel


def bulk_update_products(req: BulkUpdateRequest, current_user: AuthenticatedUser, db: Session):
    query = select(ProductModel).where(ProductModel.company_id == current_user.company_id)

    if "category" in req.filters:
        query = query.where(ProductModel.category == req.filters["category"])

    if "product_ids" in req.filters:
        ids = [UUID(pid) for pid in req.filters["product_ids"]]

        query = query.where(ProductModel.id.in_(ids))

    products = db.execute(query).scalars().all()

    preview_diffs = []

    batch_id = uuid4().hex[:12]

    for p in products:
        old_price = p.unit_price

        new_price = old_price

        if req.operation.type == "PERCENTAGE_PRICE_ADJUSTMENT":
            factor = Decimal("1") + (Decimal(req.operation.value) / Decimal("100"))

            new_price = (old_price * factor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        elif req.operation.type == "FIXED_PRICE_ADJUSTMENT":
            new_price = max(Decimal("0"), old_price + Decimal(req.operation.value))

        preview_diffs.append(
            {
                "product_id": str(p.id),
                "sku": p.sku,
                "name": p.name,
                "old_price": str(old_price),
                "new_price": str(new_price),
            }
        )

        if not req.preview:
            p.unit_price = new_price

            hist = ProductPriceHistoryModel(
                id=uuid4(),
                company_id=current_user.company_id,
                product_id=p.id,
                old_price=old_price,
                new_price=new_price,
                effective_date=datetime.now(timezone.utc),
                changed_by=current_user.email,
                batch_id=batch_id,
            )

            db.add(hist)

    if not req.preview:
        audit = AuditLogModel(
            id=uuid4(),
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="BATCH_PRICE_UPDATE",
            entity_type="Product",
            entity_id=products[0].id if products else current_user.user_id,
            trace_id=batch_id,
            payload_diff=json.dumps({"count": len(products), "operation": req.operation.model_dump()}),
        )

        db.add(audit)

        db.commit()

    return {
        "is_preview": req.preview,
        "batch_id": batch_id if not req.preview else None,
        "total_affected": len(preview_diffs),
        "items": preview_diffs,
    }
