from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_kits import KitItemCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductKitItemModel
from salesia.modules.catalogo.service import get_or_create_product_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel


def create_kit_item(product_id: UUID, req: KitItemCreateModel, current_user: AuthenticatedUser, db: Session):
    from salesia.modules.organizacion.application.perfil_operativo import require_area
    require_area(db, current_user.company_id, "inventory")
    kit_product = db.execute(
        select(ProductModel).where(ProductModel.company_id == current_user.company_id, ProductModel.id == product_id)
    ).scalar_one_or_none()

    if not kit_product:
        raise DomainNotFoundException("Producto kit no encontrado.")

    comp_product = db.execute(
        select(ProductModel).where(
            ProductModel.company_id == current_user.company_id, ProductModel.id == req.component_product_id
        )
    ).scalar_one_or_none()

    if not comp_product:
        raise DomainNotFoundException("Producto componente no encontrado.")

    profile = get_or_create_product_profile(db, current_user.company_id, kit_product.id)

    profile.is_kit = True

    kit_item = ProductKitItemModel(
        id=uuid4(),
        company_id=current_user.company_id,
        kit_product_id=kit_product.id,
        component_product_id=comp_product.id,
        quantity=req.quantity,
    )

    db.add(kit_item)

    db.commit()

    return {
        "id": str(kit_item.id),
        "kit_product_id": str(kit_item.kit_product_id),
        "component_product_id": str(kit_item.component_product_id),
        "quantity": str(kit_item.quantity),
    }
