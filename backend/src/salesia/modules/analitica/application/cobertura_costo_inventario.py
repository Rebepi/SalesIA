from sqlalchemy import case, func, select

from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, WarehouseModel


def cost_coverage(db, user, branch_id, category):
    filters = [InventoryStockModel.company_id == user.company_id, ProductModel.company_id == user.company_id]
    if branch_id:
        filters.append(InventoryStockModel.warehouse_id.in_(select(WarehouseModel.id).where(WarehouseModel.company_id == user.company_id, WarehouseModel.branch_id == branch_id)))
    if category:
        filters.append(ProductModel.category == category)
    rows = db.execute(select(ProductModel.id, ProductModel.name, ProductModel.sku, func.sum(InventoryStockModel.physical_quantity), func.max(case(((InventoryStockModel.physical_quantity > 0) & (InventoryStockModel.average_cost <= 0), 1), else_=0))).join(ProductModel, ProductModel.id == InventoryStockModel.product_id).where(*filters).group_by(ProductModel.id, ProductModel.name, ProductModel.sku).having(func.sum(InventoryStockModel.physical_quantity) > 0).order_by(ProductModel.sku, ProductModel.id)).all()
    missing = [{"id": str(row[0]), "producto": row[1], "sku": row[2], "estado": "Por revisar"} for row in rows if row[4]]
    return {"products_with_stock": len(rows), "valued_products": len(rows) - len(missing), "missing_count": len(missing), "status": "review" if missing else "available", "items": missing}
