import json
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.auxiliares.category_descendant_ids import category_descendant_ids
from salesia.modules.catalogo.application.contracts.categorias import (
    CategoryCreateModel,
    CategoryRestoreRequest,
    CategoryUpdateModel,
)
from salesia.modules.catalogo.infrastructure_models import CategoryModel, ProductProfileModel
from salesia.modules.catalogo.service import validate_no_category_cycle
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import (
    DomainConflictException,
    DomainForbiddenException,
    DomainNotFoundException,
)
from salesia.shared.infrastructure.models import AuditLogModel, CompanyModel, ProductModel


def list_categories(current_user: AuthenticatedUser, db: Session):
    categories = (
        db.execute(
            select(CategoryModel)
            .where(CategoryModel.company_id == current_user.company_id, CategoryModel.is_active.is_(True))
            .order_by(CategoryModel.level.asc(), CategoryModel.sort_order.asc(), CategoryModel.name.asc())
        )
        .scalars()
        .all()
    )

    if not categories:
        product_cats = (
            db.execute(
                select(ProductModel.category).where(ProductModel.company_id == current_user.company_id).distinct()
            )
            .scalars()
            .all()
        )

        created = []

        for idx, cat_name in enumerate(product_cats):
            cat = CategoryModel(
                id=uuid4(),
                company_id=current_user.company_id,
                code=f"CAT-{idx + 1:03d}",
                name=cat_name,
                parent_id=None,
                level=1,
                sort_order=idx,
                is_active=True,
            )

            db.add(cat)

            created.append(cat)

        if created:
            db.commit()

            categories = created

    return [
        {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "level": c.level,
            "sort_order": c.sort_order,
            "is_active": c.is_active,
        }
        for c in categories
    ]


def create_category(req: CategoryCreateModel, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())

    category_id = uuid4()

    category_code = req.code.strip().upper() if req.code else f"CAT-{category_id.hex[:8].upper()}"

    dup = db.execute(
        select(CategoryModel).where(
            CategoryModel.company_id == current_user.company_id, CategoryModel.code == category_code
        )
    ).scalar_one_or_none()

    if dup:
        raise DomainConflictException(f"Ya existe una categoría con el código '{category_code}'.")

    level = validate_no_category_cycle(db, current_user.company_id, category_id, req.parent_id)

    cat = CategoryModel(
        id=category_id,
        company_id=current_user.company_id,
        code=category_code,
        name=req.name,
        parent_id=req.parent_id,
        level=level,
        sort_order=req.sort_order,
        is_active=True,
    )

    db.add(cat)

    db.commit()

    return {
        "id": str(cat.id),
        "code": cat.code,
        "name": cat.name,
        "parent_id": str(cat.parent_id) if cat.parent_id else None,
        "level": cat.level,
        "sort_order": cat.sort_order,
    }


def update_category(category_id: UUID, req: CategoryUpdateModel, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())

    cat = db.execute(
        select(CategoryModel).where(
            CategoryModel.company_id == current_user.company_id, CategoryModel.id == category_id
        )
    ).scalar_one_or_none()

    if not cat:
        other = db.scalar(select(CategoryModel.id).where(CategoryModel.id == category_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise DomainNotFoundException("Categoría no encontrada.")

    before = {
        "name": cat.name,
        "parent_id": str(cat.parent_id) if cat.parent_id else None,
        "level": cat.level,
        "sort_order": cat.sort_order,
    }

    if req.code is not None:
        code = req.code.strip().upper()

        duplicate = db.scalar(
            select(CategoryModel.id).where(
                CategoryModel.company_id == current_user.company_id,
                CategoryModel.code == code,
                CategoryModel.id != cat.id,
            )
        )

        if duplicate:
            raise DomainConflictException("El código de categoría ya está registrado.")

        cat.code = code

    if req.name is not None:
        name = req.name.strip()

        if len(name) < 2:
            raise HTTPException(422, "Escribe un nombre de categoría válido.")

        db.execute(
            update(ProductModel)
            .where(
                ProductModel.company_id == current_user.company_id,
                ProductModel.id.in_(
                    select(ProductProfileModel.product_id).where(
                        ProductProfileModel.company_id == current_user.company_id,
                        ProductProfileModel.category_id == cat.id,
                    )
                ),
            )
            .values(category=name)
        )

        cat.name = name

    if req.sort_order is not None:
        cat.sort_order = req.sort_order

    if req.is_active is not None:
        cat.is_active = req.is_active

    affected = category_descendant_ids(db, current_user.company_id, cat.id)

    if req.parent_id is not None or "parent_id" in req.model_fields_set:
        level = validate_no_category_cycle(db, current_user.company_id, cat.id, req.parent_id)

        if req.parent_id:
            parent = db.get(CategoryModel, req.parent_id)

            if not parent.is_active:
                raise DomainConflictException("Restaura la categoría padre antes de mover productos a ella.")

        delta = level - cat.level

        descendants = db.scalars(
            select(CategoryModel).where(
                CategoryModel.company_id == current_user.company_id, CategoryModel.id.in_(affected - {cat.id})
            )
        ).all()

        if any(child.level + delta > 5 for child in descendants):
            raise DomainConflictException("El movimiento supera cinco niveles al incluir las subcategorías.")

        for child in descendants:
            child.level += delta

        cat.parent_id = req.parent_id

        cat.level = level

    db.add(
        AuditLogModel(
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="UPDATE_CATEGORY",
            entity_type="Category",
            entity_id=cat.id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps(
                {
                    "before": before,
                    "after": {
                        "name": cat.name,
                        "parent_id": str(cat.parent_id) if cat.parent_id else None,
                        "level": cat.level,
                        "sort_order": cat.sort_order,
                    },
                    "affected_categories": len(affected),
                }
            ),
        )
    )

    db.commit()

    return {
        "id": str(cat.id),
        "code": cat.code,
        "name": cat.name,
        "parent_id": str(cat.parent_id) if cat.parent_id else None,
        "level": cat.level,
        "sort_order": cat.sort_order,
        "is_active": cat.is_active,
    }


def category_impact(category_id: UUID, current_user: AuthenticatedUser, db: Session):
    category = db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.company_id == current_user.company_id
        )
    )

    if not category:
        raise DomainNotFoundException("Categoría no encontrada.")

    category_ids = category_descendant_ids(db, current_user.company_id, category.id)

    names = db.scalars(select(CategoryModel.name).where(CategoryModel.id.in_(category_ids))).all()

    product_count = (
        db.scalar(
            select(func.count(ProductModel.id))
            .join(ProductProfileModel, ProductProfileModel.product_id == ProductModel.id, isouter=True)
            .where(
                ProductModel.company_id == current_user.company_id,
                or_(ProductProfileModel.category_id.in_(category_ids), ProductModel.category.in_(names)),
            )
        )
        or 0
    )

    return {"category_id": str(category.id), "category_count": len(category_ids), "product_count": product_count}


def archive_category(category_id: UUID, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())

    category = db.scalar(
        select(CategoryModel).where(
            CategoryModel.id == category_id, CategoryModel.company_id == current_user.company_id
        )
    )

    if not category:
        raise DomainNotFoundException("Categoría no encontrada.")

    category_ids = category_descendant_ids(db, current_user.company_id, category.id)

    active_ids = db.scalars(
        select(CategoryModel.id).where(
            CategoryModel.id.in_(category_ids),
            CategoryModel.company_id == current_user.company_id,
            CategoryModel.is_active.is_(True),
        )
    ).all()

    db.execute(
        update(CategoryModel)
        .where(CategoryModel.company_id == current_user.company_id, CategoryModel.id.in_(category_ids))
        .values(is_active=False)
    )

    db.add(
        AuditLogModel(
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="ARCHIVE_CATEGORY",
            entity_type="Category",
            entity_id=category.id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"archived_ids": [str(item) for item in active_ids]}),
        )
    )

    db.commit()

    return {
        "category_id": str(category.id),
        "archived_categories": len(active_ids),
        "archived_ids": [str(item) for item in active_ids],
        "is_active": False,
    }


def restore_category(category_id: UUID, payload: CategoryRestoreRequest, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())

    rows = db.scalars(
        select(CategoryModel).where(
            CategoryModel.company_id == current_user.company_id, CategoryModel.id.in_(payload.category_ids)
        )
    ).all()

    target_ids = set(payload.category_ids)

    if (
        len(rows) != len(target_ids)
        or category_id not in target_ids
        or not target_ids.issubset(category_descendant_ids(db, current_user.company_id, category_id))
    ):
        raise DomainConflictException("La selección debe pertenecer al subárbol archivado.")

    for category in rows:
        if category.parent_id and category.parent_id not in target_ids:
            parent = db.scalar(
                select(CategoryModel).where(
                    CategoryModel.id == category.parent_id, CategoryModel.company_id == current_user.company_id
                )
            )

            if not parent or not parent.is_active:
                raise DomainConflictException("Restaura primero la categoría padre.")

        category.is_active = True

    db.add(
        AuditLogModel(
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="RESTORE_CATEGORY",
            entity_type="Category",
            entity_id=category_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"restored_ids": [str(item) for item in target_ids]}),
        )
    )

    db.commit()

    return {"category_id": str(category_id), "restored_categories": len(rows), "is_active": True}
