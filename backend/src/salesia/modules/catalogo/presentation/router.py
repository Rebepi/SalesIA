from fastapi import APIRouter

from salesia.modules.catalogo.application.auxiliares.category_descendant_ids import (
    category_descendant_ids as category_descendant_ids,
)
from salesia.modules.catalogo.application.contracts.categorias import CategoryCreateModel as CategoryCreateModel
from salesia.modules.catalogo.application.contracts.categorias import CategoryRestoreRequest as CategoryRestoreRequest
from salesia.modules.catalogo.application.contracts.categorias import CategoryUpdateModel as CategoryUpdateModel
from salesia.modules.catalogo.application.contracts.comunes import BulkUpdateOperation as BulkUpdateOperation
from salesia.modules.catalogo.application.contracts.comunes import ImportItemModel as ImportItemModel
from salesia.modules.catalogo.application.contracts.comunes import VariantUpdateModel as VariantUpdateModel
from salesia.modules.catalogo.application.contracts.cupones import CouponCreateModel as CouponCreateModel
from salesia.modules.catalogo.application.contracts.cupones import CouponValidateRequest as CouponValidateRequest
from salesia.modules.catalogo.application.contracts.garantias import (
    WarrantyClaimCreateModel as WarrantyClaimCreateModel,
)
from salesia.modules.catalogo.application.contracts.listas_precios import PriceListCreateModel as PriceListCreateModel
from salesia.modules.catalogo.application.contracts.listas_precios import (
    PriceListItemCreateModel as PriceListItemCreateModel,
)
from salesia.modules.catalogo.application.contracts.listas_precios import (
    PriceListItemUpdateModel as PriceListItemUpdateModel,
)
from salesia.modules.catalogo.application.contracts.listas_precios import PriceListUpdateModel as PriceListUpdateModel
from salesia.modules.catalogo.application.contracts.precios import PricePreviewRequest as PricePreviewRequest
from salesia.modules.catalogo.application.contracts.productos_adjuntos import (
    AttachmentCreateModel as AttachmentCreateModel,
)
from salesia.modules.catalogo.application.contracts.productos_bulk_update import BulkUpdateRequest as BulkUpdateRequest
from salesia.modules.catalogo.application.contracts.productos_codigos_barras import (
    BarcodeCreateModel as BarcodeCreateModel,
)
from salesia.modules.catalogo.application.contracts.productos_escalas import (
    VolumeTierCreateModel as VolumeTierCreateModel,
)
from salesia.modules.catalogo.application.contracts.productos_gestion import ProductCreateModel as ProductCreateModel
from salesia.modules.catalogo.application.contracts.productos_gestion import (
    ProductDuplicateModel as ProductDuplicateModel,
)
from salesia.modules.catalogo.application.contracts.productos_gestion import ProductUpdateModel as ProductUpdateModel
from salesia.modules.catalogo.application.contracts.productos_importacion import (
    ImportBatchRequest as ImportBatchRequest,
)
from salesia.modules.catalogo.application.contracts.productos_kits import KitItemCreateModel as KitItemCreateModel
from salesia.modules.catalogo.application.contracts.productos_perfil import (
    ProductCommercialProfileUpdate as ProductCommercialProfileUpdate,
)
from salesia.modules.catalogo.application.contracts.productos_variantes import VariantCreateModel as VariantCreateModel
from salesia.modules.catalogo.application.contracts.promociones import PromotionCreateModel as PromotionCreateModel
from salesia.modules.catalogo.application.contracts.promociones import PromotionUpdateModel as PromotionUpdateModel
from salesia.modules.catalogo.application.contracts.unidades import (
    UnitConversionCreateModel as UnitConversionCreateModel,
)
from salesia.modules.catalogo.application.contracts.unidades import UnitConvertRequest as UnitConvertRequest
from salesia.modules.catalogo.application.contracts.unidades import UnitCreateModel as UnitCreateModel
from salesia.modules.catalogo.presentation.routes import (
    categorias,
    cupones,
    garantias,
    listas_precios,
    precios,
    productos_adjuntos,
    productos_bulk_update,
    productos_busqueda,
    productos_codigos_barras,
    productos_consulta,
    productos_escalas,
    productos_gestion,
    productos_importacion,
    productos_kits,
    productos_perfil,
    productos_variantes,
    promociones,
    unidades,
)

router = APIRouter(tags=["Catálogo, Productos y Precios"])
router.include_router(productos_consulta.router)
router.include_router(productos_gestion.router)
router.include_router(productos_perfil.router)
router.include_router(productos_variantes.router)
router.include_router(productos_codigos_barras.router)
router.include_router(productos_busqueda.router)
router.include_router(categorias.router)
router.include_router(unidades.router)
router.include_router(listas_precios.router)
router.include_router(productos_escalas.router)
router.include_router(promociones.router)
router.include_router(cupones.router)
router.include_router(productos_adjuntos.router)
router.include_router(productos_kits.router)
router.include_router(garantias.router)
router.include_router(productos_bulk_update.router)
router.include_router(productos_importacion.router)
router.include_router(precios.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "list_products",
            "search_products_with_availability",
            "create_product",
            "get_product",
            "get_product_commercial_profile",
            "update_product_commercial_profile",
            "update_product",
            "archive_product",
            "restore_product",
            "duplicate_product",
            "list_product_variants",
            "create_product_variant",
            "create_product_barcode",
            "lookup_product_by_barcode",
            "list_categories",
            "create_category",
            "update_category",
            "category_impact",
            "archive_category",
            "restore_category",
            "list_units",
            "create_unit",
            "create_unit_conversion",
            "list_unit_conversions",
            "convert_unit_endpoint",
            "create_price_list",
            "list_price_lists",
            "update_price_list",
            "delete_price_list",
            "add_price_list_item",
            "list_price_list_items",
            "update_price_list_item",
            "delete_price_list_item",
            "create_volume_tier",
            "create_promotion",
            "list_promotions",
            "update_promotion",
            "delete_promotion",
            "create_coupon",
            "validate_coupon_endpoint",
            "create_attachment",
            "create_kit_item",
            "create_warranty_claim",
            "eligible_warranty_sales",
            "bulk_update_products",
            "import_products",
            "preview_price",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
from salesia.modules.catalogo.presentation.routes.garantias_gestion import router as warranty_management_router

router.include_router(warranty_management_router)
list_products = productos_consulta.list_products
search_products_with_availability = productos_consulta.search_products_with_availability
create_product = productos_gestion.create_product
get_product = productos_consulta.get_product
get_product_commercial_profile = productos_perfil.get_product_commercial_profile
update_product_commercial_profile = productos_perfil.update_product_commercial_profile
update_product = productos_gestion.update_product
archive_product = productos_gestion.archive_product
restore_product = productos_gestion.restore_product
duplicate_product = productos_gestion.duplicate_product
list_product_variants = productos_variantes.list_product_variants
create_product_variant = productos_variantes.create_product_variant
create_product_barcode = productos_codigos_barras.create_product_barcode
lookup_product_by_barcode = productos_busqueda.lookup_product_by_barcode
list_categories = categorias.list_categories
create_category = categorias.create_category
update_category = categorias.update_category
category_impact = categorias.category_impact
archive_category = categorias.archive_category
restore_category = categorias.restore_category
list_units = unidades.list_units
create_unit = unidades.create_unit
create_unit_conversion = unidades.create_unit_conversion
list_unit_conversions = unidades.list_unit_conversions
convert_unit_endpoint = unidades.convert_unit_endpoint
create_price_list = listas_precios.create_price_list
list_price_lists = listas_precios.list_price_lists
update_price_list = listas_precios.update_price_list
delete_price_list = listas_precios.delete_price_list
add_price_list_item = listas_precios.add_price_list_item
list_price_list_items = listas_precios.list_price_list_items
update_price_list_item = listas_precios.update_price_list_item
delete_price_list_item = listas_precios.delete_price_list_item
create_volume_tier = productos_escalas.create_volume_tier
create_promotion = promociones.create_promotion
list_promotions = promociones.list_promotions
update_promotion = promociones.update_promotion
delete_promotion = promociones.delete_promotion
create_coupon = cupones.create_coupon
validate_coupon_endpoint = cupones.validate_coupon_endpoint
create_attachment = productos_adjuntos.create_attachment
create_kit_item = productos_kits.create_kit_item
create_warranty_claim = garantias.create_warranty_claim
eligible_warranty_sales = garantias.eligible_warranty_sales
bulk_update_products = productos_bulk_update.bulk_update_products
import_products = productos_importacion.import_products
preview_price = precios.preview_price
