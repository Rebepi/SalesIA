from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import CategoryModel
from salesia.shared.infrastructure.errors import DomainConflictException, DomainNotFoundException


def validate_no_category_cycle(db: Session, company_id: UUID, category_id: UUID, new_parent_id: Optional[UUID]) -> int:
    if new_parent_id is None:
        return 1
    if new_parent_id == category_id:
        raise DomainConflictException("Una categoría no puede ser su propio padre jerárquico.")

    parent = db.execute(
        select(CategoryModel).where(CategoryModel.company_id == company_id, CategoryModel.id == new_parent_id)
    ).scalar_one_or_none()
    if not parent:
        raise DomainNotFoundException("La categoría padre especificada no existe.")

    current = parent
    visited = {category_id}
    depth = 1
    while current is not None:
        if current.id in visited:
            raise DomainConflictException("Referencia circular detectada en el árbol de categorías.")
        visited.add(current.id)
        depth += 1
        if depth > 5:
            raise DomainConflictException(
                "La jerarquía de categorías excede la profundidad máxima permitida de 5 niveles."
            )
        if current.parent_id is None:
            break
        current = db.execute(
            select(CategoryModel).where(CategoryModel.company_id == company_id, CategoryModel.id == current.parent_id)
        ).scalar_one_or_none()

    return parent.level + 1
