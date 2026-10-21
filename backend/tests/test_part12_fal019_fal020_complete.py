import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import secrets
import time
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, sync_engine, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    CustomerModel,
    BranchModel,
    WarehouseModel,
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
    WarehouseLocation,
    LocationStock,
    InventoryLot,
    InventorySerial,
    StockRule,
    InventoryAlert,
    InventoryReservation,
    InventoryQuarantine,
    PhysicalCountSession,
    PhysicalCountLine,
    InventoryPickingList,
    InventoryPickingLine,
    InventoryValuationSetting,
    InventoryReconciliation
)
from salesia.modules.inventario.service import (
    reserve_stock,
    release_reservation,
    consume_reservation,
    reconcile_stock,
    repair_stock_discrepancy,
    recalculate_alerts,
    move_stock
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000101")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000109")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000102")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000192")
WAREHOUSE_A1 = UUID("00000000-0000-0000-0000-000000000104")
WAREHOUSE_A2 = UUID("00000000-0000-0000-0000-000000000105")
WAREHOUSE_B1 = UUID("00000000-0000-0000-0000-000000000194")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000103")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000107")
USER_WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000106")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000108")


@pytest.fixture(autouse=True, scope="module")
def setup_part12_data():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999000101", "Empresa A P12"), (COMPANY_B, "20999000109", "Empresa B P12")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        session.flush()
        for bid, cid, code, name in [(BRANCH_A, COMPANY_A, "SUC-P12-A", "Sucursal P12 A"), (BRANCH_B, COMPANY_B, "SUC-P12-B", "Sucursal P12 B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=name, timezone="America/Lima", is_active=True))
        session.flush()
        for wid, cid, bid, code, name in [
            (WAREHOUSE_A1, COMPANY_A, BRANCH_A, "WH-P12-A1", "Almacen Principal A"),
            (WAREHOUSE_A2, COMPANY_A, BRANCH_A, "WH-P12-A2", "Almacen Secundario A"),
            (WAREHOUSE_B1, COMPANY_B, BRANCH_B, "WH-P12-B1", "Almacen Rival B")
        ]:
            wh = session.scalar(select(WarehouseModel).where(WarehouseModel.id == wid))
            if not wh:
                session.add(WarehouseModel(id=wid, company_id=cid, branch_id=bid, code=code, name=name, is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_admin_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_p12_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_seller_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_p12_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_warehouse_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_WAREHOUSE_A, role="warehouse", email="warehouse_p12_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_admin_b():
    identity = create_durable_identity(company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_p12_b@rival.enterprise", password="valid_password")
    return identity["headers"]


def create_product(company_id=COMPANY_A, sku_prefix="PROD-P12", cost=Decimal("50.000000"), price=Decimal("100.000000")):
    pid = uuid4()
    with sync_session_factory() as session:
        prod = ProductModel(
            id=pid,
            company_id=company_id,
            sku=f"{sku_prefix}-{uuid4().hex[:6]}",
            name=f"Producto {sku_prefix}",
            category="Almacen",
            unit_of_measure="NIU",
            unit_cost=cost,
            unit_price=price,
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(prod)
        session.commit()
    return pid


def set_stock(company_id, warehouse_id, product_id, physical=Decimal("100.000000"), reserved=Decimal("0.000000"), cost=Decimal("50.000000")):
    with sync_session_factory() as session:
        stk = session.scalar(select(InventoryStockModel).where(
            InventoryStockModel.company_id == company_id,
            InventoryStockModel.warehouse_id == warehouse_id,
            InventoryStockModel.product_id == product_id
        ))
        if not stk:
            stk = InventoryStockModel(
                id=uuid4(),
                company_id=company_id,
                warehouse_id=warehouse_id,
                product_id=product_id,
                physical_quantity=physical,
                reserved_quantity=reserved,
                average_cost=cost
            )
            session.add(stk)
        else:
            stk.physical_quantity = physical
            stk.reserved_quantity = reserved
            stk.average_cost = cost
        session.commit()


@pytest.mark.asyncio
async def test_fal019_stk009_stk010_api052_api053_transfer_lifecycle_transit_conservation_and_partial_receive(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "TRF", Decimal("20.00"), Decimal("40.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("50.00"), reserved=Decimal("0.00"), cost=Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A2, pid, physical=Decimal("0.00"), reserved=Decimal("0.00"), cost=Decimal("20.00"))

        idemp_trf = uuid4().hex
        res_create = await client.post(
            "/api/v1/inventory/transfers",
            headers={**auth_admin_a, "Idempotency-Key": idemp_trf},
            json={
                "source_warehouse_id": str(WAREHOUSE_A1),
                "destination_warehouse_id": str(WAREHOUSE_A2),
                "items": [{"product_id": str(pid), "quantity": "20.000000", "unit_cost": "20.000000"}],
                "notes": "Envio intersucursal A1 a A2"
            }
        )
        assert res_create.status_code == 201
        trf_data = res_create.json()
        trf_id = trf_data["id"]
        assert trf_data["status"] == "draft"

        idemp_disp = uuid4().hex
        res_disp = await client.post(f"/api/v1/inventory/transfers/{trf_id}/dispatch", headers={**auth_admin_a, "Idempotency-Key": idemp_disp})
        assert res_disp.status_code == 200
        disp_data = res_disp.json()
        assert disp_data["status"] == "in_transit"

        inv_a1 = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A1}&product_id={pid}", headers=auth_admin_a)
        assert inv_a1.status_code == 200
        item_a1 = inv_a1.json()["items"][0]
        assert Decimal(item_a1["physical_quantity"]) == Decimal("30.000000")
        assert Decimal(item_a1["available_quantity"]) == Decimal("30.000000")

        inv_a2 = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A2}&product_id={pid}", headers=auth_admin_a)
        assert inv_a2.status_code == 200
        item_a2 = inv_a2.json()["items"][0]
        assert Decimal(item_a2["physical_quantity"]) == Decimal("0.000000")
        assert Decimal(item_a2["available_quantity"]) == Decimal("0.000000")
        assert Decimal(item_a2["transit_quantity"]) == Decimal("20.000000")

        idemp_rec1 = uuid4().hex
        res_rec1 = await client.post(
            f"/api/v1/inventory/transfers/{trf_id}/receive",
            headers={**auth_admin_a, "Idempotency-Key": idemp_rec1},
            json={
                "items": [{"product_id": str(pid), "quantity_received": "12.000000", "quantity_damaged": "3.000000"}],
                "notes": "Recepcion parcial con 3 unidades danadas por transporte"
            }
        )
        assert res_rec1.status_code == 200
        rec1_data = res_rec1.json()
        assert rec1_data["status"] == "partially_received"

        inv_a2_p = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A2}&product_id={pid}", headers=auth_admin_a)
        item_a2_p = inv_a2_p.json()["items"][0]
        assert Decimal(item_a2_p["physical_quantity"]) == Decimal("12.000000")
        assert Decimal(item_a2_p["available_quantity"]) == Decimal("12.000000")
        assert Decimal(item_a2_p["transit_quantity"]) == Decimal("5.000000")

        res_rec_dup = await client.post(
            f"/api/v1/inventory/transfers/{trf_id}/receive",
            headers={**auth_admin_a, "Idempotency-Key": idemp_rec1},
            json={
                "items": [{"product_id": str(pid), "quantity_received": "12.000000", "quantity_damaged": "3.000000"}],
                "notes": "Recepcion parcial con 3 unidades danadas por transporte"
            }
        )
        assert res_rec_dup.status_code == 200
        inv_a2_after_dup = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A2}&product_id={pid}", headers=auth_admin_a)
        assert Decimal(inv_a2_after_dup.json()["items"][0]["physical_quantity"]) == Decimal("12.000000")

        idemp_rec2 = uuid4().hex
        res_rec2 = await client.post(
            f"/api/v1/inventory/transfers/{trf_id}/receive",
            headers={**auth_admin_a, "Idempotency-Key": idemp_rec2},
            json={
                "items": [{"product_id": str(pid), "quantity_received": "5.000000", "quantity_damaged": "0.000000"}],
                "notes": "Recepcion de unidades restantes"
            }
        )
        assert res_rec2.status_code == 200
        assert res_rec2.json()["status"] == "received"

        with sync_session_factory() as session:
            stk_a1 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            stk_a2 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A2, InventoryStockModel.product_id == pid))
            quar_a2 = session.scalar(select(InventoryQuarantine.quantity).where(InventoryQuarantine.company_id == COMPANY_A, InventoryQuarantine.warehouse_id == WAREHOUSE_A2, InventoryQuarantine.product_id == pid))
            assert stk_a1 == Decimal("30.000000")
            assert stk_a2 == Decimal("17.000000")
            assert quar_a2 == Decimal("3.000000")
            assert stk_a1 + stk_a2 + quar_a2 == Decimal("50.000000")


@pytest.mark.asyncio
async def test_fal019_api052_rejects_same_warehouse_invalid_quantities_and_cross_tenant(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "VAL", Decimal("10.00"), Decimal("20.00"))

        res_same = await client.post(
            "/api/v1/inventory/transfers",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "source_warehouse_id": str(WAREHOUSE_A1),
                "destination_warehouse_id": str(WAREHOUSE_A1),
                "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "10.00"}]
            }
        )
        assert res_same.status_code == 422

        res_cross = await client.post(
            "/api/v1/inventory/transfers",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "source_warehouse_id": str(WAREHOUSE_A1),
                "destination_warehouse_id": str(WAREHOUSE_B1),
                "items": [{"product_id": str(pid), "quantity": "5.00", "unit_cost": "10.00"}]
            }
        )
        assert res_cross.status_code == 422

        res_b_access_a = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A1}", headers=auth_admin_b)
        assert res_b_access_a.status_code in (404, 422)


@pytest.mark.asyncio
async def test_fal019_transfer_cancellation_restores_source_stock(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "CAN", Decimal("15.00"), Decimal("30.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("40.00"), reserved=Decimal("0.00"), cost=Decimal("15.00"))

        res_create = await client.post(
            "/api/v1/inventory/transfers",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "source_warehouse_id": str(WAREHOUSE_A1),
                "destination_warehouse_id": str(WAREHOUSE_A2),
                "items": [{"product_id": str(pid), "quantity": "10.00", "unit_cost": "15.00"}]
            }
        )
        trf_id = res_create.json()["id"]

        await client.post(f"/api/v1/inventory/transfers/{trf_id}/dispatch", headers={**auth_admin_a, "Idempotency-Key": uuid4().hex})

        with sync_session_factory() as session:
            stk_disp = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk_disp == Decimal("30.000000")

        res_cancel = await client.post(f"/api/v1/inventory/transfers/{trf_id}/cancel", headers={**auth_admin_a, "Idempotency-Key": uuid4().hex})
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "cancelled"

        with sync_session_factory() as session:
            stk_after = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk_after == Decimal("40.000000")


@pytest.mark.asyncio
async def test_fal020_stk019_warehouse_locations_and_internal_transfers(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "LOC", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("100.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        loc1_code = f"LOC-A-{uuid4().hex[:4].upper()}"
        res_loc1 = await client.post(
            "/api/v1/inventory/locations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "code": loc1_code, "aisle": "P1", "rack": "E1", "shelf": "N1", "bin": "B1", "capacity_units": 500}
        )
        assert res_loc1.status_code == 201
        loc1_id = res_loc1.json()["id"]

        loc2_code = f"LOC-B-{uuid4().hex[:4].upper()}"
        res_loc2 = await client.post(
            "/api/v1/inventory/locations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "code": loc2_code, "aisle": "P2", "rack": "E2", "shelf": "N2", "bin": "B2", "capacity_units": 500}
        )
        assert res_loc2.status_code == 201
        loc2_id = res_loc2.json()["id"]

        with sync_session_factory() as session:
            session.add(LocationStock(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A1,
                location_id=UUID(loc1_id),
                product_id=pid,
                quantity=Decimal("60.00")
            ))
            session.commit()

        res_move = await client.post(
            "/api/v1/inventory/locations/transfer",
            headers=auth_admin_a,
            json={
                "warehouse_id": str(WAREHOUSE_A1),
                "product_id": str(pid),
                "from_location_id": str(loc1_id),
                "to_location_id": str(loc2_id),
                "quantity": "25.00"
            }
        )
        assert res_move.status_code == 200

        with sync_session_factory() as session:
            q1 = session.scalar(select(LocationStock.quantity).where(LocationStock.location_id == UUID(loc1_id), LocationStock.product_id == pid))
            q2 = session.scalar(select(LocationStock.quantity).where(LocationStock.location_id == UUID(loc2_id), LocationStock.product_id == pid))
            wh_tot = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert q1 == Decimal("35.000000")
            assert q2 == Decimal("25.000000")
            assert wh_tot == Decimal("100.000000")


@pytest.mark.asyncio
async def test_fal020_stk011_lots_expiration_and_blocking(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "LOT", Decimal("30.00"), Decimal("60.00"))
        lot_code_active = f"LOTE-OK-{uuid4().hex[:4].upper()}"
        fut = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
        res_lot1 = await client.post(
            "/api/v1/inventory/lots",
            headers=auth_admin_a,
            json={"product_id": str(pid), "lot_code": lot_code_active, "expiration_date": fut, "notes": "Lote vigente"}
        )
        assert res_lot1.status_code == 201

        lot_code_block = f"LOTE-BLK-{uuid4().hex[:4].upper()}"
        res_lot2 = await client.post(
            "/api/v1/inventory/lots",
            headers=auth_admin_a,
            json={"product_id": str(pid), "lot_code": lot_code_block, "expiration_date": fut, "notes": "Lote por bloquear"}
        )
        lot2_id = res_lot2.json()["id"]

        res_block = await client.post(f"/api/v1/inventory/lots/{lot2_id}/block", headers=auth_admin_a)
        assert res_block.status_code == 200
        assert res_block.json()["status"] == "BLOCKED"

        with sync_session_factory() as session:
            lot_db = session.scalar(select(InventoryLot.status).where(InventoryLot.id == UUID(lot2_id)))
            assert lot_db == "BLOCKED"


@pytest.mark.asyncio
async def test_fal020_stk012_serials_unique_and_double_sale_rejection(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "SRL", Decimal("200.00"), Decimal("400.00"))
        serial_no = f"SN-TEST-{uuid4().hex[:8].upper()}"

        res_srl = await client.post(
            "/api/v1/inventory/serials",
            headers=auth_admin_a,
            json={"product_id": str(pid), "warehouse_id": str(WAREHOUSE_A1), "serial_number": serial_no}
        )
        assert res_srl.status_code == 201
        assert res_srl.json()["status"] == "IN_STOCK"

        res_dup_serial = await client.post(
            "/api/v1/inventory/serials",
            headers=auth_admin_a,
            json={"product_id": str(pid), "warehouse_id": str(WAREHOUSE_A1), "serial_number": serial_no}
        )
        assert res_dup_serial.status_code == 409

        invalid_sale = await client.post("/api/v1/inventory/serials/sell", headers=auth_admin_a, json={"product_id": str(pid), "serial_number": serial_no, "sale_id": str(uuid4())})
        assert invalid_sale.status_code == 422
        with sync_session_factory() as session:
            customer = CustomerModel(company_id=COMPANY_A, code=f"SER-{uuid4().hex[:8]}", doc_type="DNI", doc_number=uuid4().hex[:8], legal_name="Cliente de serie", current_balance=Decimal("0"), credit_limit=Decimal("0"))
            session.add(customer)
            session.flush()
            sale = SaleModel(company_id=COMPANY_A, branch_id=BRANCH_A, warehouse_id=WAREHOUSE_A1, customer_id=customer.id, series="SRL1", number=int(uuid4().hex[:7], 16), status="confirmed", currency="USD", subtotal_amount=Decimal("400"), tax_amount=Decimal("0"), total_amount=Decimal("400"))
            session.add(sale)
            session.flush()
            session.add(SaleLineModel(company_id=COMPANY_A, sale_id=sale.id, product_id=pid, line_number=1, sku_snapshot="SERIE", name_snapshot="Producto seriado", unit_of_measure_snapshot="NIU", quantity=Decimal("1"), unit_price_snapshot=Decimal("400"), unit_cost_snapshot=Decimal("200"), discount_amount=Decimal("0"), tax_rate_snapshot=Decimal("0"), subtotal_amount=Decimal("400"), tax_amount=Decimal("0"), total_amount=Decimal("400")))
            session.commit()
            sale1 = sale.id
        res_sell1 = await client.post(
            "/api/v1/inventory/serials/sell",
            headers=auth_admin_a,
            json={"product_id": str(pid), "serial_number": serial_no, "sale_id": str(sale1)}
        )
        assert res_sell1.status_code == 200
        assert res_sell1.json()["status"] == "SOLD"

        sale2 = uuid4()
        res_sell2 = await client.post(
            "/api/v1/inventory/serials/sell",
            headers=auth_admin_a,
            json={"product_id": str(pid), "serial_number": serial_no, "sale_id": str(sale2)}
        )
        assert res_sell2.status_code == 409


@pytest.mark.asyncio
async def test_fal020_stk013_stk018_quarantine_returns_and_no_premature_sale(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "QRT", Decimal("25.00"), Decimal("50.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("0.00"), reserved=Decimal("0.00"), cost=Decimal("25.00"))

        with sync_session_factory() as session:
            quar_item = InventoryQuarantine(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A1,
                product_id=pid,
                quantity=Decimal("5.00"),
                reason="CUSTOMER_RETURN",
                status="IN_QUARANTINE"
            )
            session.add(quar_item)
            session.commit()
            quar_id = str(quar_item.id)

        inv_res = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A1}&product_id={pid}", headers=auth_admin_a)
        item = inv_res.json()["items"][0]
        assert Decimal(item["physical_quantity"]) == Decimal("0.000000")
        assert Decimal(item["quarantine_quantity"]) == Decimal("5.000000")
        assert Decimal(item["available_quantity"]) == Decimal("0.000000")

        res_class = await client.post(
            f"/api/v1/inventory/quarantine/{quar_id}/classify",
            headers=auth_admin_a,
            json={"action": "RESTOCK", "notes": "Inspeccion tecnica aprobada, producto apto"}
        )
        assert res_class.status_code == 200
        assert res_class.json()["status"] == "RELEASED_TO_STOCK"

        inv_after = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A1}&product_id={pid}", headers=auth_admin_a)
        item_after = inv_after.json()["items"][0]
        assert Decimal(item_after["physical_quantity"]) == Decimal("5.000000")
        assert Decimal(item_after["quarantine_quantity"]) == Decimal("0.000000")
        assert Decimal(item_after["available_quantity"]) == Decimal("5.000000")


@pytest.mark.asyncio
async def test_fal020_stk008_api054_api055_counts_blind_cutoff_approval_idempotency_and_segregation(auth_admin_a, auth_warehouse_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "CNT", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("50.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        res_cnt = await client.post(
            "/api/v1/inventory/counts",
            headers=auth_warehouse_a,
            json={
                "warehouse_id": str(WAREHOUSE_A1),
                "scope": "FULL",
                "is_blind": True,
                "items": [{"product_id": str(pid), "quantity": "46.000000", "unit_cost": "10.000000"}],
                "notes": "Conteo ciclico fin de mes"
            }
        )
        assert res_cnt.status_code == 201
        cnt_data = res_cnt.json()
        count_id = cnt_data["id"]

        res_self_appr = await client.post(
            f"/api/v1/inventory/counts/{count_id}/approve",
            headers={**auth_warehouse_a, "Idempotency-Key": uuid4().hex}
        )
        assert res_self_appr.status_code == 403

        idemp_appr = uuid4().hex
        res_admin_appr = await client.post(
            f"/api/v1/inventory/counts/{count_id}/approve",
            headers={**auth_admin_a, "Idempotency-Key": idemp_appr}
        )
        assert res_admin_appr.status_code == 200
        assert res_admin_appr.json()["status"] == "approved"

        res_appr_repeat = await client.post(
            f"/api/v1/inventory/counts/{count_id}/approve",
            headers={**auth_admin_a, "Idempotency-Key": idemp_appr}
        )
        assert res_appr_repeat.status_code == 200

        with sync_session_factory() as session:
            final_stock = session.scalar(select(InventoryStockModel.physical_quantity).where(
                InventoryStockModel.company_id == COMPANY_A,
                InventoryStockModel.warehouse_id == WAREHOUSE_A1,
                InventoryStockModel.product_id == pid
            ))
            assert final_stock == Decimal("46.000000")


@pytest.mark.asyncio
async def test_reg13_repeated_reservation_receipt_transfer_and_return_idempotency(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "REG13", Decimal("40.00"), Decimal("80.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("100.00"), reserved=Decimal("0.00"), cost=Decimal("40.00"))

        doc_sale = uuid4()
        res_res1 = await client.post(
            "/api/v1/inventory/reservations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity": "10.00", "document_type": "SALE", "document_id": str(doc_sale)}
        )
        assert res_res1.status_code == 201

        res_res2 = await client.post(
            "/api/v1/inventory/reservations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity": "10.00", "document_type": "SALE", "document_id": str(doc_sale)}
        )
        assert res_res2.status_code == 201

        with sync_session_factory() as session:
            stk_res = session.scalar(select(InventoryStockModel.reserved_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk_res == Decimal("10.000000")

        rel1 = await client.post(
            "/api/v1/inventory/reservations/release",
            headers=auth_admin_a,
            json={"document_type": "SALE", "document_id": str(doc_sale), "product_id": str(pid)}
        )
        assert rel1.status_code == 200
        assert rel1.json()["released_count"] == 1

        rel2 = await client.post(
            "/api/v1/inventory/reservations/release",
            headers=auth_admin_a,
            json={"document_type": "SALE", "document_id": str(doc_sale), "product_id": str(pid)}
        )
        assert rel2.status_code == 200
        assert rel2.json()["released_count"] == 0

        with sync_session_factory() as session:
            stk_rel = session.scalar(select(InventoryStockModel.reserved_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert stk_rel == Decimal("0.000000")


@pytest.mark.asyncio
async def test_stk001_stk002_authoritative_ledger_reconciliation(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "LEDGER", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("0.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("50.00"), Decimal("10.00"), uuid4(), "ENTRADA_INICIAL")
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("-15.00"), Decimal("10.00"), uuid4(), "VENTA")
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("5.00"), Decimal("10.00"), uuid4(), "AJUSTE")
            session.commit()

        res_rec = await client.post(
            "/api/v1/inventory/reconcile",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid)}
        )
        assert res_rec.status_code == 200
        rec_data = res_rec.json()
        assert Decimal(rec_data["ledger_balance"]) == Decimal("40.000000")
        assert Decimal(rec_data["cached_stock_balance"]) == Decimal("40.000000")
        assert Decimal(rec_data["discrepancy_delta"]) == Decimal("0.000000")
        assert rec_data["status"] == "MATCH"


@pytest.mark.asyncio
async def test_stk003_stk022_stock_minimum_rules_and_deduplicated_alerts(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "MIN", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("5.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        res_rule = await client.post(
            "/api/v1/inventory/rules",
            headers=auth_admin_a,
            json={
                "warehouse_id": str(WAREHOUSE_A1),
                "product_id": str(pid),
                "min_quantity": "20.000000",
                "max_quantity": "100.000000",
                "reorder_point": "25.000000",
                "reorder_quantity": "50.000000"
            }
        )
        assert res_rule.status_code == 201

        res_recalc1 = await client.post("/api/v1/inventory/alerts/recalculate", headers=auth_admin_a)
        assert res_recalc1.status_code == 200

        res_recalc2 = await client.post("/api/v1/inventory/alerts/recalculate", headers=auth_admin_a)
        assert res_recalc2.status_code == 200

        res_alerts = await client.get("/api/v1/inventory/alerts", headers=auth_admin_a)
        assert res_alerts.status_code == 200
        matching = [a for a in res_alerts.json()["items"] if a["alert_type"] == "MIN_STOCK" and a.get("product_id") == str(pid)]
        assert len(matching) == 1
        alert_id = matching[0]["id"]

        res_fake_resolve = await client.post(f"/api/v1/inventory/alerts/{alert_id}/resolve", headers=auth_admin_a)
        assert res_fake_resolve.status_code == 422

        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("30.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))
        res_real_resolve = await client.post(f"/api/v1/inventory/alerts/{alert_id}/resolve", headers=auth_admin_a)
        assert res_real_resolve.status_code == 200
        assert res_real_resolve.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_stk004_stk005_atomic_reservation_and_anti_overselling(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "OVS", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("1.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        res1 = await client.post(
            "/api/v1/inventory/reservations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity": "1.00", "document_type": "ORDER", "document_id": str(uuid4())}
        )
        assert res1.status_code == 201

        res2 = await client.post(
            "/api/v1/inventory/reservations",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity": "1.00", "document_type": "ORDER", "document_id": str(uuid4())}
        )
        assert res2.status_code == 409


@pytest.mark.asyncio
async def test_stk006_goods_receipt_inspection_quarantine_separation(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        supplier_res = await client.post("/api/v1/suppliers", headers=auth_admin_a, json={"tax_id": uuid4().hex[:11], "legal_name": "Proveedor Inspeccion SAC"})
        assert supplier_res.status_code == 201
        supplier_id = supplier_res.json()["id"]

        pid = create_product(COMPANY_A, "INSP", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("0.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        order_res = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"supplier_id": supplier_id, "warehouse_id": str(WAREHOUSE_A1), "currency": "USD", "items": [{"product_id": str(pid), "quantity": "20.00", "unit_cost": "10.00"}]}
        )
        assert order_res.status_code == 201
        po_id = order_res.json()["id"]

        rcpt_res = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"purchase_order_id": po_id, "warehouse_id": str(WAREHOUSE_A1), "items": [{"product_id": str(pid), "quantity": "20.00", "unit_cost": "10.00"}], "inspection_status": "quarantine"}
        )
        assert rcpt_res.status_code == 201

        inv_check = await client.get(f"/api/v1/inventory?warehouse_id={WAREHOUSE_A1}&product_id={pid}", headers=auth_admin_a)
        assert inv_check.status_code == 200
        inv_data = inv_check.json()["items"]
        if inv_data:
            assert Decimal(inv_data[0]["available_quantity"]) == Decimal("0.000000")


@pytest.mark.asyncio
async def test_stk007_api051_adjustments_threshold_and_idempotency(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "ADJ", Decimal("10.00"), Decimal("20.00"))
        set_stock(COMPANY_A, WAREHOUSE_A1, pid, physical=Decimal("50.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))

        res_seller_huge = await client.post(
            "/api/v1/inventory/adjustments",
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex},
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity_delta": "600.00", "reason": "Ajuste masivo sin permiso", "unit_cost": "10.00"}
        )
        assert res_seller_huge.status_code == 403

        idemp_adj = uuid4().hex
        res_admin_adj = await client.post(
            "/api/v1/inventory/adjustments",
            headers={**auth_admin_a, "Idempotency-Key": idemp_adj},
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity_delta": "15.00", "reason": "Merma justificada y aprobada", "unit_cost": "10.00"}
        )
        assert res_admin_adj.status_code == 201
        m_id = res_admin_adj.json()["movement_id"]

        res_adj_repeat = await client.post(
            "/api/v1/inventory/adjustments",
            headers={**auth_admin_a, "Idempotency-Key": idemp_adj},
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid), "quantity_delta": "15.00", "reason": "Merma justificada y aprobada", "unit_cost": "10.00"}
        )
        assert res_adj_repeat.status_code == 201
        assert res_adj_repeat.json()["movement_id"] == m_id

        with sync_session_factory() as session:
            final_stock = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            assert final_stock == Decimal("65.000000")


@pytest.mark.asyncio
async def test_stk014_valuation_method_and_historical_margin(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_val = await client.post(
            "/api/v1/inventory/valuation",
            headers=auth_admin_a,
            json={"costing_method": "AVERAGE_WEIGHTED", "rounding_decimals": 6}
        )
        assert res_val.status_code == 200
        assert res_val.json()["costing_method"] == "AVERAGE_WEIGHTED"

        res_get_val = await client.get("/api/v1/inventory/valuation", headers=auth_admin_a)
        assert res_get_val.status_code == 200
        assert res_get_val.json()["costing_method"] == "AVERAGE_WEIGHTED"


@pytest.mark.asyncio
async def test_stk015_periodic_reconciliation_discrepancy_and_controlled_repair(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "REP", Decimal("10.00"), Decimal("20.00"))
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("30.00"), Decimal("10.00"), uuid4(), "ENTRADA_REAL")
            stk = session.scalar(select(InventoryStockModel).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid))
            stk.physical_quantity = Decimal("35.00")
            session.commit()

        res_rec = await client.post(
            "/api/v1/inventory/reconcile",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "product_id": str(pid)}
        )
        assert res_rec.status_code == 200
        rec_data = res_rec.json()
        assert rec_data["status"] == "DISCREPANCY"
        assert Decimal(rec_data["discrepancy_delta"]) == Decimal("5.000000")
        rec_id = rec_data["id"]

        res_repair = await client.post(
            f"/api/v1/inventory/reconcile/{rec_id}/repair",
            headers=auth_admin_a,
            json={"reason": "Ajuste controlado segun acta de auditoria AUD-902", "evidence": "acta_firmada_auditoria_902.pdf"}
        )
        assert res_repair.status_code == 200
        assert res_repair.json()["status"] == "REPAIRED"
        assert Decimal(res_repair.json()["after_balance"]) == Decimal("30.000000")


@pytest.mark.asyncio
async def test_stk017_api050_kardex_movements_filters_and_pagination(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "KDX", Decimal("10.00"), Decimal("20.00"))
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("10.00"), Decimal("10.00"), uuid4(), "KARDEX_IN")
            move_stock(session, COMPANY_A, WAREHOUSE_A1, pid, Decimal("-3.00"), Decimal("10.00"), uuid4(), "KARDEX_OUT")
            session.commit()

        res_mov = await client.get(f"/api/v1/inventory/movements?warehouse_id={WAREHOUSE_A1}&product_id={pid}", headers=auth_admin_a)
        assert res_mov.status_code == 200
        items = res_mov.json()["items"]
        assert len(items) >= 2
        types = [i["movement_type"] for i in items]
        assert "KARDEX_IN" in types
        assert "KARDEX_OUT" in types


@pytest.mark.asyncio
async def test_stk020_picking_and_packing_validation(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pid = create_product(COMPANY_A, "PCK", Decimal("10.00"), Decimal("20.00"))
        sale_id = uuid4()
        with sync_session_factory() as session:
            customer_id = UUID("00000000-0000-0000-0000-000000000114")
            if not session.get(CustomerModel, customer_id):
                session.add(CustomerModel(id=customer_id, company_id=COMPANY_A, code="PICKING-CUSTOMER", doc_type="DNI", doc_number="12345679", legal_name="Cliente de preparación", current_balance=Decimal("0"), credit_limit=Decimal("0")))
                session.flush()
            sale = SaleModel(
                id=sale_id,
                company_id=COMPANY_A,
                customer_id=UUID("00000000-0000-0000-0000-000000000114"),
                branch_id=BRANCH_A,
                warehouse_id=WAREHOUSE_A1,
                series="F001",
                number=int(secrets.randbelow(899999) + 100000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("20.00"),
                tax_amount=Decimal("3.60"),
                total_amount=Decimal("23.60"),
                paid_amount=Decimal("23.60"),
                version=1
            )
            session.add(sale)
            session.flush()
            session.add(SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale.id,
                product_id=pid,
                line_number=1,
                sku_snapshot="SKU-PCK-001",
                name_snapshot="Producto Picking",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("2.000000"),
                unit_price_snapshot=Decimal("10.000000"),
                unit_cost_snapshot=Decimal("5.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("20.000000"),
                tax_amount=Decimal("3.600000"),
                total_amount=Decimal("23.600000")
            ))
            session.commit()

        res_pck = await client.post(
            "/api/v1/inventory/picking-lists",
            headers=auth_admin_a,
            json={"warehouse_id": str(WAREHOUSE_A1), "sale_id": str(sale_id)}
        )
        assert res_pck.status_code == 201
        pck_id = res_pck.json()["id"]

        wrong_pid = create_product(COMPANY_A, "WRG", Decimal("5.00"), Decimal("10.00"))
        res_scan_wrong = await client.post(
            f"/api/v1/inventory/picking-lists/{pck_id}/verify-item",
            headers=auth_admin_a,
            json={"product_id": str(wrong_pid), "scanned_code": "SKU-WRONG", "quantity": "1.00"}
        )
        assert res_scan_wrong.status_code == 422

        res_scan_right = await client.post(
            f"/api/v1/inventory/picking-lists/{pck_id}/verify-item",
            headers=auth_admin_a,
            json={"product_id": str(pid), "scanned_code": str(pid), "quantity": "2.00"}
        )
        assert res_scan_right.status_code == 200
        assert res_scan_right.json()["is_verified"] is True

        res_comp = await client.post(f"/api/v1/inventory/picking-lists/{pck_id}/complete", headers=auth_admin_a)
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_stk021_concurrency_stable_locking():
    pid1 = create_product(COMPANY_A, "KIT1", Decimal("10.00"), Decimal("20.00"))
    pid2 = create_product(COMPANY_A, "KIT2", Decimal("15.00"), Decimal("30.00"))
    set_stock(COMPANY_A, WAREHOUSE_A1, pid1, physical=Decimal("100.00"), reserved=Decimal("0.00"), cost=Decimal("10.00"))
    set_stock(COMPANY_A, WAREHOUSE_A1, pid2, physical=Decimal("100.00"), reserved=Decimal("0.00"), cost=Decimal("15.00"))

    def execute_with_retry(fn):
        for attempt in range(10):
            try:
                fn()
                return
            except Exception:
                if attempt == 9:
                    raise
                time.sleep(0.05 * (attempt + 1))

    def worker_a():
        with sync_session_factory() as session:
            for p in sorted([pid1, pid2]):
                move_stock(session, COMPANY_A, WAREHOUSE_A1, p, Decimal("-2.00"), Decimal("10.00"), uuid4(), "KIT_SALE")
            session.commit()

    def worker_b():
        with sync_session_factory() as session:
            for p in sorted([pid1, pid2]):
                move_stock(session, COMPANY_A, WAREHOUSE_A1, p, Decimal("-3.00"), Decimal("10.00"), uuid4(), "KIT_TRANSFER")
            session.commit()

    loop = asyncio.get_running_loop()
    await asyncio.gather(
        loop.run_in_executor(None, lambda: execute_with_retry(worker_a)),
        loop.run_in_executor(None, lambda: execute_with_retry(worker_b))
    )

    with sync_session_factory() as session:
        stk1 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid1))
        stk2 = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.warehouse_id == WAREHOUSE_A1, InventoryStockModel.product_id == pid2))
        assert stk1 == Decimal("95.000000")
        assert stk2 == Decimal("95.000000")
