import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, sync_engine, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    InventoryStockModel,
    KardexMovementModel,
    SaleModel,
    SaleLineModel
)
from salesia.modules.inventario.infrastructure_models import (
    Supplier,
    SupplyDocument,
    SupplyLine,
    LandedCostAdjustment,
    PurchaseInvoiceMatch,
    DeliveryShipment,
    DeliveryTrackingEvent,
    ProofOfDelivery,
    DeliveryIncident,
    StockRule
)
from salesia.modules.inventario.service import move_stock
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000101")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000109")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000102")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000192")
WAREHOUSE_A1 = UUID("00000000-0000-0000-0000-000000000104")
WAREHOUSE_B1 = UUID("00000000-0000-0000-0000-000000000194")
CUSTOMER_A = UUID("00000000-0000-0000-0000-000000000114")
CUSTOMER_B = UUID("00000000-0000-0000-0000-000000000195")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000103")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000107")
USER_WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000106")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000108")


@pytest.fixture(autouse=True, scope="module")
def setup_part13_data():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999000101", "Empresa A P13"), (COMPANY_B, "20999000109", "Empresa B P13")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        session.flush()
        for bid, cid, code, name in [(BRANCH_A, COMPANY_A, "SUC-P13-A", "Sucursal P13 A"), (BRANCH_B, COMPANY_B, "SUC-P13-B", "Sucursal P13 B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=name, timezone="America/Lima", is_active=True))
        session.flush()
        for wid, cid, bid, code, name in [
            (WAREHOUSE_A1, COMPANY_A, BRANCH_A, "WH-P13-A1", "Almacen Principal P13 A"),
            (WAREHOUSE_B1, COMPANY_B, BRANCH_B, "WH-P13-B1", "Almacen Rival P13 B")
        ]:
            wh = session.scalar(select(WarehouseModel).where(WarehouseModel.id == wid))
            if not wh:
                session.add(WarehouseModel(id=wid, company_id=cid, branch_id=bid, code=code, name=name, is_active=True))
        session.flush()
        for cust_id, cid, doc_num, name in [
            (CUSTOMER_A, COMPANY_A, "10000000001", "Cliente P13 A"),
            (CUSTOMER_B, COMPANY_B, "10000000009", "Cliente P13 B")
        ]:
            c = session.scalar(select(CustomerModel).where(CustomerModel.id == cust_id))
            if not c:
                session.add(CustomerModel(id=cust_id, company_id=cid, code=f"CLI-{doc_num}", doc_type="DNI", doc_number=doc_num, legal_name=name, credit_limit=Decimal("5000.00"), current_balance=Decimal("0.00"), is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_admin_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_p13_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_seller_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_p13_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_warehouse_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_WAREHOUSE_A, role="warehouse", email="warehouse_p13_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_admin_b():
    identity = create_durable_identity(company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_p13_b@rival.enterprise", password="valid_password")
    return identity["headers"]


def create_test_product(company_id=COMPANY_A, cost=Decimal("20.000000"), price=Decimal("50.000000")):
    pid = uuid4()
    with sync_session_factory() as session:
        prod = ProductModel(
            id=pid,
            company_id=company_id,
            sku=f"SKU-P13-{uuid4().hex[:8]}",
            name="Producto P13 Prueba",
            category="Pruebas",
            unit_of_measure="NIU",
            unit_cost=cost,
            unit_price=price,
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(prod)
        session.commit()
    return pid


def create_confirmed_sale(company_id, warehouse_id, product_id, quantity=Decimal("5.000000")):
    sid = uuid4()
    with sync_session_factory() as session:
        cust_id = CUSTOMER_A if company_id == COMPANY_A else CUSTOMER_B
        sale = SaleModel(
            id=sid,
            company_id=company_id,
            customer_id=cust_id,
            branch_id=BRANCH_A if company_id == COMPANY_A else BRANCH_B,
            warehouse_id=warehouse_id,
            series="F001",
            number=int(secrets.randbelow(899999) + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("250.00"),
            tax_amount=Decimal("45.00"),
            total_amount=Decimal("295.00"),
            paid_amount=Decimal("295.00"),
            version=1
        )
        session.add(sale)
        line = SaleLineModel(
            id=uuid4(),
            company_id=company_id,
            sale_id=sid,
            product_id=product_id,
            line_number=1,
            sku_snapshot="SKU-SNAPSHOT",
            name_snapshot="Producto Prueba",
            unit_of_measure_snapshot="NIU",
            quantity=quantity,
            unit_price_snapshot=Decimal("50.00"),
            unit_cost_snapshot=Decimal("20.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_snapshot=Decimal("0.1800"),
            subtotal_amount=Decimal("250.00"),
            tax_amount=Decimal("45.00"),
            total_amount=Decimal("295.00")
        )
        session.add(line)
        session.commit()
    return sid


@pytest.mark.asyncio
async def test_buy_001_supplier_card_and_financial_masking(auth_admin_a, auth_warehouse_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        create_res = await client.post(
            "/api/v1/suppliers",
            headers=auth_admin_a,
            json={
                "tax_id": tax_id,
                "legal_name": "Corporacion Proveedora Andina SAC",
                "contact_name": "Ing. Carlos Mendoza",
                "email": "carlos@andina.pe",
                "phone": "+51987654321",
                "payment_terms_days": 45,
                "currency": "PEN",
                "bank_name": "Banco de Credito del Peru",
                "bank_account": "191-12345678-0-99",
                "notes": "Proveedor preferencial de suministros"
            }
        )
        assert create_res.status_code == 201
        supplier_id = create_res.json()["id"]

        admin_res = await client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_admin_a)
        assert admin_res.status_code == 200
        admin_data = admin_res.json()
        assert admin_data["bank_name"] == "Banco de Credito del Peru"
        assert admin_data["bank_account"] == "191-12345678-0-99"

        wh_res = await client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_warehouse_a)
        assert wh_res.status_code == 200
        wh_data = wh_res.json()
        assert wh_data["legal_name"] == "Corporacion Proveedora Andina SAC"
        assert wh_data["contact_name"] == "Ing. Carlos Mendoza"
        assert wh_data["payment_terms_days"] == 45
        assert wh_data["bank_name"] is None
        assert wh_data["bank_account"] is None

        rival_res = await client.get(f"/api/v1/suppliers/{supplier_id}", headers=auth_admin_b)
        assert rival_res.status_code == 404


@pytest.mark.asyncio
async def test_buy_002_purchase_requisition_governance(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        req_res = await client.post(
            "/api/v1/purchases/requisitions",
            headers=auth_admin_a,
            json={
                "warehouse_id": str(WAREHOUSE_A1),
                "priority": "HIGH",
                "justification": "Inventario critico para campana Q4",
                "items": [{
                    "product_id": str(pid),
                    "quantity": "25.000000",
                    "unit_cost": "20.000000"
                }]
            }
        )
        assert req_res.status_code == 201
        req_data = req_res.json()
        assert req_data["status"] == "pending_approval"
        req_id = req_data["id"]

        list_po = await client.get("/api/v1/purchase-orders", headers=auth_admin_a)
        assert list_po.status_code == 200
        assert not any(str(pid) in str(po) for po in list_po.json()["items"])

        appr_res = await client.post(f"/api/v1/purchases/requisitions/{req_id}/approve", headers=auth_admin_a)
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_buy_003_purchase_order_versioning_and_approval_threshold(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup_res = await client.post(
            "/api/v1/suppliers",
            headers=auth_admin_a,
            json={"tax_id": tax_id, "legal_name": "Mayorista Tech SAC", "payment_terms_days": 30, "currency": "USD"}
        )
        supplier_id = sup_res.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("150.000000"))

        po_res = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "supplier_id": supplier_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "currency": "USD",
                "payment_terms_days": 30,
                "items": [{"product_id": str(pid), "quantity": "100.000000", "unit_cost": "150.000000"}]
            }
        )
        assert po_res.status_code == 201
        po_id = po_res.json()["id"]
        assert po_res.json()["version"] == 1
        assert po_res.json()["status"] == "submitted"

        appr_denied = await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_seller_a)
        assert appr_denied.status_code in (403, 401)

        appr_ok = await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)
        assert appr_ok.status_code == 200
        assert appr_ok.json()["status"] == "approved"
        assert appr_ok.json()["version"] == 2

        update_res = await client.put(
            f"/api/v1/purchase-orders/{po_id}",
            headers=auth_admin_a,
            json={
                "notes": "Cambio de plazo pactado a 60 dias",
                "payment_terms_days": 60,
                "items": [{"product_id": str(pid), "quantity": "120.000000", "unit_cost": "145.000000"}]
            }
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["version"] == 3
        assert updated["status"] == "submitted"


@pytest.mark.asyncio
async def test_buy_004_partial_goods_receipt_and_tolerances(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup_res = await client.post(
            "/api/v1/suppliers",
            headers=auth_admin_a,
            json={"tax_id": tax_id, "legal_name": "Distribuciones Quimicas SAC", "payment_terms_days": 15, "currency": "PEN"}
        )
        supplier_id = sup_res.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("10.000000"))

        po_res = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "supplier_id": supplier_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "currency": "PEN",
                "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "10.000000"}]
            }
        )
        po_id = po_res.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)

        rc1_res = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "purchase_order_id": po_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "inspection_status": "accepted",
                "tolerance_percentage": "0.05",
                "items": [{"product_id": str(pid), "quantity": "4.000000", "unit_cost": "10.000000"}]
            }
        )
        assert rc1_res.status_code == 201

        po_after1 = await client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_admin_a)
        assert po_after1.json()["status"] == "partially_received"
        assert Decimal(po_after1.json()["lines"][0]["processed_quantity"]) == Decimal("4.000000")

        exceed_res = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "purchase_order_id": po_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "inspection_status": "accepted",
                "tolerance_percentage": "0.05",
                "items": [{"product_id": str(pid), "quantity": "7.000000", "unit_cost": "10.000000"}]
            }
        )
        assert exceed_res.status_code == 409

        rc2_res = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "purchase_order_id": po_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "inspection_status": "accepted",
                "tolerance_percentage": "0.05",
                "items": [{"product_id": str(pid), "quantity": "6.000000", "unit_cost": "10.000000"}]
            }
        )
        assert rc2_res.status_code == 201
        po_after2 = await client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_admin_a)
        assert po_after2.json()["status"] == "received"


@pytest.mark.asyncio
async def test_buy_005_landed_cost_adjustments_and_valuation(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Importaciones Globales SAC"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("100.000000"))

        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "100.000000"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)

        rc = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "100.000000"}]}
        )
        rc_id = rc.json()["id"]

        cost_res = await client.post(
            f"/api/v1/goods-receipts/{rc_id}/landed-cost",
            headers=auth_admin_a,
            json={
                "charges": [
                    {"charge_type": "FREIGHT", "amount": "200.000000", "allocation_method": "VALUE", "notes": "Flete naviero"},
                    {"charge_type": "CUSTOMS", "amount": "100.000000", "allocation_method": "QUANTITY", "notes": "Arancel aduanero"}
                ]
            }
        )
        assert cost_res.status_code == 201
        data = cost_res.json()
        assert Decimal(data["total_charges_applied"]) == Decimal("300.000000")
        assert Decimal(data["lines"][0]["new_unit_cost"]) == Decimal("130.000000")

        with sync_session_factory() as session:
            kardex = session.scalars(select(KardexMovementModel).where(KardexMovementModel.reference_doc_type == "LANDED_COST", KardexMovementModel.reference_doc_id == UUID(rc_id))).all()
            assert len(kardex) > 0
            assert kardex[0].movement_type == "AJUSTE_VALORIZACION"
            assert kardex[0].quantity_delta == Decimal("0.000000")


@pytest.mark.asyncio
async def test_buy_006_purchase_return_restrictions_and_expected_credit(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Ferreteria Industrial SAC"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("50.000000"))

        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "5.000000", "unit_cost": "50.000000"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)
        rc = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "5.000000", "unit_cost": "50.000000"}]}
        )
        rc_id = rc.json()["id"]

        excess_fail = await client.post(
            "/api/v1/purchases/returns",
            headers=auth_admin_a,
            json={
                "goods_receipt_id": rc_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "items": [{"product_id": str(pid), "quantity": "8.000000"}],
                "reason": "Lote no conforme"
            }
        )
        assert excess_fail.status_code == 409

        ret_ok = await client.post(
            "/api/v1/purchases/returns",
            headers=auth_admin_a,
            json={
                "goods_receipt_id": rc_id,
                "warehouse_id": str(WAREHOUSE_A1),
                "items": [{"product_id": str(pid), "quantity": "2.000000"}],
                "reason": "Defecto de empaque verificado"
            }
        )
        assert ret_ok.status_code == 201
        details = json.loads(ret_ok.json().get("details_json", "{}"))
        assert Decimal(details["expected_credit_note_amount"]) == Decimal("100.000000")


@pytest.mark.asyncio
async def test_buy_007_three_way_matching_and_discrepancy_resolution(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Servicios Logisticos SAC"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("20.000000"))

        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "20.000000"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)
        await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "20.000000"}]}
        )

        match_discrepancy = await client.post(
            f"/api/v1/purchase-orders/{po_id}/three-way-match",
            headers=auth_admin_a,
            json={"supplier_invoice_number": "F001-000456", "invoice_amount": "250.000000", "notes": "Factura excede monto de recepcion"}
        )
        assert match_discrepancy.status_code == 201
        m_data = match_discrepancy.json()
        assert m_data["status"] == "UNDER_REVIEW"
        assert m_data["requires_review"] is True
        assert Decimal(m_data["discrepancy_amount"]) == Decimal("50.000000")

        resolve_res = await client.post(
            f"/api/v1/purchase-orders/{po_id}/three-way-match/resolve",
            headers=auth_admin_a,
            json={"resolution_notes": "Aprobado por ajuste comercial pactado con proveedor"}
        )
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "APPROVED_OVERRIDE"


@pytest.mark.asyncio
async def test_buy_008_supplier_performance_kpis(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Calzados Confort SAC"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("30.000000"))

        promised = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "delivery_date": promised, "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "30.000000"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)
        await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "10.000000", "unit_cost": "30.000000"}]}
        )

        perf_res = await client.get(f"/api/v1/suppliers/{sup_id}/performance", headers=auth_admin_a)
        assert perf_res.status_code == 200
        perf = perf_res.json()
        assert perf["sample_size"] == 1
        assert Decimal(perf["on_time_delivery_rate"]) == Decimal("100.00")
        assert Decimal(perf["fill_rate"]) == Decimal("100.00")
        assert len(perf["sample_records"]) == 1


@pytest.mark.asyncio
async def test_buy_009_replenishment_suggestions_labeled_needs_data(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        res = await client.get("/api/v1/purchases/replenishment-suggestions", headers=auth_admin_a)
        assert res.status_code == 200
        items = res.json()["suggestions"]
        target = next((item for item in items if item["product_id"] == str(pid)), None)
        assert target is not None
        assert target["data_insufficient"] is True
        assert target["status"] == "NEEDS_DATA"
        assert target["can_auto_approve"] is False


@pytest.mark.asyncio
async def test_buy_010_purchase_order_process_timeline(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Aceros del Centro SAC"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("100.000000"))

        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "20.000000", "unit_cost": "100.000000"}]}
        )
        po_id = po.json()["id"]

        time1 = await client.get(f"/api/v1/purchase-orders/{po_id}/process-timeline", headers=auth_admin_a)
        assert time1.status_code == 200
        t1 = time1.json()
        assert t1["next_recommended_step"] == "APPROVE_ORDER"
        assert Decimal(t1["line_balances"][0]["pending_quantity"]) == Decimal("20.000000")

        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)
        time2 = await client.get(f"/api/v1/purchase-orders/{po_id}/process-timeline", headers=auth_admin_a)
        assert time2.json()["next_recommended_step"] == "RECEIVE_GOODS"


@pytest.mark.asyncio
async def test_ship_001_address_snapshot_immutability(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("4.000000"))

        deliv_res = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Ana Maria Lopez",
                "delivery_address": "Av. Los Fresnos 450 Dpto 302, San Isidro",
                "recipient_phone": "+51999888777",
                "carrier": "DHL Express",
                "tracking_number": "DHL-SN-001",
                "tracking_url": "https://www.dhl.com/track/DHL-SN-001",
                "shipping_fee_charged": "20.00",
                "logistics_cost": "16.50",
                "estimated_delivery_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                "is_guaranteed": True
            }
        )
        assert deliv_res.status_code == 201
        deliv_id = deliv_res.json()["id"]

        check_res = await client.get(f"/api/v1/deliveries/{deliv_id}", headers=auth_admin_a)
        assert check_res.status_code == 200
        shipment = check_res.json()["shipment"]
        assert shipment["recipient_name"] == "Ana Maria Lopez"
        assert shipment["delivery_address"] == "Av. Los Fresnos 450 Dpto 302, San Isidro"


@pytest.mark.asyncio
async def test_ship_002_multi_delivery_preparation_and_balance(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("10.000000"))

        deliv1 = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Cliente Parcial",
                "delivery_address": "Calle 1",
                "carrier": "Transporte Propio",
                "tracking_number": "TR-01",
                "items": [{"product_id": str(pid), "quantity": "6.000000", "unit_cost": "50.00"}]
            }
        )
        assert deliv1.status_code == 201

        exceed = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Cliente Parcial",
                "delivery_address": "Calle 1",
                "carrier": "Transporte Propio",
                "tracking_number": "TR-02",
                "items": [{"product_id": str(pid), "quantity": "5.000000", "unit_cost": "50.00"}]
            }
        )
        assert exceed.status_code == 409

        deliv2 = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Cliente Parcial",
                "delivery_address": "Calle 1",
                "carrier": "Transporte Propio",
                "tracking_number": "TR-02",
                "items": [{"product_id": str(pid), "quantity": "4.000000", "unit_cost": "50.00"}]
            }
        )
        assert deliv2.status_code == 201


@pytest.mark.asyncio
async def test_ship_003_dispatch_idempotency_and_stock_exit(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("20.000000"), Decimal("20.00"), uuid4(), "STOCK_INICIAL")
            session.commit()
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("5.000000"))

        deliv = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Destino Salida",
                "delivery_address": "Jr. Puno 100",
                "carrier": "Olva Express",
                "tracking_number": "OLVA-12345",
                "items": [{"product_id": str(pid), "quantity": "5.000000", "unit_cost": "50.00"}]
            }
        )
        deliv_id = deliv.json()["id"]

        disp_res1 = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)
        assert disp_res1.status_code == 200
        assert disp_res1.json()["status"] == "dispatched"

        with sync_session_factory() as session:
            stk1 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk1 == Decimal("15.000000")

        disp_res2 = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)
        assert disp_res2.status_code == 200
        assert disp_res2.json()["status"] == "dispatched"

        with sync_session_factory() as session:
            stk2 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk2 == Decimal("15.000000")


@pytest.mark.asyncio
async def test_ship_004_carrier_url_security_validation(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("2.000000"))

        bad_url = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Destinatario",
                "delivery_address": "Lima",
                "carrier": "Falso Courier",
                "tracking_number": "EVIL-001",
                "tracking_url": "http://servidor-malicioso.com/phishing"
            }
        )
        assert bad_url.status_code == 422

        good_url = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Destinatario Seguro",
                "delivery_address": "Lima",
                "carrier": "FedEx",
                "tracking_number": "FDX-999",
                "tracking_url": "https://www.fedex.com/track/FDX-999"
            }
        )
        assert good_url.status_code == 201


@pytest.mark.asyncio
async def test_ship_005_tracking_events_anti_regression_and_deduplication(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Destino Tracking", "delivery_address": "Lima", "carrier": "DHL Express", "tracking_number": "DHL-TK-01"}
        )
        deliv_id = deliv.json()["id"]
        await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)

        fixed_time = "2026-10-10T12:00:00Z"
        ev1 = await client.post(
            f"/api/v1/deliveries/{deliv_id}/tracking-events",
            headers=auth_admin_a,
            json={"event_code": "IN_TRANSIT", "event_status": "in_transit", "description": "Paquete en ruta", "occurred_at": fixed_time}
        )
        assert ev1.status_code == 201
        assert ev1.json()["deduplicated"] is False
        assert ev1.json()["status"] == "in_transit"

        ev1_dup = await client.post(
            f"/api/v1/deliveries/{deliv_id}/tracking-events",
            headers=auth_admin_a,
            json={"event_code": "IN_TRANSIT", "event_status": "in_transit", "description": "Paquete en ruta", "occurred_at": fixed_time}
        )
        assert ev1_dup.status_code == 201
        assert ev1_dup.json()["deduplicated"] is True

        await client.post(
            f"/api/v1/deliveries/{deliv_id}/proof-of-delivery",
            headers=auth_admin_a,
            json={"received_by_name": "Receptor Final"}
        )
        curr = await client.get(f"/api/v1/deliveries/{deliv_id}", headers=auth_admin_a)
        assert curr.json()["status"] == "delivered"

        old_ev = await client.post(
            f"/api/v1/deliveries/{deliv_id}/tracking-events",
            headers=auth_admin_a,
            json={"event_code": "DELAYED_IN_HUB", "event_status": "in_transit", "description": "Evento antiguo retrasado"}
        )
        assert old_ev.status_code == 201
        after_old = await client.get(f"/api/v1/deliveries/{deliv_id}", headers=auth_admin_a)
        assert after_old.json()["status"] == "delivered"


@pytest.mark.asyncio
async def test_ship_006_proof_of_delivery_retention_and_permission(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Juan Perez", "delivery_address": "Lima", "carrier": "Transporte Propio", "tracking_number": "POD-01"}
        )
        deliv_id = deliv.json()["id"]
        await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)

        pod_res = await client.post(
            f"/api/v1/deliveries/{deliv_id}/proof-of-delivery",
            headers=auth_admin_a,
            json={
                "received_by_name": "Juan Perez",
                "received_by_id_doc": "DNI 44556677",
                "signature_data": "HASH_FIRMA_CONFORME_SHA256",
                "notes": "Entregado en puerta principal conforme"
            }
        )
        assert pod_res.status_code == 201

        view_ok = await client.get(f"/api/v1/deliveries/{deliv_id}/proof-of-delivery", headers=auth_admin_a)
        assert view_ok.status_code == 200
        assert view_ok.json()["received_by_name"] == "Juan Perez"
        assert view_ok.json()["received_by_id_doc"] == "DNI 44556677"

        view_rival = await client.get(f"/api/v1/deliveries/{deliv_id}/proof-of-delivery", headers=auth_admin_b)
        assert view_rival.status_code == 404


@pytest.mark.asyncio
async def test_ship_007_incident_recording_does_not_replenish_stock(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("10.000000"), Decimal("20.00"), uuid4(), "STOCK_INICIAL")
            session.commit()
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("2.000000"))

        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Destino Incidencia", "delivery_address": "Lima", "carrier": "DHL Express", "tracking_number": "INC-01"}
        )
        deliv_id = deliv.json()["id"]
        await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)

        inc_res = await client.post(
            f"/api/v1/deliveries/{deliv_id}/incidents",
            headers=auth_admin_a,
            json={"incident_type": "FAILED_ATTEMPT", "description": "Destinatario no responde citofono"}
        )
        assert inc_res.status_code == 201

        check = await client.get(f"/api/v1/deliveries/{deliv_id}", headers=auth_admin_a)
        assert check.json()["status"] == "failed_attempt"

        with sync_session_factory() as session:
            stk = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk == Decimal("8.000000")


@pytest.mark.asyncio
async def test_ship_008_cancellation_and_in_transit_interception(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("10.000000"), Decimal("20.00"), uuid4(), "STOCK_INICIAL")
            session.commit()
        sid1 = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        d1 = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid1), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Cancelable", "delivery_address": "Lima", "carrier": "Transporte Propio", "tracking_number": "CAN-01"}
        )
        d1_id = d1.json()["id"]

        cancel_ok = await client.post(f"/api/v1/deliveries/{d1_id}/cancel", headers=auth_admin_a)
        assert cancel_ok.status_code == 200
        assert cancel_ok.json()["status"] == "cancelled"

        sid2 = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        d2 = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid2), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Interceptable", "delivery_address": "Lima", "carrier": "Transporte Propio", "tracking_number": "INT-01"}
        )
        d2_id = d2.json()["id"]
        await client.post(f"/api/v1/deliveries/{d2_id}/dispatch", headers=auth_admin_a)

        cancel_bad = await client.post(f"/api/v1/deliveries/{d2_id}/cancel", headers=auth_admin_a)
        assert cancel_bad.status_code == 409

        intercept_ok = await client.post(
            f"/api/v1/deliveries/{d2_id}/intercept",
            headers=auth_admin_a,
            json={"reason": "Solicitud de devolucion comercial en transito"}
        )
        assert intercept_ok.status_code == 200
        assert intercept_ok.json()["status"] == "intercept_requested"


@pytest.mark.asyncio
async def test_ship_009_cost_separation_and_promise_levels(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        est_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Distincion Costos",
                "delivery_address": "Lima",
                "carrier": "DHL Express",
                "tracking_number": "DHL-COST-01",
                "shipping_fee_charged": "25.000000",
                "logistics_cost": "18.500000",
                "estimated_delivery_date": est_date,
                "is_guaranteed": False
            }
        )
        assert deliv.status_code == 201
        res = deliv.json()["shipment"]
        assert Decimal(res["shipping_fee_charged"]) == Decimal("25.000000")
        assert Decimal(res["logistics_cost"]) == Decimal("18.500000")
        assert res["is_guaranteed"] is False


@pytest.mark.asyncio
async def test_ship_010_operational_monitoring_and_delayed_badges(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("1.000000"))
        past_date = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Entrega Retrasada",
                "delivery_address": "Lima",
                "carrier": "Olva Express",
                "tracking_number": "OLVA-DELAY-01",
                "estimated_delivery_date": past_date
            }
        )
        deliv_id = deliv.json()["id"]

        list_delayed = await client.get("/api/v1/deliveries?delayed_only=true", headers=auth_admin_a)
        assert list_delayed.status_code == 200
        items = list_delayed.json()["items"]
        target = next((i for i in items if i["id"] == deliv_id), None)
        assert target is not None
        assert target["is_delayed"] is True
        assert target["delayed_days"] >= 3
        assert target["next_action"] == "DISPATCH"


@pytest.mark.asyncio
async def test_api_056_get_suppliers(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/suppliers?limit=10", headers=auth_admin_a)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "count" in data

        res_b = await client.get("/api/v1/suppliers?limit=10", headers=auth_admin_b)
        assert res_b.status_code == 200
        for item in res_b.json()["items"]:
            assert item["id"] not in [i["id"] for i in data["items"]]


@pytest.mark.asyncio
async def test_api_057_post_purchase_orders(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "API 057 Proveedor"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A)

        idem = str(uuid4())
        res1 = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert res1.status_code == 201

        res2 = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert res2.status_code == 201
        assert res2.json()["id"] == res1.json()["id"]

        cross = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_b, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_B1), "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert cross.status_code in (404, 422)


@pytest.mark.asyncio
async def test_api_058_post_goods_receipts(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "API 058 Proveedor"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A)
        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)

        cross = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_b, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_B1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert cross.status_code in (403, 404, 409)

        idem = str(uuid4())
        ok1 = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert ok1.status_code == 201

        ok2 = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "20.00"}]}
        )
        assert ok2.status_code == 201
        assert ok2.json()["id"] == ok1.json()["id"]


@pytest.mark.asyncio
async def test_api_059_post_deliveries(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("3.00"))

        cross = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_b,
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_B1), "recipient_name": "Rival", "delivery_address": "Lima", "carrier": "DHL Express", "tracking_number": "TR-X"}
        )
        assert cross.status_code in (404, 409)

        idem = str(uuid4())
        ok1 = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Cliente API 059", "delivery_address": "Lima", "carrier": "DHL Express", "tracking_number": "TR-059"}
        )
        assert ok1.status_code == 201

        ok2 = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": idem},
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Cliente API 059", "delivery_address": "Lima", "carrier": "DHL Express", "tracking_number": "TR-059"}
        )
        assert ok2.status_code == 201
        assert ok2.json()["id"] == ok1.json()["id"]


@pytest.mark.asyncio
async def test_api_060_post_deliveries_dispatch(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("10.00"), Decimal("20.00"), uuid4(), "STOCK_INICIAL")
            session.commit()
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("2.00"))
        deliv = await client.post(
            "/api/v1/deliveries",
            headers=auth_admin_a,
            json={"sale_id": str(sid), "warehouse_id": str(WAREHOUSE_A1), "recipient_name": "Cliente API 060", "delivery_address": "Lima", "carrier": "Transporte Propio", "tracking_number": "TR-060"}
        )
        deliv_id = deliv.json()["id"]

        cross = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_b)
        assert cross.status_code in (403, 404)

        idem = str(uuid4())
        disp1 = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers={**auth_admin_a, "Idempotency-Key": idem})
        assert disp1.status_code == 200
        assert disp1.json()["status"] == "dispatched"

        disp2 = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers={**auth_admin_a, "Idempotency-Key": idem})
        assert disp2.status_code == 200
        assert disp2.json()["status"] == "dispatched"


@pytest.mark.asyncio
async def test_fal021_purchasing_end_to_end(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tax_id = f"20{secrets.token_hex(4)}"
        sup = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": tax_id, "legal_name": "Proveedor FAL021 Integral SAC", "payment_terms_days": 30, "currency": "USD"})
        sup_id = sup.json()["id"]
        pid = create_test_product(company_id=COMPANY_A, cost=Decimal("40.00"))

        req = await client.post(
            "/api/v1/purchases/requisitions",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "priority": "MEDIUM", "justification": "Reposicion programada", "items": [{"product_id": str(pid), "quantity": "10.00", "unit_cost": "40.00"}]}
        )
        assert req.status_code == 201
        req_id = req.json()["id"]
        await client.post(f"/api/v1/purchases/requisitions/{req_id}/approve", headers=auth_admin_a)

        po = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"supplier_id": sup_id, "warehouse_id": str(WAREHOUSE_A1), "currency": "USD", "items": [{"product_id": str(pid), "quantity": "10.00", "unit_cost": "40.00"}]}
        )
        po_id = po.json()["id"]
        await client.post(f"/api/v1/purchase-orders/{po_id}/approve", headers=auth_admin_a)

        rc = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "inspection_status": "accepted", "items": [{"product_id": str(pid), "quantity": "10.00", "unit_cost": "40.00"}]}
        )
        rc_id = rc.json()["id"]

        landed = await client.post(
            f"/api/v1/goods-receipts/{rc_id}/landed-cost",
            headers=auth_admin_a,
            json={"charges": [{"charge_type": "FREIGHT", "amount": "50.00", "allocation_method": "VALUE", "notes": "Flete local"}]}
        )
        assert landed.status_code == 201

        ret = await client.post(
            "/api/v1/purchases/returns",
            headers=auth_admin_a,
            json={"goods_receipt_id": rc_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "1.00"}], "reason": "Falla de acabado"}
        )
        assert ret.status_code == 201

        match = await client.post(
            f"/api/v1/purchase-orders/{po_id}/three-way-match",
            headers=auth_admin_a,
            json={"supplier_invoice_number": "FAL-021-INV", "invoice_amount": "400.00", "notes": "Factura proveedor conforme"}
        )
        assert match.status_code == 201
        assert match.json()["status"] == "MATCHED"


@pytest.mark.asyncio
async def test_fal023_shipping_end_to_end(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_test_product(company_id=COMPANY_A)
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("10.00"), Decimal("25.00"), uuid4(), "STOCK_INICIAL")
            session.commit()
        sid = create_confirmed_sale(COMPANY_A, WAREHOUSE_A1, pid, quantity=Decimal("4.00"))

        deliv = await client.post(
            "/api/v1/deliveries",
            headers={**auth_admin_a, "Idempotency-Key": str(uuid4())},
            json={
                "sale_id": str(sid),
                "warehouse_id": str(WAREHOUSE_A1),
                "recipient_name": "Corporacion Cliente SAC",
                "delivery_address": "Av. Republica de Panama 3055, San Isidro",
                "recipient_phone": "+51988776655",
                "carrier": "DHL Express",
                "tracking_number": "DHL-FAL023-999",
                "tracking_url": "https://www.dhl.com/track/DHL-FAL023-999",
                "shipping_fee_charged": "30.00",
                "logistics_cost": "22.00",
                "estimated_delivery_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "is_guaranteed": True
            }
        )
        assert deliv.status_code == 201
        deliv_id = deliv.json()["id"]

        disp = await client.post(f"/api/v1/deliveries/{deliv_id}/dispatch", headers=auth_admin_a)
        assert disp.status_code == 200
        assert disp.json()["status"] == "dispatched"

        tr = await client.post(
            f"/api/v1/deliveries/{deliv_id}/tracking-events",
            headers=auth_admin_a,
            json={"event_code": "DISPATCHED_HUB", "event_status": "in_transit", "description": "Salida de centro de distribucion"}
        )
        assert tr.status_code == 201

        inc = await client.post(
            f"/api/v1/deliveries/{deliv_id}/incidents",
            headers=auth_admin_a,
            json={"incident_type": "RESCHEDULE", "description": "Cliente solicita entrega en horario de la tarde"}
        )
        assert inc.status_code == 201

        pod = await client.post(
            f"/api/v1/deliveries/{deliv_id}/proof-of-delivery",
            headers=auth_admin_a,
            json={"received_by_name": "Carlos Gomez", "received_by_id_doc": "DNI 10203040", "notes": "Recepcion exitosa en oficina de recepcion"}
        )
        assert pod.status_code == 201
        assert pod.json()["status"] == "delivered"

        summary = await client.get(f"/api/v1/deliveries/{deliv_id}", headers=auth_admin_a)
        assert summary.status_code == 200
        assert summary.json()["status"] == "delivered"
        assert summary.json()["has_proof_of_delivery"] is True
        assert len(summary.json()["tracking_events"]) > 0
        assert len(summary.json()["incidents"]) > 0
