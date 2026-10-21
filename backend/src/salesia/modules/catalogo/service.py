from datetime import datetime as datetime
from datetime import timezone as timezone
from decimal import ROUND_HALF_EVEN as ROUND_HALF_EVEN
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import func as func
from sqlalchemy import or_ as or_
from sqlalchemy import select as select
from sqlalchemy.orm import Session as Session

from salesia.modules.catalogo.application.catalogo.categorias import (
    validate_no_category_cycle as validate_no_category_cycle,
)
from salesia.modules.catalogo.application.catalogo.fechas import ensure_utc as ensure_utc
from salesia.modules.catalogo.application.catalogo.perfiles import (
    get_or_create_product_profile as get_or_create_product_profile,
)
from salesia.modules.catalogo.application.catalogo.precios import resolve_product_price as resolve_product_price
from salesia.modules.catalogo.application.catalogo.unidades import convert_units as convert_units
from salesia.modules.catalogo.application.catalogo.unidades import validate_unit_fraction as validate_unit_fraction
from salesia.modules.catalogo.infrastructure_models import CategoryModel as CategoryModel
from salesia.modules.catalogo.infrastructure_models import CouponModel as CouponModel
from salesia.modules.catalogo.infrastructure_models import PriceListItemModel as PriceListItemModel
from salesia.modules.catalogo.infrastructure_models import PriceListModel as PriceListModel
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel as ProductProfileModel
from salesia.modules.catalogo.infrastructure_models import ProductVariantModel as ProductVariantModel
from salesia.modules.catalogo.infrastructure_models import ProductVolumeTierModel as ProductVolumeTierModel
from salesia.modules.catalogo.infrastructure_models import PromotionModel as PromotionModel
from salesia.modules.catalogo.infrastructure_models import UnitConversionModel as UnitConversionModel
from salesia.modules.catalogo.infrastructure_models import UnitOfMeasureModel as UnitOfMeasureModel
from salesia.modules.clientes.infrastructure.models import CustomerProfileModel as CustomerProfileModel
from salesia.shared.infrastructure.errors import DomainConflictException as DomainConflictException
from salesia.shared.infrastructure.errors import DomainForbiddenException as DomainForbiddenException
from salesia.shared.infrastructure.errors import DomainNotFoundException as DomainNotFoundException
from salesia.shared.infrastructure.models import ProductModel as ProductModel
