from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, BranchModel, WarehouseModel, ProductModel, InventoryStockModel, UserModel, KardexMovementModel
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.inventario.infrastructure_models import SupplyDocument, Supplier


@pytest.fixture
def supply():
    password = "A-valid-test-password-2026"
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Supply", trade_name="Supply")
        db.add(company); db.flush()
        branch = BranchModel(company_id=company.id, code="B", name="Sucursal")
        product = ProductModel(company_id=company.id, sku="P", name="Producto", category="General", unit_of_measure="NIU", unit_price=Decimal("20"), unit_cost=Decimal("5"), tax_rate=Decimal("0"))
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add_all([branch, product, user]); db.flush()
        first = WarehouseModel(company_id=company.id, branch_id=branch.id, code="A", name="Origen")
        second = WarehouseModel(company_id=company.id, branch_id=branch.id, code="B", name="Destino")
        db.add_all([first, second]); db.flush()
        db.add(InventoryStockModel(company_id=company.id, warehouse_id=first.id, product_id=product.id, physical_quantity=Decimal("10"), reserved_quantity=Decimal("0"), average_cost=Decimal("5")))
        db.commit()
        return {"email": user.email, "password": password, "user_id": user.id, "company_id": company.id, "product_id": product.id, "source": first.id, "destination": second.id}


async def client_for(data):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    login = await client.post("/api/v1/auth/login", json={"email": data["email"], "password": data["password"]})
    assert login.status_code == 200, login.text
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


@pytest.mark.asyncio
async def test_transfer_is_durable_idempotent_and_balanced(supply):
    client = await client_for(supply)
    try:
        payload = {"source_warehouse_id": str(supply["source"]), "destination_warehouse_id": str(supply["destination"]), "items": [{"product_id": str(supply["product_id"]), "quantity": "3", "unit_cost": "5"}]}
        created = await client.post("/api/v1/inventory/transfers", json=payload, headers={"Idempotency-Key": uuid4().hex})
        assert created.status_code == 201, created.text
        transfer_id = created.json()["id"]
        dispatch_key = {"Idempotency-Key": uuid4().hex}
        assert (await client.post(f"/api/v1/inventory/transfers/{transfer_id}/dispatch", headers=dispatch_key)).status_code == 200
        assert (await client.post(f"/api/v1/inventory/transfers/{transfer_id}/dispatch", headers=dispatch_key)).status_code == 200
        receive_key = {"Idempotency-Key": uuid4().hex}
        assert (await client.post(f"/api/v1/inventory/transfers/{transfer_id}/receive", headers=receive_key)).status_code == 200
        assert (await client.post(f"/api/v1/inventory/transfers/{transfer_id}/receive", headers=receive_key)).status_code == 200
        with sync_session_factory() as db:
            rows = db.scalars(select(InventoryStockModel).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == supply["product_id"])).all()
            assert sum(row.physical_quantity for row in rows) == 10
            assert {row.warehouse_id: row.physical_quantity for row in rows} == {supply["source"]: 7, supply["destination"]: 3}
            assert db.scalar(select(func.count()).select_from(KardexMovementModel).where(KardexMovementModel.reference_doc_id == UUID(transfer_id))) == 2
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_purchase_receipt_limits_and_weighted_cost(supply):
    client = await client_for(supply)
    try:
        supplier = await client.post("/api/v1/suppliers", json={"tax_id": uuid4().hex, "legal_name": "Proveedor"})
        assert supplier.status_code == 201, supplier.text
        order = await client.post("/api/v1/purchase-orders", json={"supplier_id": supplier.json()["id"], "warehouse_id": str(supply["source"]), "currency": "USD", "items": [{"product_id": str(supply["product_id"]), "quantity": "4", "unit_cost": "15"}]}, headers={"Idempotency-Key": uuid4().hex})
        assert order.status_code == 201, order.text
        receipt = {"purchase_order_id": order.json()["id"], "warehouse_id": str(supply["source"]), "items": [{"product_id": str(supply["product_id"]), "quantity": "3", "unit_cost": "15"}]}
        key = {"Idempotency-Key": uuid4().hex}
        result = await client.post("/api/v1/goods-receipts", json=receipt, headers=key)
        assert result.status_code == 201, result.text
        assert (await client.post("/api/v1/goods-receipts", json=receipt, headers=key)).json()["id"] == result.json()["id"]
        excessive = {**receipt, "items": [{"product_id": str(supply["product_id"]), "quantity": "2", "unit_cost": "15"}]}
        assert (await client.post("/api/v1/goods-receipts", json=excessive, headers={"Idempotency-Key": uuid4().hex})).status_code == 409
        with sync_session_factory() as db:
            stock = db.scalar(select(InventoryStockModel).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.warehouse_id == supply["source"], InventoryStockModel.product_id == supply["product_id"]))
            assert stock.physical_quantity == 13
            assert stock.average_cost == Decimal("7.307692")
            assert db.scalar(select(func.count()).select_from(SupplyDocument).where(SupplyDocument.company_id == supply["company_id"], SupplyDocument.kind == "GOODS_RECEIPT")) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_unknown_transfer_and_invalid_adjustment_fail_without_side_effect(supply):
    client = await client_for(supply)
    try:
        assert (await client.post(f"/api/v1/inventory/transfers/{uuid4()}/receive", headers={"Idempotency-Key": uuid4().hex})).status_code == 404
        result = await client.post("/api/v1/inventory/adjustments", json={"warehouse_id": str(uuid4()), "product_id": str(supply["product_id"]), "quantity_delta": "1", "reason": "Prueba"}, headers={"Idempotency-Key": uuid4().hex})
        assert result.status_code == 422
    finally:
        await client.aclose()
