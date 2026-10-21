from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.productos_escalas import VolumeTierCreateModel
from salesia.modules.catalogo.infrastructure_models import ProductVolumeTierModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_volume_tier(product_id: UUID, req: VolumeTierCreateModel, current_user: AuthenticatedUser, db: Session):
    tier = ProductVolumeTierModel(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=product_id,
        min_quantity=req.min_quantity,
        unit_price=req.unit_price,
        discount_percentage=req.discount_percentage,
    )

    db.add(tier)

    db.commit()

    return {
        "id": str(tier.id),
        "product_id": str(tier.product_id),
        "min_quantity": str(tier.min_quantity),
        "unit_price": str(tier.unit_price) if tier.unit_price is not None else None,
        "discount_percentage": str(tier.discount_percentage) if tier.discount_percentage is not None else None,
    }
