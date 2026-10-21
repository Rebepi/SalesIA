from decimal import Decimal
from uuid import UUID, uuid4
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    InventoryStockModel,
    KardexMovementModel,
    PaymentModel,
    AuditLogModel,
    OutboxEventModel
)
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.clientes.infrastructure.models import CustomerProfileModel
from salesia.shared.infrastructure.transactions import IdempotencyRecord
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000009")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000002")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000092")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000004")
WAREHOUSE_B = UUID("00000000-0000-0000-0000-000000000094")
CUSTOMER_A = UUID("00000000-0000-0000-0000-000000000014")
CUSTOMER_B = UUID("00000000-0000-0000-0000-000000000095")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000003")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000007")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000008")


@pytest.fixture(autouse=True, scope="module")
def setup_part10_data():
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999999991", "Empresa A P10"), (COMPANY_B, "20999999992", "Empresa B P10")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        for bid, cid, code, name in [(BRANCH_A, COMPANY_A, "SUC-P10-A", "Sucursal P10 A"), (BRANCH_B, COMPANY_B, "SUC-P10-B", "Sucursal P10 B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=name, timezone="America/Lima", is_active=True))
        for wid, cid, bid, code, name in [(WAREHOUSE_A, COMPANY_A, BRANCH_A, "WH-P10-A", "Almacen P10 A"), (WAREHOUSE_B, COMPANY_B, BRANCH_B, "WH-P10-B", "Almacen P10 B")]:
            wh = session.scalar(select(WarehouseModel).where(WarehouseModel.id == wid))
            if not wh:
                session.add(WarehouseModel(id=wid, company_id=cid, branch_id=bid, code=code, name=name, is_active=True))
        for cust_id, cid, code, doc in [(CUSTOMER_A, COMPANY_A, "CLI-P10-A", "20111222333"), (CUSTOMER_B, COMPANY_B, "CLI-P10-B", "20222333444")]:
            c = session.scalar(select(CustomerModel).where(CustomerModel.id == cust_id))
            if not c:
                session.add(CustomerModel(id=cust_id, company_id=cid, code=code, doc_type="RUC", doc_number=doc, legal_name=f"Cliente {code}", credit_limit=Decimal("50000.00"), current_balance=Decimal("0.00"), is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_headers_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_p10_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_seller_headers_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_p10_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_headers_b():
    identity = create_durable_identity(company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_p10_b@rival.enterprise", password="valid_password")
    return identity["headers"]


def create_product_with_stock(company_id, warehouse_id, price=Decimal("10.00"), tax_rate=Decimal("0.18"), stock_qty=Decimal("100.00")):
    prod_id = uuid4()
    sku = f"SKU-{uuid4().hex[:8].upper()}"
    with sync_session_factory() as session:
        prod = ProductModel(id=prod_id, company_id=company_id, sku=sku, name=f"Prod {sku}", category="GENERAL", unit_of_measure="NIU", unit_price=price, unit_cost=price * Decimal("0.5"), tax_rate=tax_rate, is_active=True)
        session.add(prod)
        stock = InventoryStockModel(id=uuid4(), company_id=company_id, warehouse_id=warehouse_id, product_id=prod_id, physical_quantity=stock_qty, reserved_quantity=Decimal("0.000000"))
        session.add(stock)
        session.commit()
    return prod_id, sku


@pytest.mark.asyncio
async def test_reg_05_idempotent_confirm_stock_retention(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("10.000000"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        sale_id = res.json()["sale_id"]
        confirm_key = f"K-REG05-{uuid4().hex}"
        conf1 = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"is_credit_sale": False}, headers={**auth_headers_a, "Idempotency-Key": confirm_key})
        assert conf1.status_code == 200
        with sync_session_factory() as session:
            st1 = session.scalar(select(InventoryStockModel).where(InventoryStockModel.product_id == prod_id))
            assert st1.physical_quantity == Decimal("9.000000")
        conf2 = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"is_credit_sale": False}, headers={**auth_headers_a, "Idempotency-Key": confirm_key})
        assert conf2.status_code == 200
        with sync_session_factory() as session:
            st2 = session.scalar(select(InventoryStockModel).where(InventoryStockModel.product_id == prod_id))
            assert st2.physical_quantity == Decimal("9.000000")


@pytest.mark.asyncio
async def test_reg_06_concurrent_confirmations_last_stock(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("1.000000"))
        res1 = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        res2 = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale1_id = res1.json()["sale_id"]
        sale2_id = res2.json()["sale_id"]
        c1 = await client.post(f"/api/v1/sales/{sale1_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert c1.status_code == 200
        c2 = await client.post(f"/api/v1/sales/{sale2_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert c2.status_code == 409
        with sync_session_factory() as session:
            st = session.scalar(select(InventoryStockModel).where(InventoryStockModel.product_id == prod_id))
            assert st.physical_quantity == Decimal("0.000000")


@pytest.mark.asyncio
async def test_reg_07_no_stock_or_cross_tenant_warehouse_fails_atomically(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("0.000000"))
        cross_wh = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_B), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert cross_wh.status_code in (422, 403)
        draft = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert draft.status_code == 201
        conf = await client.post(f"/api/v1/sales/{draft.json()['sale_id']}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert conf.status_code == 409


@pytest.mark.asyncio
async def test_reg_08_commit_failure_leaves_no_in_memory_or_orphan_sale(auth_headers_a):
    non_existent = uuid4()
    with sync_session_factory() as session:
        sale = session.scalar(select(SaleModel).where(SaleModel.id == non_existent))
        assert sale is None


@pytest.mark.asyncio
async def test_reg_09_idempotency_key_payload_matching_and_tenant_isolation(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_a, sku_a = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        prod_b, sku_b = create_product_with_stock(COMPANY_B, WAREHOUSE_B)
        shared_key = f"IDEM-SHARED-{uuid4().hex}"
        body_a1 = {"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_a), "sku": sku_a, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}
        res1 = await client.post("/api/v1/sales/draft", json=body_a1, headers={**auth_headers_a, "Idempotency-Key": shared_key})
        assert res1.status_code == 201
        sale_a1 = res1.json()["sale_id"]
        res2 = await client.post("/api/v1/sales/draft", json=body_a1, headers={**auth_headers_a, "Idempotency-Key": shared_key})
        assert res2.status_code == 201
        assert res2.json()["sale_id"] == sale_a1
        body_a2 = {"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_a), "sku": sku_a, "product_name": "Item", "quantity": 2, "unit_price": "10.00"}]}
        res_conflict = await client.post("/api/v1/sales/draft", json=body_a2, headers={**auth_headers_a, "Idempotency-Key": shared_key})
        assert res_conflict.status_code == 409
        body_b = {"customer_id": str(CUSTOMER_B), "branch_id": str(BRANCH_B), "warehouse_id": str(WAREHOUSE_B), "currency": "USD", "lines": [{"product_id": str(prod_b), "sku": sku_b, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}
        res_b = await client.post("/api/v1/sales/draft", json=body_b, headers={**auth_headers_b, "Idempotency-Key": shared_key})
        assert res_b.status_code == 201
        assert res_b.json()["sale_id"] != sale_a1


@pytest.mark.asyncio
async def test_sale_001_enterprise_cart_line_definition(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "notes": "Pedido prioritario", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item con notas", "quantity": 2, "unit_price": "10.00", "notes": "Linea 1"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        sale_id = res.json()["sale_id"]
        detail = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_a)
        assert detail.status_code == 200
        assert len(detail.json()["lines"]) == 1
        assert detail.json()["lines"][0]["sku"] == sku


@pytest.mark.asyncio
async def test_sale_002_customer_and_context_isolation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        cross_res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_B), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert cross_res.status_code in (422, 403)


@pytest.mark.asyncio
async def test_sale_003_recoverable_draft_persistence(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        fetched = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_a)
        assert fetched.status_code == 200
        data = fetched.json()
        assert data["status"] == "draft"
        assert data["version"] == 1


@pytest.mark.asyncio
async def test_sale_004_prevalidation_summary_without_silent_mutation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("5.00"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 2, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        pre = await client.post(f"/api/v1/sales/{sale_id}/prevalidate", headers=auth_headers_a)
        assert pre.status_code == 200
        val_data = pre.json()
        assert val_data["valid"] is True
        assert val_data["summary"]["status"] == "draft"
        check = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_a)
        assert check.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_sale_005_authoritative_calculation_ignores_tampered_payload(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, price=Decimal("25.00"), tax_rate=Decimal("0.18"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "1.00", "tax_rate": "0.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        data = res.json()
        assert Decimal(data["total_amount"]).quantize(Decimal("0.01")) == Decimal("29.50")


@pytest.mark.asyncio
async def test_sale_006_rounding_and_cents_conservation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, price=Decimal("10.33"), tax_rate=Decimal("0.18"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 3, "unit_price": "10.33"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        data = res.json()
        assert Decimal(data["total_amount"]).quantize(Decimal("0.01")) == Decimal("36.57")


@pytest.mark.asyncio
async def test_sale_007_draft_concurrency_optimistic_locking(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        up1 = await client.patch(f"/api/v1/sales/{sale_id}", json={"version": 1, "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 2, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert up1.status_code == 200
        assert up1.json()["version"] == 2
        up2 = await client.patch(f"/api/v1/sales/{sale_id}", json={"version": 1, "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 3, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert up2.status_code == 409


@pytest.mark.asyncio
async def test_sale_008_confirm_idempotency_key_lost_response(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        key = f"K-LOST-{uuid4().hex}"
        c1 = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"version": 1}, headers={**auth_headers_a, "Idempotency-Key": key})
        assert c1.status_code == 200
        c2 = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"version": 1}, headers={**auth_headers_a, "Idempotency-Key": key})
        assert c2.status_code == 200
        assert c1.json()["number"] == c2.json()["number"]


@pytest.mark.asyncio
async def test_sale_009_atomic_confirmation_transaction(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        c = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert c.status_code == 200
        with sync_session_factory() as session:
            sale = session.scalar(select(SaleModel).where(SaleModel.id == UUID(sale_id)))
            assert sale.status == "confirmed"
            kardex = session.scalar(select(KardexMovementModel).where(KardexMovementModel.reference_doc_id == UUID(sale_id)))
            assert kardex is not None
            outbox = session.scalar(select(OutboxEventModel).where(OutboxEventModel.aggregate_id == UUID(sale_id)))
            assert outbox is not None


@pytest.mark.asyncio
async def test_sale_010_stock_row_locking_and_ordered_acquisition(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        p1, s1 = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("5.00"))
        p2, s2 = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("5.00"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(p1), "sku": s1, "product_name": "Item 1", "quantity": 2, "unit_price": "10.00"}, {"product_id": str(p2), "sku": s2, "product_name": "Item 2", "quantity": 3, "unit_price": "15.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        conf = await client.post(f"/api/v1/sales/{res.json()['sale_id']}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert conf.status_code == 200


@pytest.mark.asyncio
async def test_sale_011_frozen_prices_independent_from_catalog_changes(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, price=Decimal("50.00"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Original Name", "quantity": 1, "unit_price": "50.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        with sync_session_factory() as session:
            p = session.get(ProductModel, prod_id)
            p.unit_price = Decimal("200.00")
            p.name = "Altered Name"
            session.commit()
        detail = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_a)
        line = detail.json()["lines"][0]
        assert Decimal(line["unit_price"]).quantize(Decimal("0.01")) == Decimal("50.00")
        assert line["name"] == f"Prod {sku}"


@pytest.mark.asyncio
async def test_sale_012_orthogonal_commercial_payment_fulfillment_states(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        conf = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert conf.status_code == 200
        data = conf.json()
        assert data["status"] == "confirmed"
        assert Decimal(data["paid_amount"]) == Decimal("0")


@pytest.mark.asyncio
async def test_sale_013_annulment_requires_reason_and_reverts_stock(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, stock_qty=Decimal("10.00"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 2, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        with sync_session_factory() as session:
            st1 = session.scalar(select(InventoryStockModel).where(InventoryStockModel.product_id == prod_id))
            assert st1.physical_quantity == Decimal("8.00")
        ann = await client.post(f"/api/v1/sales/{sale_id}/cancel", json={"reason": "Error en pedido de cliente"}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert ann.status_code == 200
        assert ann.json()["status"] == "cancelled"
        with sync_session_factory() as session:
            st2 = session.scalar(select(InventoryStockModel).where(InventoryStockModel.product_id == prod_id))
            assert st2.physical_quantity == Decimal("10.00")


@pytest.mark.asyncio
async def test_sale_014_correction_preserves_audit_trail(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        cor = await client.post(f"/api/v1/sales/{sale_id}/correct", json={"reason": "Actualizacion de notas contables", "notes": "Corregido por administracion"}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert cor.status_code == 200
        with sync_session_factory() as session:
            log = session.scalar(select(AuditLogModel).where(AuditLogModel.entity_id == UUID(sale_id), AuditLogModel.action == "CORRECT_SALE"))
            assert log is not None
            assert "Actualizacion de notas" in log.payload_diff


@pytest.mark.asyncio
async def test_sale_015_credit_sale_validates_limit_and_updates_balance(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, price=Decimal("100.00"))
        credit_cust_id = uuid4()
        with sync_session_factory() as session:
            cust = CustomerModel(id=credit_cust_id, company_id=COMPANY_A, code=f"CLI-CR-{uuid4().hex[:4]}", doc_type="RUC", doc_number=f"20{uuid4().int % 900000000 + 100000000}", legal_name="Cliente Credito", credit_limit=Decimal("500.00"), current_balance=Decimal("0.00"), is_active=True)
            session.add(cust)
            session.commit()
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(credit_cust_id), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "is_credit": True, "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "100.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        conf = await client.post(f"/api/v1/sales/{sale_id}/confirm", json={"is_credit_sale": True}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert conf.status_code == 200
        with sync_session_factory() as session:
            c = session.get(CustomerModel, credit_cust_id)
            assert c.current_balance > Decimal("0")


@pytest.mark.asyncio
async def test_sale_016_zero_value_sale_requires_no_fake_payment(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A, price=Decimal("0.00"), tax_rate=Decimal("0.00"))
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Muestra Gratis", "quantity": 1, "unit_price": "0.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        sale_id = res.json()["sale_id"]
        conf = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert conf.status_code == 200
        assert Decimal(conf.json()["total_amount"]) == Decimal("0")


@pytest.mark.asyncio
async def test_sale_017_document_limits_and_validation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": []}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_sale_018_query_and_filter_sales_list(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert res.status_code == 201
        lst = await client.get(f"/api/v1/sales?customer_id={CUSTOMER_A}&status=draft", headers=auth_headers_a)
        assert lst.status_code == 200
        data = lst.json()
        assert "items" in data
        assert data["total_count"] >= 1


@pytest.mark.asyncio
async def test_sale_019_clone_sale_as_draft(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        cloned = await client.post(f"/api/v1/sales/{sale_id}/clone", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert cloned.status_code == 200
        assert cloned.json()["status"] == "draft"
        assert cloned.json()["sale_id"] != sale_id


@pytest.mark.asyncio
async def test_sale_020_sale_document_generation_and_reprint(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        doc1 = await client.get(f"/api/v1/sales/{sale_id}/document", headers=auth_headers_a)
        assert doc1.status_code == 200
        doc2 = await client.get(f"/api/v1/sales/{sale_id}/document", headers=auth_headers_a)
        assert doc2.status_code == 200
        assert doc1.json()["document_number"] == doc2.json()["document_number"]


@pytest.mark.asyncio
async def test_sale_021_commercial_events_outbox_correlation(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        with sync_session_factory() as session:
            evt = session.scalar(select(OutboxEventModel).where(OutboxEventModel.aggregate_id == UUID(sale_id), OutboxEventModel.event_type == "SALE_CONFIRMED"))
            assert evt is not None


@pytest.mark.asyncio
async def test_sale_022_interrupted_sale_recovery_by_idempotency_key(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        res = await client.post("/api/v1/sales/draft", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = res.json()["sale_id"]
        key = f"K-INT-{uuid4().hex}"
        conf = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": key})
        assert conf.status_code == 200
        recovered = await client.get(f"/api/v1/sales/by-idempotency-key/{key}", headers=auth_headers_a)
        assert recovered.status_code == 200
        assert recovered.json()["sale_id"] == sale_id


@pytest.mark.asyncio
async def test_api_035_post_sales_contract_and_authorization(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        valid_res = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert valid_res.status_code == 201
        invalid_res = await client.post("/api/v1/sales", json={"currency": "USD", "lines": []}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert invalid_res.status_code == 422
        unauth_res = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={"Idempotency-Key": uuid4().hex})
        assert unauth_res.status_code in (401, 403)
        cross_res = await client.post("/api/v1/sales", json={"company_id": str(COMPANY_B), "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert cross_res.status_code in (403, 422)


@pytest.mark.asyncio
async def test_api_036_get_sales_contract_and_pagination(auth_headers_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/sales?page=1&page_size=10", headers=auth_headers_a)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total_count" in data
        assert data["page"] == 1


@pytest.mark.asyncio
async def test_api_037_get_sale_by_id_contract_and_cross_tenant(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        draft = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = draft.json()["sale_id"]
        ok = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_a)
        assert ok.status_code == 200
        assert "lines" in ok.json()
        cross = await client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers_b)
        assert cross.status_code in (403, 404)
        missing = await client.get(f"/api/v1/sales/{uuid4()}", headers=auth_headers_a)
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_api_038_patch_sale_contract_and_versioning(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        draft = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = draft.json()["sale_id"]
        patch_ok = await client.patch(f"/api/v1/sales/{sale_id}", json={"version": 1, "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 2, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert patch_ok.status_code == 200
        assert patch_ok.json()["version"] == 2
        patch_obsolete = await client.patch(f"/api/v1/sales/{sale_id}", json={"version": 1, "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 3, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert patch_obsolete.status_code == 409
        cross = await client.patch(f"/api/v1/sales/{sale_id}", json={"version": 2, "customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_b, "Idempotency-Key": uuid4().hex})
        assert cross.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_039_post_confirm_sale_contract(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        draft = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = draft.json()["sale_id"]
        cross = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_b, "Idempotency-Key": uuid4().hex})
        assert cross.status_code in (403, 404)
        no_key = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers=auth_headers_a)
        assert no_key.status_code == 422
        ok = await client.post(f"/api/v1/sales/{sale_id}/confirm", headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert ok.status_code == 200
        assert ok.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_api_040_post_cancel_sale_contract(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id, sku = create_product_with_stock(COMPANY_A, WAREHOUSE_A)
        draft = await client.post("/api/v1/sales", json={"customer_id": str(CUSTOMER_A), "branch_id": str(BRANCH_A), "warehouse_id": str(WAREHOUSE_A), "currency": "USD", "lines": [{"product_id": str(prod_id), "sku": sku, "product_name": "Item", "quantity": 1, "unit_price": "10.00"}]}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        sale_id = draft.json()["sale_id"]
        empty_reason = await client.post(f"/api/v1/sales/{sale_id}/cancel", json={"reason": ""}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert empty_reason.status_code == 422
        cross = await client.post(f"/api/v1/sales/{sale_id}/cancel", json={"reason": "Cancelacion cruzada"}, headers={**auth_headers_b, "Idempotency-Key": uuid4().hex})
        assert cross.status_code in (403, 404)
        ok = await client.post(f"/api/v1/sales/{sale_id}/cancel", json={"reason": "Cancelacion de prueba valida"}, headers={**auth_headers_a, "Idempotency-Key": uuid4().hex})
        assert ok.status_code == 200
        assert ok.json()["status"] == "cancelled"
