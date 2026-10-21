from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    InventoryStockModel,
    SaleModel,
    SaleLineModel,
    KardexMovementModel
)
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000005")
TEST_WAREHOUSE_B = UUID("00000000-0000-0000-0000-000000000006")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp = session.execute(
            select(CompanyModel).where(CompanyModel.id == TEST_COMPANY_ID)
        ).scalar_one_or_none()
        if not comp:
            comp = CompanyModel(
                id=TEST_COMPANY_ID,
                tax_id="20999999999",
                legal_name="EMPRESA COMERCIAL MATRIZ S.A.C.",
                trade_name="SALESIA CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp)
            session.flush()

        branch = session.execute(
            select(BranchModel).where(BranchModel.id == TEST_BRANCH_ID)
        ).scalar_one_or_none()
        if not branch:
            branch = BranchModel(
                id=TEST_BRANCH_ID,
                company_id=TEST_COMPANY_ID,
                code="SUC-01",
                name="Sucursal Principal Lima",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch)

        wh_a = session.execute(
            select(WarehouseModel).where(WarehouseModel.id == TEST_WAREHOUSE_A)
        ).scalar_one_or_none()
        if not wh_a:
            wh_a = WarehouseModel(
                id=TEST_WAREHOUSE_A,
                company_id=TEST_COMPANY_ID,
                branch_id=TEST_BRANCH_ID,
                code="ALM-01",
                name="Almacén Central",
                is_active=True
            )
            session.add(wh_a)

        wh_b = session.execute(
            select(WarehouseModel).where(WarehouseModel.id == TEST_WAREHOUSE_B)
        ).scalar_one_or_none()
        if not wh_b:
            wh_b = WarehouseModel(
                id=TEST_WAREHOUSE_B,
                company_id=TEST_COMPANY_ID,
                branch_id=TEST_BRANCH_ID,
                code="ALM-02",
                name="Almacén Secundario",
                is_active=True
            )
            session.add(wh_b)

        session.commit()
    yield


@pytest.fixture
def auth_headers():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="company_admin",
        email="admin@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def approver_headers():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        role="company_admin",
        email="approver@salesia.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_quotation_lifecycle_and_conversion(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        product_id = uuid4()
        sku_code = f"PROD-QUOT-{uuid4().hex[:6]}"
        with sync_session_factory() as session:
            session.add(CustomerModel(
                id=customer_id,
                company_id=TEST_COMPANY_ID,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Cotizacion SAC",
                is_active=True
            ))
            session.add(ProductModel(
                id=product_id,
                company_id=TEST_COMPANY_ID,
                sku=sku_code,
                name="Servidor Rack 2U",
                category="TI",
                unit_of_measure="NIU",
                unit_price=Decimal("1500.000000"),
                unit_cost=Decimal("1000.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            ))
            session.flush()
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                warehouse_id=TEST_WAREHOUSE_A,
                product_id=product_id,
                physical_quantity=Decimal("10.000000"),
                reserved_quantity=Decimal("0.000000")
            ))
            session.commit()

        valid_future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        q_res = await client.post(
            "/api/v1/quotations",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(customer_id),
                "branch_id": str(TEST_BRANCH_ID),
                "valid_until": valid_future,
                "lines": [
                    {
                        "product_id": str(product_id),
                        "sku": sku_code,
                        "name": "Servidor Rack 2U",
                        "quantity": "2",
                        "unit_price": "1500.00",
                        "discount_pct": "5.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert q_res.status_code == 201
        q_data = q_res.json()
        assert Decimal(q_data["subtotal_amount"]) == Decimal("2850.000000")
        assert Decimal(q_data["total_amount"]) == Decimal("3363.000000")
        quotation_id = q_data["quotation_id"]

        v2_res = await client.post(
            f"/api/v1/quotations/{quotation_id}/versions",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "lines": [
                    {
                        "product_id": str(product_id),
                        "sku": sku_code,
                        "name": "Servidor Rack 2U",
                        "quantity": "3",
                        "unit_price": "1500.00",
                        "discount_pct": "10.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert v2_res.status_code == 201
        v2_data = v2_res.json()
        assert v2_data["version"] == 2
        assert v2_data["quotation_number"] == q_data["quotation_number"]

        v2_quotation_id = v2_data["quotation_id"]

        accept_res = await client.post(
            f"/api/v1/quotations/{v2_quotation_id}/accept",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert accept_res.status_code == 200
        assert accept_res.json()["status"] == "accepted"

        conv_key = uuid4().hex
        conv1_res = await client.post(
            f"/api/v1/quotations/{v2_quotation_id}/convert?warehouse_id={TEST_WAREHOUSE_A}",
            headers={**auth_headers, "Idempotency-Key": conv_key}
        )
        assert conv1_res.status_code == 201
        conv1_data = conv1_res.json()
        order_id = conv1_data["order_id"]

        conv2_res = await client.post(
            f"/api/v1/quotations/{v2_quotation_id}/convert?warehouse_id={TEST_WAREHOUSE_A}",
            headers={**auth_headers, "Idempotency-Key": conv_key}
        )
        assert conv2_res.status_code == 201
        conv2_data = conv2_res.json()
        assert conv2_data["order_id"] == order_id


@pytest.mark.asyncio
async def test_order_reservations_and_insufficient_stock(auth_headers, approver_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        prod_id = uuid4()
        sku_code = f"PROD-RESERV-{uuid4().hex[:6]}"

        with sync_session_factory() as session:
            session.add(CustomerModel(
                id=customer_id,
                company_id=TEST_COMPANY_ID,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Orden SAC",
                is_active=True
            ))
            session.add(ProductModel(
                id=prod_id,
                company_id=TEST_COMPANY_ID,
                sku=sku_code,
                name="Router Cisco Enterprise",
                category="TI",
                unit_of_measure="NIU",
                unit_price=Decimal("250.000000"),
                unit_cost=Decimal("150.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            ))
            session.flush()
            stock = InventoryStockModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                warehouse_id=TEST_WAREHOUSE_A,
                product_id=prod_id,
                physical_quantity=Decimal("10.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)
            session.commit()

        order_res = await client.post(
            "/api/v1/orders",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(customer_id),
                "branch_id": str(TEST_BRANCH_ID),
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_code,
                        "name": "Router Cisco Enterprise",
                        "quantity": "8",
                        "unit_price": "250.00",
                        "discount_pct": "20.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert order_res.status_code == 201
        order_data = order_res.json()
        assert order_data["status"] == "pending_approval"
        assert order_data["requires_approval"] is True
        order_id = order_data["order_id"]

        appr_res = await client.post(
            f"/api/v1/orders/{order_id}/approve",
            headers={**approver_headers, "Idempotency-Key": uuid4().hex}
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "draft"

        conf_res = await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert conf_res.status_code == 200
        assert conf_res.json()["stock_reserved"] is True

        with sync_session_factory() as session:
            stk = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk.reserved_quantity == Decimal("8.000000")

        order2_res = await client.post(
            "/api/v1/orders",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(customer_id),
                "branch_id": str(TEST_BRANCH_ID),
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_code,
                        "name": "Router Cisco Enterprise",
                        "quantity": "5",
                        "unit_price": "250.00",
                        "discount_pct": "0.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert order2_res.status_code == 201
        order2_id = order2_res.json()["order_id"]

        conf_fail_res = await client.post(
            f"/api/v1/orders/{order2_id}/confirm",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert conf_fail_res.status_code == 409

        cancel_res = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cancel_res.status_code == 200

        with sync_session_factory() as session:
            stk_after = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk_after.reserved_quantity == Decimal("0.000000")


@pytest.mark.asyncio
async def test_sales_draft_and_atomic_kardex_deduction(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        prod_id = uuid4()
        sku_code = f"SKU-SWITCH-{uuid4().hex[:6]}"

        with sync_session_factory() as session:
            session.add(CustomerModel(
                id=customer_id,
                company_id=TEST_COMPANY_ID,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Ventas SAC",
                is_active=True
            ))
            session.add(ProductModel(
                id=prod_id,
                company_id=TEST_COMPANY_ID,
                sku=sku_code,
                name="Switch Gigabit 48 Puertos",
                category="TI",
                unit_of_measure="NIU",
                unit_price=Decimal("400.000000"),
                unit_cost=Decimal("220.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            ))
            session.flush()
            stock = InventoryStockModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                warehouse_id=TEST_WAREHOUSE_A,
                product_id=prod_id,
                physical_quantity=Decimal("20.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)
            session.commit()

        draft_res = await client.post(
            "/api/v1/sales/draft",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(TEST_BRANCH_ID),
                "customer_id": str(customer_id),
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_code,
                        "product_name": "Switch Gigabit 48 Puertos",
                        "quantity": 5,
                        "unit_price": "400.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert draft_res.status_code == 201
        draft_data = draft_res.json()
        sale_id = draft_data["sale_id"]
        assert Decimal(draft_data["total_amount"]) == Decimal("2360.00")

        confirm_res = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers, "Idempotency-Key": f"key-{sale_id}"}
        )
        assert confirm_res.status_code == 200
        assert confirm_res.json()["status"] == "confirmed"

        with sync_session_factory() as session:
            updated_stock = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert updated_stock.physical_quantity == Decimal("15.000000")

            kardex = session.execute(
                select(KardexMovementModel).where(
                    KardexMovementModel.company_id == TEST_COMPANY_ID,
                    KardexMovementModel.reference_doc_id == UUID(sale_id)
                )
            ).scalar_one()
            assert kardex.movement_type == "VENTA"
            assert kardex.quantity_delta == Decimal("-5.000000")

        annul_res = await client.post(
            f"/api/v1/sales/{sale_id}/annul",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={"reason": "Cliente solicitó cancelación por cambio de proyecto"}
        )
        assert annul_res.status_code == 200
        assert annul_res.json()["status"] == "cancelled"

        with sync_session_factory() as session:
            restored_stock = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert restored_stock.physical_quantity == Decimal("20.000000")

        clone_res = await client.post(
            f"/api/v1/sales/{sale_id}/clone",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert clone_res.status_code == 200
        assert clone_res.json()["status"] == "draft"
        assert clone_res.json()["cloned_sale_id"] != sale_id


@pytest.mark.asyncio
async def test_payments_cash_tendered_and_cash_session_blind_closure(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        customer_id = uuid4()
        sale_id = uuid4()
        with sync_session_factory() as session:
            session.add(CustomerModel(
                id=customer_id,
                company_id=TEST_COMPANY_ID,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Pagos SAC",
                is_active=True
            ))
            session.flush()
            sale = SaleModel(
                id=sale_id,
                company_id=TEST_COMPANY_ID,
                branch_id=TEST_BRANCH_ID,
                customer_id=customer_id,
                series="B001",
                number=int(uuid4().int % 1000000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("100.000000"),
                tax_amount=Decimal("18.000000"),
                total_amount=Decimal("118.000000"),
                paid_amount=Decimal("0.000000")
            )
            session.add(sale)
            session.commit()

        pay1_res = await client.post(
            "/api/v1/payments",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "CASH",
                "amount": 50.00,
                "cash_tendered": 100.00
            }
        )
        assert pay1_res.status_code == 201
        pay1_data = pay1_res.json()
        assert Decimal(pay1_data["change"]) == Decimal("50.000000")
        assert Decimal(pay1_data["remaining_due"]) == Decimal("68.000000")

        pay2_res = await client.post(
            "/api/v1/payments",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "TRANSFER",
                "amount": 68.00,
                "reference_code": "VISA-AUTH-998822"
            }
        )
        assert pay2_res.status_code == 201
        pay2_data = pay2_res.json()
        assert Decimal(pay2_data["remaining_due"]) == Decimal("0.000000")
        assert pay2_data["sale_status"] == "paid"

        term_code = f"POS-{uuid4().hex[:4]}"
        open_cash_res = await client.post(
            "/api/v1/cash-sessions",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(TEST_BRANCH_ID),
                "terminal_code": term_code,
                "opening_balance": 200.00
            }
        )
        assert open_cash_res.status_code == 201
        session_id = open_cash_res.json()["session_id"]

        dep_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/movements",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "movement_type": "DEPOSIT",
                "amount": 100.00,
                "reason": "Ingreso extra para fondo de cambio"
            }
        )
        assert dep_res.status_code == 201
        assert Decimal(dep_res.json()["current_balance"]) == Decimal("300.00")

        wit_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/movements",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "movement_type": "WITHDRAWAL",
                "amount": 40.00,
                "reason": "Pago servicio de mensajería"
            }
        )
        assert wit_res.status_code == 201
        assert Decimal(wit_res.json()["current_balance"]) == Decimal("260.00")

        close_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/close",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "counted_balance": 255.00,
                "notes": "Arqueo ciego turno tarde"
            }
        )
        assert close_res.status_code == 200
        close_data = close_res.json()
        assert close_data["status"] == "closed"
        assert Decimal(close_data["expected_balance"]) == Decimal("260.00")
        assert Decimal(close_data["counted_balance"]) == Decimal("255.00")
        assert Decimal(close_data["difference"]) == Decimal("-5.000000")


@pytest.mark.asyncio
async def test_transfers_goods_receipts_and_returns(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod_id = uuid4()
        customer_id = uuid4()
        sku_code = f"SKU-TRANS-{uuid4().hex[:6]}"

        with sync_session_factory() as session:
            session.add(CustomerModel(
                id=customer_id,
                company_id=TEST_COMPANY_ID,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Transfer SAC",
                is_active=True
            ))
            session.add(ProductModel(
                id=prod_id,
                company_id=TEST_COMPANY_ID,
                sku=sku_code,
                name="Producto Transferencia",
                category="TI",
                unit_of_measure="NIU",
                unit_price=Decimal("100.000000"),
                unit_cost=Decimal("50.000000"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            ))
            session.flush()
            stock_a = InventoryStockModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                warehouse_id=TEST_WAREHOUSE_A,
                product_id=prod_id,
                physical_quantity=Decimal("30.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock_a)
            session.commit()

        transfer_res = await client.post(
            "/api/v1/inventory/transfers",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "source_warehouse_id": str(TEST_WAREHOUSE_A),
                "destination_warehouse_id": str(TEST_WAREHOUSE_B),
                "items": [
                    {
                        "product_id": str(prod_id),
                        "quantity": "10.00",
                        "unit_cost": "50.00"
                    }
                ]
            }
        )
        assert transfer_res.status_code == 201
        transfer_id = transfer_res.json()["id"]

        disp_res = await client.post(
            f"/api/v1/inventory/transfers/{transfer_id}/dispatch",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert disp_res.status_code == 200

        with sync_session_factory() as session:
            stk_a = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.warehouse_id == TEST_WAREHOUSE_A,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk_a.physical_quantity == Decimal("20.000000")

        rcv_res = await client.post(
            f"/api/v1/inventory/transfers/{transfer_id}/receive",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert rcv_res.status_code == 200

        with sync_session_factory() as session:
            stk_b = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.warehouse_id == TEST_WAREHOUSE_B,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk_b.physical_quantity == Decimal("10.000000")

        sup_res = await client.post(
            "/api/v1/suppliers",
            headers=auth_headers,
            json={
                "tax_id": f"20{uuid4().int % 1000000000:09d}",
                "legal_name": "Proveedor Mayorista SAC",
                "email": f"supp_{uuid4().hex[:6]}@proveedor.com"
            }
        )
        assert sup_res.status_code == 201
        supplier_id = sup_res.json()["id"]

        po_res = await client.post(
            "/api/v1/purchase-orders",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "supplier_id": supplier_id,
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "currency": "USD",
                "items": [
                    {
                        "product_id": str(prod_id),
                        "quantity": "20.00",
                        "unit_cost": "60.00"
                    }
                ]
            }
        )
        assert po_res.status_code == 201
        po_id = po_res.json()["id"]

        receipt_res = await client.post(
            "/api/v1/goods-receipts",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "purchase_order_id": po_id,
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "items": [
                    {
                        "product_id": str(prod_id),
                        "quantity": "20.00",
                        "unit_cost": "60.00"
                    }
                ]
            }
        )
        assert receipt_res.status_code == 201

        with sync_session_factory() as session:
            stk_a_new = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.warehouse_id == TEST_WAREHOUSE_A,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk_a_new.physical_quantity == Decimal("40.000000")

        draft_sale_res = await client.post(
            "/api/v1/sales/draft",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(TEST_BRANCH_ID),
                "customer_id": str(customer_id),
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": sku_code,
                        "product_name": "Producto Transferencia",
                        "quantity": 5,
                        "unit_price": "100.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert draft_sale_res.status_code == 201
        sale_for_return_id = draft_sale_res.json()["sale_id"]

        confirm_sale_res = await client.post(
            f"/api/v1/sales/{sale_for_return_id}/confirm",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert confirm_sale_res.status_code == 200

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_headers,
            json={
                "sale_id": sale_for_return_id,
                "warehouse_id": str(TEST_WAREHOUSE_A),
                "reason": "Empaque dañado en tránsito",
                "items": [
                    {
                        "product_id": str(prod_id),
                        "quantity": "2.00",
                        "disposition": "RESTOCK"
                    }
                ]
            }
        )
        assert ret_res.status_code == 201
        return_id = ret_res.json()["id"]

        accept_ret_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex}
        )
        assert accept_ret_res.status_code == 200

        with sync_session_factory() as session:
            stk_a_after_return = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == TEST_COMPANY_ID,
                    InventoryStockModel.warehouse_id == TEST_WAREHOUSE_A,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stk_a_after_return.physical_quantity == Decimal("37.000000")
