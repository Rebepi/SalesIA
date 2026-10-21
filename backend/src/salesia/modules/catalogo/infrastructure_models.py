from datetime import datetime as datetime
from decimal import Decimal as Decimal
from typing import Optional as Optional
from uuid import UUID as UUID
from uuid import uuid4 as uuid4

from sqlalchemy import Boolean as Boolean
from sqlalchemy import CheckConstraint as CheckConstraint
from sqlalchemy import DateTime as DateTime
from sqlalchemy import ForeignKey as ForeignKey
from sqlalchemy import Integer as Integer
from sqlalchemy import Numeric as Numeric
from sqlalchemy import String as String
from sqlalchemy import Text as Text
from sqlalchemy import UniqueConstraint as UniqueConstraint
from sqlalchemy.orm import Mapped as Mapped
from sqlalchemy.orm import mapped_column as mapped_column

from salesia.modules.catalogo.infrastructure.models.clasificacion import CategoryModel as CategoryModel
from salesia.modules.catalogo.infrastructure.models.clasificacion import UnitConversionModel as UnitConversionModel
from salesia.modules.catalogo.infrastructure.models.clasificacion import UnitOfMeasureModel as UnitOfMeasureModel
from salesia.modules.catalogo.infrastructure.models.precios import CouponModel as CouponModel
from salesia.modules.catalogo.infrastructure.models.precios import PriceListItemModel as PriceListItemModel
from salesia.modules.catalogo.infrastructure.models.precios import PriceListModel as PriceListModel
from salesia.modules.catalogo.infrastructure.models.precios import ProductPriceHistoryModel as ProductPriceHistoryModel
from salesia.modules.catalogo.infrastructure.models.precios import ProductVolumeTierModel as ProductVolumeTierModel
from salesia.modules.catalogo.infrastructure.models.precios import PromotionModel as PromotionModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductModel as ProductModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductAttachmentModel as ProductAttachmentModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductBarcodeModel as ProductBarcodeModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductKitItemModel as ProductKitItemModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductProfileModel as ProductProfileModel
from salesia.modules.catalogo.infrastructure.models.productos import ProductVariantModel as ProductVariantModel
from salesia.modules.catalogo.infrastructure.models.productos import (
    ProductWarrantyClaimModel as ProductWarrantyClaimModel,
)
from salesia.shared.infrastructure.database import Base as Base
from salesia.shared.infrastructure.database import TimestampMixin as TimestampMixin