from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.valorizacion import ValuationRequest
from salesia.modules.inventario.infrastructure_models import InventoryValuationSetting
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_valuation_setting(current_user: AuthenticatedUser, db: Session):
    setting = db.scalar(
        select(InventoryValuationSetting).where(
            InventoryValuationSetting.company_id == current_user.company_id,
            InventoryValuationSetting.product_id.is_(None),
        )
    )

    method = setting.costing_method if setting else "AVERAGE_WEIGHTED"

    return {"costing_method": method, "rounding_decimals": setting.rounding_decimals if setting else 6}


def set_valuation_setting(payload: ValuationRequest, current_user: AuthenticatedUser, db: Session):
    setting = db.scalar(
        select(InventoryValuationSetting).where(
            InventoryValuationSetting.company_id == current_user.company_id,
            InventoryValuationSetting.product_id == payload.product_id,
        )
    )

    if not setting:
        setting = InventoryValuationSetting(
            id=uuid4(),
            company_id=current_user.company_id,
            product_id=payload.product_id,
            costing_method=payload.costing_method,
            rounding_decimals=payload.rounding_decimals,
        )

        db.add(setting)

    else:
        setting.costing_method = payload.costing_method

        setting.rounding_decimals = payload.rounding_decimals

    db.commit()

    return {"costing_method": setting.costing_method, "rounding_decimals": setting.rounding_decimals}
