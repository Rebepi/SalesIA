from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel


def get_or_create_product_profile(
    db: Session,
    company_id: UUID,
    product_id: UUID,
    product_type: str = "product",
    track_inventory: bool = True,
    status: str = "active",
) -> ProductProfileModel:
    profile = db.execute(
        select(ProductProfileModel).where(
            ProductProfileModel.company_id == company_id, ProductProfileModel.product_id == product_id
        )
    ).scalar_one_or_none()
    if not profile:
        profile = ProductProfileModel(
            id=uuid4(),
            company_id=company_id,
            product_id=product_id,
            product_type=product_type,
            track_inventory=track_inventory,
            status=status,
        )
        db.add(profile)
        db.flush()
    return profile
