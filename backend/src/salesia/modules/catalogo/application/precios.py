from decimal import Decimal

from sqlalchemy.orm import Session

from salesia.modules.catalogo.application.contracts.precios import PricePreviewRequest
from salesia.modules.catalogo.service import resolve_product_price
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel


def preview_price(req: PricePreviewRequest, current_user: AuthenticatedUser, db: Session):
    result = resolve_product_price(
        db=db,
        company_id=current_user.company_id,
        product_id=req.product_id,
        quantity=req.quantity,
        customer_id=req.customer_id,
        variant_id=req.variant_id,
        coupon_code=req.coupon_code,
    )

    if "products:cost:read" in current_user.permissions:
        product = db.get(ProductModel, req.product_id)

        if product:
            result["unit_cost"] = str(product.unit_cost)

            result["estimated_margin"] = str(Decimal(result["final_unit_price"]) - product.unit_cost)

    return result
