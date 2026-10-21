from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import CategoryModel


def category_descendant_ids(db: Session, company_id: UUID, category_id: UUID) -> set[UUID]:

    found = {category_id}

    pending = [category_id]

    while pending:
        children = db.scalars(
            select(CategoryModel.id).where(CategoryModel.company_id == company_id, CategoryModel.parent_id.in_(pending))
        ).all()

        pending = [item for item in children if item not in found]

        found.update(pending)

    return found
