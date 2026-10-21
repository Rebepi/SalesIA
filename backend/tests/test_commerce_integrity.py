import secrets
import asyncio
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, BranchModel, WarehouseModel, CustomerModel, ProductModel, InventoryStockModel, UserModel, SaleModel, PaymentModel, KardexMovementModel
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.infrastructure.transactions import RefundModel


@pytest.fixture
def business():
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Comercio", trade_name="Comercio", base_currency="USD")
        db.add(company)
        db.flush()
        branch = BranchModel(company_id=company.id, code="ONE", name="Sucursal")
        customer = CustomerModel(company_id=company.id, code="C1", doc_type="TEST", doc_number=uuid4().hex, legal_name="Cliente", credit_limit=Decimal("1000"), current_balance=Decimal("0"))
        product = ProductModel(company_id=company.id, sku="SKU1", name="Producto", category="GENERAL", unit_of_measure="NIU", unit_price=Decimal("100"), unit_cost=Decimal("50"), tax_rate=Decimal("0"))
        password = secrets.token_urlsafe(24)
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add_all([branch, customer, product, user])
        db.flush()
        warehouse = WarehouseModel(company_id=company.id, branch_id=branch.id, code="ONE", name="Almacén")
        db.add(warehouse)
        db.flush()
        stock = InventoryStockModel(company_id=company.id, warehouse_id=warehouse.id, product_id=product.id, physical_quantity=Decimal("10"), reserved_quantity=Decimal("0"))
        db.add(stock)
        db.commit()
        return {"email": user.email, "password": password, "user_id": user.id, "company_id": company.id, "stock_id": stock.id, "customer_id": customer.id, "draft": {"branch_id": str(branch.id), "customer_id": str(customer.id), "warehouse_id": str(warehouse.id), "currency": "USD", "lines": [{"product_id": str(product.id), "sku": product.sku, "product_name": product.name, "quantity": 1, "unit_price": "1", "cost_snapshot": "0", "tax_rate": "0"}]}}


async def authenticate(client, business):
    response = await client.post("/api/v1/auth/login", json={"email": business["email"], "password": business["password"]})
    assert response.status_code == 200, response.text
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"


async def confirmed_sale(client, business):
    draft = await client.post("/api/v1/sales", json=business["draft"], headers={"Idempotency-Key": uuid4().hex})
    assert draft.status_code == 201, draft.text
    assert Decimal(draft.json()["total_amount"]) == 100
    sale_id = draft.json()["sale_id"]
    response = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"is_credit_sale": False}, headers={"Idempotency-Key": uuid4().hex})
    assert response.status_code == 200, response.text
    return sale_id


@pytest.mark.asyncio
async def test_confirmation_idempotent_and_authoritative_price(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        sale_id = await confirmed_sale(client, business)
        assert (await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={"Idempotency-Key": uuid4().hex})).status_code == 200
        with sync_session_factory() as db:
            assert db.get(InventoryStockModel, business["stock_id"]).physical_quantity == 9
            assert db.scalar(select(func.count()).select_from(KardexMovementModel).where(KardexMovementModel.reference_doc_id == UUID(sale_id))) == 1


@pytest.mark.asyncio
async def test_payment_refund_limits_and_idempotence(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        sale_id = await confirmed_sale(client, business)
        payload = {"sale_id": sale_id, "payment_method": "CASH", "amount": "100", "currency": "USD"}
        key = {"Idempotency-Key": uuid4().hex}
        response = await client.post("/api/v1/payments", json=payload, headers=key)
        assert response.status_code == 201, response.text
        payment_id = response.json()["id"]
        repeat = await client.post("/api/v1/payments", json=payload, headers=key)
        assert repeat.json()["id"] == payment_id
        assert (await client.post("/api/v1/payments", json={**payload, "amount": "99"}, headers=key)).status_code == 409
        refund = {"payment_id": payment_id, "amount": "60", "reason": "Reembolso parcial"}
        refund_key = {"Idempotency-Key": uuid4().hex}
        response = await client.post("/api/v1/refunds", json=refund, headers=refund_key)
        assert response.status_code == 201, response.text
        assert (await client.post("/api/v1/refunds", json=refund, headers=refund_key)).json()["refund_id"] == response.json()["refund_id"]
        assert (await client.post("/api/v1/refunds", json=refund, headers={"Idempotency-Key": uuid4().hex})).status_code == 409
        with sync_session_factory() as db:
            assert db.get(SaleModel, UUID(sale_id)).paid_amount == 40
            assert db.scalar(select(func.sum(RefundModel.amount)).where(RefundModel.payment_id == UUID(payment_id))) == 60
            assert db.scalar(select(func.count()).select_from(PaymentModel).where(PaymentModel.sale_id == UUID(sale_id))) == 1


@pytest.mark.asyncio
async def test_missing_stock_rolls_back_and_retry_works(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        draft = (await client.post("/api/v1/sales", json=business["draft"], headers={"Idempotency-Key": uuid4().hex})).json()
        with sync_session_factory() as db:
            db.get(InventoryStockModel, business["stock_id"]).physical_quantity = 0
            db.commit()
        key = {"Idempotency-Key": uuid4().hex}
        response = await client.post(f"/api/v1/sales/{draft['sale_id']}/confirm", headers=key)
        assert response.status_code == 409, response.text
        with sync_session_factory() as db:
            assert db.get(SaleModel, UUID(draft["sale_id"])).status == "draft"
            db.get(InventoryStockModel, business["stock_id"]).physical_quantity = 1
            db.commit()
        assert (await client.post(f"/api/v1/sales/{draft['sale_id']}/confirm", headers=key)).status_code == 200


@pytest.mark.asyncio
async def test_invalid_references_never_create_placeholder_data(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        payload = {**business["draft"], "customer_id": str(uuid4())}
        assert (await client.post("/api/v1/sales", json=payload, headers={"Idempotency-Key": uuid4().hex})).status_code == 422
        with sync_session_factory() as db:
            assert db.scalar(select(func.count()).select_from(SaleModel).where(SaleModel.company_id == business["company_id"])) == 0


@pytest.mark.asyncio
async def test_concurrent_last_unit_is_not_oversold(business):
    from salesia.shared.infrastructure.database import sync_engine
    if sync_engine.dialect.name != "postgresql":
        pytest.skip("Esta prueba requiere bloqueos reales de PostgreSQL")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        first = (await client.post("/api/v1/sales", json=business["draft"], headers={"Idempotency-Key": uuid4().hex})).json()["sale_id"]
        second = (await client.post("/api/v1/sales", json=business["draft"], headers={"Idempotency-Key": uuid4().hex})).json()["sale_id"]
        with sync_session_factory() as db:
            db.get(InventoryStockModel, business["stock_id"]).physical_quantity = 1
            db.commit()
        results = await asyncio.gather(client.post(f"/api/v1/sales/{first}/confirm", headers={"Idempotency-Key": uuid4().hex}), client.post(f"/api/v1/sales/{second}/confirm", headers={"Idempotency-Key": uuid4().hex}))
        assert sorted(response.status_code for response in results) == [200, 409]
        with sync_session_factory() as db:
            assert db.get(InventoryStockModel, business["stock_id"]).physical_quantity == 0
            assert db.scalar(select(func.count()).select_from(SaleModel).where(SaleModel.company_id == business["company_id"], SaleModel.status == "confirmed")) == 1


@pytest.mark.asyncio
async def test_settings_zero_persists_and_stale_version_rejected(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        response = await client.patch("/api/v1/companies/current/settings", json={"version": 0, "default_tax_rate": "0"})
        assert response.status_code == 200, response.text
        settings = (await client.get("/api/v1/settings")).json()
        assert Decimal(settings["default_tax_rate"]) == 0
        assert (await client.patch("/api/v1/companies/current/settings", json={"version": 0, "default_tax_rate": "0.18"})).status_code == 409


@pytest.mark.asyncio
async def test_dashboard_excludes_draft_from_average(business):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await authenticate(client, business)
        await confirmed_sale(client, business)
        assert (await client.post("/api/v1/sales", json=business["draft"], headers={"Idempotency-Key": uuid4().hex})).status_code == 201
        response = await client.get("/api/v1/dashboard/summary?period=all")
        assert response.status_code == 200, response.text
        assert response.json()["orders_count"] == 1
        assert Decimal(response.json()["average_ticket"]) == 100


def test_rls_isolation_with_non_owner_role(business):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from salesia.shared.infrastructure.database import sync_engine
    if sync_engine.dialect.name != "postgresql":
        pytest.skip("RLS requiere PostgreSQL")
    role = "salesia_test_" + uuid4().hex
    with sync_engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS'))
            connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role}"'))
            connection.execute(text(f'GRANT SELECT, INSERT ON customers TO "{role}"'))
            connection.execute(text(f'SET LOCAL ROLE "{role}"'))
            connection.execute(text("SELECT set_config('app.current_company_id', :company, true)"), {"company": str(business["company_id"])})
            assert connection.scalar(text("SELECT count(*) FROM customers")) == 1
            connection.execute(text("SELECT set_config('app.current_company_id', :company, true)"), {"company": str(uuid4())})
            assert connection.scalar(text("SELECT count(*) FROM customers")) == 0
            with pytest.raises(DBAPIError):
                connection.execute(text("INSERT INTO customers (id, company_id, code, doc_type, doc_number, legal_name, credit_limit, current_balance, is_active, created_at, updated_at) VALUES (:id, :company, 'X', 'TEST', 'NONE', 'Invalid', 0, 0, true, now(), now())"), {"id": str(uuid4()), "company": str(business["company_id"])})
        finally:
            transaction.rollback()
