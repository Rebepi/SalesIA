import secrets
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, CustomerModel, InventoryStockModel, ProductModel, UserModel, WarehouseModel


@pytest.fixture
def order_data():
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Pedidos", trade_name="Pedidos")
        db.add(company)
        db.flush()
        branch = BranchModel(company_id=company.id, code=uuid4().hex[:8], name="Principal")
        customer = CustomerModel(company_id=company.id, code=uuid4().hex[:8], doc_type="RUC", doc_number=uuid4().hex, legal_name="Cliente")
        product = ProductModel(company_id=company.id, sku=uuid4().hex[:8], name="Producto", category="General", unit_of_measure="NIU", unit_price=Decimal("100"), unit_cost=Decimal("40"), tax_rate=Decimal("0.18"))
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add_all([branch, customer, product, user])
        db.flush()
        warehouse = WarehouseModel(company_id=company.id, branch_id=branch.id, code=uuid4().hex[:8], name="Central")
        db.add(warehouse)
        db.flush()
        db.add(InventoryStockModel(company_id=company.id, warehouse_id=warehouse.id, product_id=product.id, physical_quantity=Decimal("5"), reserved_quantity=Decimal("0"), average_cost=Decimal("40")))
        db.commit()
        return {"email": user.email, "password": password, "company": company.id, "branch": branch.id, "customer": customer.id, "product": product.id, "warehouse": warehouse.id}


async def client_for(data):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    response = await client.post("/api/v1/auth/login", json={"email": data["email"], "password": data["password"]})
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


@pytest.mark.asyncio
async def test_order_uses_authoritative_price_and_balanced_reservation(order_data):
    client = await client_for(order_data)
    try:
        payload = {"customer_id": str(order_data["customer"]), "branch_id": str(order_data["branch"]), "warehouse_id": str(order_data["warehouse"]), "currency": "USD", "lines": [{"product_id": str(order_data["product"]), "quantity": "2", "discount_pct": "0"}]}
        created = await client.post("/api/v1/orders", json=payload, headers={"Idempotency-Key": uuid4().hex})
        assert created.status_code == 201, created.text
        assert created.json()["lines"][0]["unit_price"] == "100.000000"
        order_id = created.json()["order_id"]
        confirm_key = {"Idempotency-Key": uuid4().hex}
        first = await client.post(f"/api/v1/orders/{order_id}/confirm", headers=confirm_key)
        assert first.status_code == 200, first.text
        assert (await client.post(f"/api/v1/orders/{order_id}/confirm", headers=confirm_key)).status_code == 200
        fulfilled = await client.post(f"/api/v1/orders/{order_id}/fulfill-partial", json={"fulfilled_items": [{"product_id": str(order_data["product"]), "quantity": "1"}]}, headers={"Idempotency-Key": uuid4().hex})
        assert fulfilled.status_code == 200, fulfilled.text
        cancelled = await client.post(f"/api/v1/orders/{order_id}/cancel", headers={"Idempotency-Key": uuid4().hex})
        assert cancelled.status_code == 200, cancelled.text
        with sync_session_factory() as db:
            stock = db.scalar(select(InventoryStockModel).where(InventoryStockModel.company_id == order_data["company"], InventoryStockModel.product_id == order_data["product"]))
            assert stock.physical_quantity == 4
            assert stock.reserved_quantity == 0
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_unknown_order_and_cash_session_never_fake_success(order_data):
    client = await client_for(order_data)
    try:
        assert (await client.get(f"/api/v1/orders/{uuid4()}")).status_code == 404
        close = await client.post(f"/api/v1/cash-sessions/{uuid4()}/close", json={"counted_balance": "0"}, headers={"Idempotency-Key": uuid4().hex})
        assert close.status_code == 404
        opened = await client.post("/api/v1/cash-sessions", json={"branch_id": str(order_data["branch"]), "terminal_code": "POS-1", "opening_balance": "100"}, headers={"Idempotency-Key": uuid4().hex})
        assert opened.status_code == 201, opened.text
        movement = await client.post(f"/api/v1/cash-sessions/{opened.json()['session_id']}/movements", json={"movement_type": "WITHDRAWAL", "amount": "20", "reason": "Gasto operativo"}, headers={"Idempotency-Key": uuid4().hex})
        assert movement.status_code == 201, movement.text
        closed = await client.post(f"/api/v1/cash-sessions/{opened.json()['session_id']}/close", json={"counted_balance": "80"}, headers={"Idempotency-Key": uuid4().hex})
        assert closed.status_code == 200, closed.text
        assert closed.json()["difference"] == "0.000000"
    finally:
        await client.aclose()
