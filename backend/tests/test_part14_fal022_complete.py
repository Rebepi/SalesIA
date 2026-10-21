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
    SaleLineModel,
    PaymentModel
)
from salesia.modules.inventario.infrastructure_models import (
    SupplyDocument,
    SupplyLine,
    InventoryQuarantine
)
from salesia.modules.finanzas.infrastructure_models import (
    CreditNoteModel,
    CreditNoteLineModel,
    CustomerCreditMovementModel
)
from salesia.shared.infrastructure.transactions import RefundModel
from salesia.modules.inventario.service import move_stock
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000101")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000109")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000102")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000192")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000104")
WAREHOUSE_B = UUID("00000000-0000-0000-0000-000000000194")
CUSTOMER_A = UUID("00000000-0000-0000-0000-000000000114")
CUSTOMER_B = UUID("00000000-0000-0000-0000-000000000195")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000103")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000107")
USER_WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000106")
USER_ANALYST_A = UUID("00000000-0000-0000-0000-000000000105")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000108")


@pytest.fixture(autouse=True, scope="module")
def setup_part14_data():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999000101", "Empresa A P14"), (COMPANY_B, "20999000109", "Empresa B P14")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        session.flush()
        for bid, cid, code, name in [(BRANCH_A, COMPANY_A, "SUC-P14-A", "Sucursal P14 A"), (BRANCH_B, COMPANY_B, "SUC-P14-B", "Sucursal P14 B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=name, timezone="America/Lima", is_active=True))
        session.flush()
        for wid, cid, bid, code, name in [
            (WAREHOUSE_A, COMPANY_A, BRANCH_A, "WH-P14-A", "Almacen Principal P14 A"),
            (WAREHOUSE_B, COMPANY_B, BRANCH_B, "WH-P14-B", "Almacen Rival P14 B")
        ]:
            wh = session.scalar(select(WarehouseModel).where(WarehouseModel.id == wid))
            if not wh:
                session.add(WarehouseModel(id=wid, company_id=cid, branch_id=bid, code=code, name=name, is_active=True))
        session.flush()
        for cust_id, cid, doc_num, name in [
            (CUSTOMER_A, COMPANY_A, "10000000001", "Cliente P14 A"),
            (CUSTOMER_B, COMPANY_B, "10000000009", "Cliente P14 B")
        ]:
            c = session.scalar(select(CustomerModel).where(CustomerModel.id == cust_id))
            if not c:
                session.add(CustomerModel(id=cust_id, company_id=cid, code=f"CLI-{doc_num}", doc_type="DNI", doc_number=doc_num, legal_name=name, credit_limit=Decimal("5000.00"), current_balance=Decimal("0.00"), is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_admin_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_p14_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_seller_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_p14_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_warehouse_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_WAREHOUSE_A, role="warehouse", email="warehouse_p14_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_analyst_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ANALYST_A, role="analyst", email="analyst_p14_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_admin_b():
    identity = create_durable_identity(company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_p14_b@rival.enterprise", password="valid_password")
    return identity["headers"]


def create_test_product(company_id=COMPANY_A, cost=Decimal("20.000000"), price=Decimal("50.000000"), discount=Decimal("0.000000")):
    pid = uuid4()
    with sync_session_factory() as session:
        prod = ProductModel(
            id=pid,
            company_id=company_id,
            sku=f"SKU-P14-{uuid4().hex[:8]}",
            name=f"Producto Test P14 {uuid4().hex[:4]}",
            category="Pruebas",
            unit_of_measure="NIU",
            unit_price=price,
            unit_cost=cost,
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(prod)
        session.commit()
    return pid


def create_test_sale(company_id=COMPANY_A, branch_id=None, warehouse_id=None, customer_id=None, product_id=None, qty=Decimal("10.000000"), price=Decimal("50.000000"), cost=Decimal("20.000000"), discount=Decimal("0.000000"), confirmed_days_ago=0, status="confirmed", is_credit=False):
    if branch_id is None:
        branch_id = BRANCH_B if company_id == COMPANY_B else BRANCH_A
    if warehouse_id is None:
        warehouse_id = WAREHOUSE_B if company_id == COMPANY_B else WAREHOUSE_A
    if customer_id is None:
        customer_id = CUSTOMER_B if company_id == COMPANY_B else CUSTOMER_A
    if product_id is None:
        product_id = create_test_product(company_id=company_id, cost=cost, price=price)
    sale_id = uuid4()
    with sync_session_factory() as session:
        subtotal = ((qty * price) - discount).quantize(Decimal("0.000001"))
        tax = (subtotal * Decimal("0.1800")).quantize(Decimal("0.000001"))
        total = subtotal + tax
        conf_at = datetime.now(timezone.utc) - timedelta(days=confirmed_days_ago)

        sale = SaleModel(
            id=sale_id,
            company_id=company_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            customer_id=customer_id,
            version=1,
            is_credit=is_credit,
            series="BV01",
            number=secrets.randbelow(900000) + 100000,
            status=status,
            currency="USD",
            subtotal_amount=subtotal,
            tax_amount=tax,
            total_amount=total,
            paid_amount=total if status == "paid" else Decimal("0.000000"),
            confirmed_at=conf_at
        )
        session.add(sale)
        session.flush()

        line = SaleLineModel(
            id=uuid4(),
            company_id=company_id,
            sale_id=sale_id,
            product_id=product_id,
            line_number=1,
            sku_snapshot="SKU-SNAPSHOT",
            name_snapshot="Nombre Snapshot",
            unit_of_measure_snapshot="NIU",
            quantity=qty,
            unit_price_snapshot=price,
            unit_cost_snapshot=cost,
            discount_amount=discount,
            tax_rate_snapshot=Decimal("0.1800"),
            subtotal_amount=subtotal,
            tax_amount=tax,
            total_amount=total
        )
        session.add(line)

        move_stock(session, company_id, warehouse_id, product_id, 100, cost, sale_id, "STOCK_INICIAL")
        move_stock(session, company_id, warehouse_id, product_id, -qty, cost, sale_id, "VENTA")

        session.commit()
    return sale_id, product_id, total


@pytest.mark.asyncio
async def test_fal022_ret001_solicitud_desde_venta_and_max_elegible(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("5.000000"), price=Decimal("100.000000"))

        elig_res = await client.get(f"/api/v1/returns/sales/{sale_id}/eligible", headers=auth_admin_a)
        assert elig_res.status_code == 200
        data = elig_res.json()
        assert data["sale_id"] == str(sale_id)
        assert len(data["lines"]) == 1
        line_info = data["lines"][0]
        assert Decimal(line_info["sold_quantity"]) == Decimal("5.000000")
        assert Decimal(line_info["eligible_quantity"]) == Decimal("5.000000")
        assert Decimal(line_info["returned_quantity"]) == Decimal("0.000000")

        exceed_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Excede cantidad vendida",
                "items": [{"product_id": str(prod_id), "quantity": "6.000000", "disposition": "RESTOCK"}]
            }
        )
        assert exceed_res.status_code == 409

        ret_res1 = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Primera devolucion parcial",
                "items": [{"product_id": str(prod_id), "quantity": "3.000000", "disposition": "RESTOCK"}]
            }
        )
        assert ret_res1.status_code == 201

        ret_res2 = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Segunda devolucion que excede remanente",
                "items": [{"product_id": str(prod_id), "quantity": "3.000000", "disposition": "RESTOCK"}]
            }
        )
        assert ret_res2.status_code == 409

        ret_res3 = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Segunda devolucion exacta remanente",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        assert ret_res3.status_code == 201


@pytest.mark.asyncio
async def test_fal022_ret002_motivos_y_politica_rechazo_conserva_solicitud(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_old_id, prod_id, _ = create_test_sale(qty=Decimal("4.000000"), confirmed_days_ago=45)

        old_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_old_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Devolucion fuera de plazo",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}],
                "authorized_exception": False
            }
        )
        assert old_res.status_code == 422

        exc_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_old_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Devolucion con excepcion aprobada",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}],
                "authorized_exception": True,
                "exception_reason": "Garantia extendida por gerencia comercial"
            }
        )
        assert exc_res.status_code == 201
        ret_id = exc_res.json()["id"]

        reject_res = await client.post(
            f"/api/v1/returns/{ret_id}/reject",
            headers=auth_admin_a,
            json={
                "reason": "El producto tiene signos evidentes de impacto y humedad",
                "criterion": "POLITICA_MAL_USO_CLIENTE"
            }
        )
        assert reject_res.status_code == 200
        rejected_doc = reject_res.json()
        assert rejected_doc["status"] == "rejected"
        assert rejected_doc["details"]["rejection_criterion"] == "POLITICA_MAL_USO_CLIENTE"

        get_res = await client.get(f"/api/v1/returns/{ret_id}", headers=auth_admin_a)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_fal022_ret003_recepcion_e_inspeccion_destinos_fisicos(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_a = create_test_product()
        prod_b = create_test_product()
        sale_id = uuid4()
        with sync_session_factory() as session:
            sale = SaleModel(
                id=sale_id,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                warehouse_id=WAREHOUSE_A,
                customer_id=CUSTOMER_A,
                version=1,
                is_credit=False,
                series="BV01",
                number=secrets.randbelow(900000) + 100000,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("200.000000"),
                tax_amount=Decimal("36.000000"),
                total_amount=Decimal("236.000000"),
                paid_amount=Decimal("0.000000"),
                confirmed_at=datetime.now(timezone.utc)
            )
            session.add(sale)
            session.flush()
            session.add(SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale_id,
                product_id=prod_a,
                line_number=1,
                sku_snapshot="SKU-A",
                name_snapshot="A",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("10.000000"),
                unit_price_snapshot=Decimal("10.000000"),
                unit_cost_snapshot=Decimal("5.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("100.000000"),
                tax_amount=Decimal("18.000000"),
                total_amount=Decimal("118.000000")
            ))
            session.add(SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale_id,
                product_id=prod_b,
                line_number=2,
                sku_snapshot="SKU-B",
                name_snapshot="B",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("10.000000"),
                unit_price_snapshot=Decimal("10.000000"),
                unit_cost_snapshot=Decimal("5.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("100.000000"),
                tax_amount=Decimal("18.000000"),
                total_amount=Decimal("118.000000")
            ))
            move_stock(session, COMPANY_A, WAREHOUSE_A, prod_a, 50, Decimal("5.000000"), sale_id, "INIT")
            move_stock(session, COMPANY_A, WAREHOUSE_A, prod_b, 50, Decimal("5.000000"), sale_id, "INIT")
            move_stock(session, COMPANY_A, WAREHOUSE_A, prod_a, -10, Decimal("5.000000"), sale_id, "VENTA")
            move_stock(session, COMPANY_A, WAREHOUSE_A, prod_b, -10, Decimal("5.000000"), sale_id, "VENTA")
            session.commit()

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Inspeccion mixta",
                "items": [
                    {"product_id": str(prod_a), "quantity": "4.000000", "disposition": "RESTOCK"},
                    {"product_id": str(prod_b), "quantity": "3.000000", "disposition": "QUARANTINE"}
                ]
            }
        )
        assert ret_res.status_code == 201
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "inspections": [
                    {"product_id": str(prod_a), "disposition": "RESTOCK"},
                    {"product_id": str(prod_b), "disposition": "QUARANTINE"}
                ]
            }
        )
        assert accept_res.status_code == 200

        with sync_session_factory() as session:
            stk_a = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A, InventoryStockModel.product_id == prod_a))
            stk_b = session.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == COMPANY_A, InventoryStockModel.warehouse_id == WAREHOUSE_A, InventoryStockModel.product_id == prod_b))
            quar_b = session.scalar(select(InventoryQuarantine.quantity).where(InventoryQuarantine.company_id == COMPANY_A, InventoryQuarantine.reference_doc_id == UUID(return_id)))

            assert stk_a == Decimal("44.000000")
            assert stk_b == Decimal("40.000000")
            assert quar_b == Decimal("3.000000")


@pytest.mark.asyncio
async def test_fal022_ret004_nota_de_credito_trazable_y_conciliacion(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("4.000000"), price=Decimal("100.000000"), cost=Decimal("40.000000"))

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Generacion de nota de credito",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True, "credit_action": "CREDIT_NOTE"}
        )
        assert accept_res.status_code == 200
        data = accept_res.json()
        assert "credit_note" in data
        cn_info = data["credit_note"]
        cn_id = cn_info["id"]
        assert cn_info["series"] == "NC01"
        assert Decimal(cn_info["total_amount"]) == Decimal("236.000000")

        cn_res = await client.get(f"/api/v1/credit-notes/{cn_id}", headers=auth_admin_a)
        assert cn_res.status_code == 200
        cn_data = cn_res.json()
        assert cn_data["sale_id"] == str(sale_id)
        assert len(cn_data["lines"]) == 1
        assert Decimal(cn_data["lines"][0]["unit_price"]) == Decimal("100.000000")


@pytest.mark.asyncio
async def test_fal022_ret005_saldo_a_favor_store_credit_movimientos_y_aplicacion(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_1_id, prod_1, _ = create_test_sale(qty=Decimal("2.000000"), price=Decimal("50.000000"))

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_1_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Retorno para saldo a favor",
                "items": [{"product_id": str(prod_1), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True, "credit_action": "STORE_CREDIT"}
        )
        assert accept_res.status_code == 200
        assert Decimal(accept_res.json()["store_credit_accrued"]) == Decimal("118.000000")

        bal_res = await client.get(f"/api/v1/customers/{CUSTOMER_A}/store-credit", headers=auth_admin_a)
        assert bal_res.status_code == 200
        assert Decimal(bal_res.json()["available_balance"]) >= Decimal("118.000000")

        sale_2_id, prod_2, total_2 = create_test_sale(qty=Decimal("1.000000"), price=Decimal("100.000000"))
        
        apply_res = await client.post(
            f"/api/v1/sales/{sale_2_id}/apply-store-credit",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"amount": "118.000000"}
        )
        assert apply_res.status_code == 200
        assert apply_res.json()["sale_status"] == "paid"
        assert Decimal(apply_res.json()["sale_paid_amount"]) == Decimal("118.000000")

        apply_again_res = await client.post(
            f"/api/v1/sales/{sale_2_id}/apply-store-credit",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"amount": "10.000000"}
        )
        assert apply_again_res.status_code == 409


@pytest.mark.asyncio
async def test_fal022_ret006_reembolso_al_pago_original_concurrencia(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("2.000000"), price=Decimal("100.000000"))
        payment_id = uuid4()
        with sync_session_factory() as session:
            pay = PaymentModel(
                id=payment_id,
                company_id=COMPANY_A,
                sale_id=sale_id,
                payment_method="CARD",
                amount=Decimal("236.000000"),
                currency="USD",
                reference_code="AUTH-CARD-12345",
                status="confirmed"
            )
            session.add(pay)
            sale = session.get(SaleModel, sale_id)
            sale.paid_amount = Decimal("236.000000")
            sale.status = "paid"
            session.commit()

        ref1_res = await client.post(
            "/api/v1/refunds",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "payment_id": str(payment_id),
                "amount": "150.000000",
                "reason": "Reembolso parcial solicitado por cliente"
            }
        )
        assert ref1_res.status_code == 201

        ref_excess = await client.post(
            "/api/v1/refunds",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "payment_id": str(payment_id),
                "amount": "100.000000",
                "reason": "Excede saldo reembolsable"
            }
        )
        assert ref_excess.status_code == 409

        ref2_res = await client.post(
            "/api/v1/refunds",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "payment_id": str(payment_id),
                "amount": "86.000000",
                "reason": "Reembolso final exacto"
            }
        )
        assert ref2_res.status_code == 201

        with sync_session_factory() as session:
            total_ref = session.scalar(select(func.sum(RefundModel.amount)).where(RefundModel.payment_id == payment_id))
            assert total_ref == Decimal("236.000000")


@pytest.mark.asyncio
async def test_fal022_ret007_estados_del_reembolso_timeout_seguro(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("1.000000"), price=Decimal("50.000000"))
        payment_id = uuid4()
        refund_id = uuid4()
        with sync_session_factory() as session:
            pay = PaymentModel(
                id=payment_id,
                company_id=COMPANY_A,
                sale_id=sale_id,
                payment_method="GATEWAY_STRIPE",
                amount=Decimal("59.000000"),
                currency="USD",
                status="confirmed"
            )
            session.add(pay)
            ref = RefundModel(
                id=refund_id,
                company_id=COMPANY_A,
                payment_id=payment_id,
                amount=Decimal("59.000000"),
                reason="Reembolso con ciclo de vida",
                status="requested",
                provider_reference="REQ-12345"
            )
            session.add(ref)
            session.commit()

        st_res1 = await client.post(
            f"/api/v1/refunds/{refund_id}/status",
            headers=auth_admin_a,
            json={"status": "approved"}
        )
        assert st_res1.status_code == 200

        st_res2 = await client.post(
            f"/api/v1/refunds/{refund_id}/status",
            headers=auth_admin_a,
            json={"status": "sent"}
        )
        assert st_res2.status_code == 200

        timeout_res = await client.post(
            f"/api/v1/refunds/{refund_id}/status",
            headers=auth_admin_a,
            json={"status": "requires_reconciliation", "failure_reason": "Gateway timeout response: transaction in indeterminate state"}
        )
        assert timeout_res.status_code == 200
        assert timeout_res.json()["status"] == "requires_reconciliation"

        inv_res = await client.post(
            f"/api/v1/refunds/{refund_id}/status",
            headers=auth_admin_a,
            json={"status": "requested"}
        )
        assert inv_res.status_code == 409


@pytest.mark.asyncio
async def test_fal022_ret008_cambio_de_producto_exchange(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        orig_sale_id, prod_ret_id, _ = create_test_sale(qty=Decimal("2.000000"), price=Decimal("100.000000"), cost=Decimal("30.000000"))
        
        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(orig_sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Cambio por otra talla/modelo",
                "items": [{"product_id": str(prod_ret_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True, "credit_action": "CREDIT_NOTE"}
        )
        assert accept_res.status_code == 200

        replacement_prod_id = create_test_product(price=Decimal("120.000000"), cost=Decimal("40.000000"))
        with sync_session_factory() as session:
            move_stock(session, COMPANY_A, WAREHOUSE_A, replacement_prod_id, 20, Decimal("40.000000"), orig_sale_id, "INIT")
            session.commit()

        exch_res = await client.post(
            f"/api/v1/returns/{return_id}/exchange",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "warehouse_id": str(WAREHOUSE_A),
                "replacement_items": [{"product_id": str(replacement_prod_id), "quantity": "2.000000"}]
            }
        )
        assert exch_res.status_code == 200
        exch_data = exch_res.json()
        assert exch_data["original_sale_id"] == str(orig_sale_id)
        assert Decimal(exch_data["return_credit_applied"]) == Decimal("236.000000")
        assert Decimal(exch_data["difference"]) > Decimal("0")

        with sync_session_factory() as session:
            orig_sale = session.get(SaleModel, orig_sale_id)
            assert orig_sale is not None
            assert len(orig_sale.lines) == 1


@pytest.mark.asyncio
async def test_fal022_ret009_devolucion_sin_comprobante_politica_limites(auth_admin_a, auth_seller_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = create_test_product(price=Decimal("150.000000"))

        seller_excess_res = await client.post(
            "/api/v1/returns/without-receipt",
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(CUSTOMER_A),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Sin comprobante que excede límite",
                "manual_valuation_total": "300.000000",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        assert seller_excess_res.status_code == 403

        admin_res = await client.post(
            "/api/v1/returns/without-receipt",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(CUSTOMER_A),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Autorizado por direccion comercial",
                "manual_valuation_total": "180.000000",
                "items": [{"product_id": str(prod_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        assert admin_res.status_code == 201
        assert admin_res.json()["details"]["is_without_receipt"] is True


@pytest.mark.asyncio
async def test_fal022_ret010_reversion_de_promocion_prorrateo_descuento(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("4.000000"), price=Decimal("100.000000"), discount=Decimal("80.000000"))

        elig_res = await client.get(f"/api/v1/returns/sales/{sale_id}/eligible", headers=auth_admin_a)
        assert elig_res.status_code == 200
        line_elig = elig_res.json()["lines"][0]
        assert Decimal(line_elig["prorated_discount_per_unit"]) == Decimal("20.000000")
        assert Decimal(line_elig["net_unit_price"]) == Decimal("80.000000")

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Retorno de item en promocion",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True}
        )
        assert accept_res.status_code == 200
        cn_info = accept_res.json()["credit_note"]
        assert Decimal(cn_info["subtotal_amount"]) == Decimal("160.000000")
        assert Decimal(cn_info["total_amount"]) < total


@pytest.mark.asyncio
async def test_fal022_ret011_efecto_analitico_separacion_comercial_financiera(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, total = create_test_sale(qty=Decimal("2.000000"), price=Decimal("50.000000"))
        
        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Analitica comercial vs financiera",
                "items": [{"product_id": str(prod_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True, "credit_action": "CREDIT_NOTE"}
        )
        assert accept_res.status_code == 200

        with sync_session_factory() as session:
            cn = session.scalar(select(CreditNoteModel).where(CreditNoteModel.return_id == UUID(return_id)))
            assert cn is not None
            refund_count = session.scalar(select(func.count(RefundModel.id)).where(RefundModel.company_id == COMPANY_A, RefundModel.reason == "Analitica comercial vs financiera"))
            assert refund_count == 0


@pytest.mark.asyncio
async def test_fal022_ret012_evidencia_aprobacion_trazabilidad(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, _ = create_test_sale(qty=Decimal("2.000000"), price=Decimal("40.000000"))

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Trazabilidad con evidencia fotografica",
                "evidence_urls": ["https://storage.enterprise/returns/evidencia_1.jpg", "https://storage.enterprise/returns/informe.pdf"],
                "items": [{"product_id": str(prod_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        get_res = await client.get(f"/api/v1/returns/{return_id}", headers=auth_admin_a)
        assert get_res.status_code == 200
        details = get_res.json()["details"]
        assert len(details["evidence_urls"]) == 2
        assert "requested_by" in details


@pytest.mark.asyncio
async def test_fal022_ret013_anulacion_de_solicitud_compensatoria(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, _ = create_test_sale(qty=Decimal("3.000000"), price=Decimal("50.000000"))

        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Anulacion de solicitud pendiente",
                "items": [{"product_id": str(prod_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        cancel_res = await client.post(
            f"/api/v1/returns/{return_id}/cancel",
            headers=auth_admin_a,
            json={"reason": "Cliente desiste de la devolucion"}
        )
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "cancelled"

        sale2_id, prod2_id, _ = create_test_sale(qty=Decimal("3.000000"), price=Decimal("50.000000"))
        ret2_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale2_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Aceptada no se puede anular directamente",
                "items": [{"product_id": str(prod2_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        ret2_id = ret2_res.json()["id"]
        await client.post(f"/api/v1/returns/{ret2_id}/accept", headers={**auth_admin_a, "Idempotency-Key": uuid4().hex})

        cancel_accepted = await client.post(
            f"/api/v1/returns/{ret2_id}/cancel",
            headers=auth_admin_a,
            json={"reason": "Intento ilegal de anular aceptada"}
        )
        assert cancel_accepted.status_code == 409


@pytest.mark.asyncio
async def test_fal022_ret014_experiencia_visual_estados_asistente(auth_admin_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        list_res = await client.get("/api/v1/returns", headers=auth_admin_a)
        assert list_res.status_code == 200
        assert isinstance(list_res.json(), list)


@pytest.mark.asyncio
async def test_api_061_post_returns_contracts(auth_admin_a, auth_admin_b, auth_warehouse_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_a_id, prod_a_id, _ = create_test_sale(company_id=COMPANY_A, warehouse_id=WAREHOUSE_A)
        sale_b_id, prod_b_id, _ = create_test_sale(company_id=COMPANY_B, warehouse_id=WAREHOUSE_B)

        success_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_a_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "API-061 Contrato de exito",
                "items": [{"product_id": str(prod_a_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        assert success_res.status_code == 201

        inv_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": "not-a-uuid",
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "X",
                "items": []
            }
        )
        assert inv_res.status_code == 422

        perm_res = await client.post(
            "/api/v1/returns",
            headers=auth_warehouse_a,
            json={
                "sale_id": str(sale_a_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Permiso insuficiente",
                "items": [{"product_id": str(prod_a_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        assert perm_res.status_code == 403

        other_comp_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_b_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "Ataque multi-tenant a venta de empresa rival",
                "items": [{"product_id": str(prod_a_id), "quantity": "1.000000", "disposition": "RESTOCK"}]
            }
        )
        assert other_comp_res.status_code in (403, 404, 409)


@pytest.mark.asyncio
async def test_api_062_post_returns_accept_contracts(auth_admin_a, auth_admin_b, auth_seller_a):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sale_id, prod_id, _ = create_test_sale(company_id=COMPANY_A, warehouse_id=WAREHOUSE_A)
        ret_res = await client.post(
            "/api/v1/returns",
            headers=auth_admin_a,
            json={
                "sale_id": str(sale_id),
                "warehouse_id": str(WAREHOUSE_A),
                "reason": "API-062 Preparacion de retorno",
                "items": [{"product_id": str(prod_id), "quantity": "2.000000", "disposition": "RESTOCK"}]
            }
        )
        return_id = ret_res.json()["id"]

        idem_key = uuid4().hex
        accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": idem_key},
            json={"create_credit_note": True}
        )
        assert accept_res.status_code == 200

        replay_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": idem_key},
            json={"create_credit_note": True}
        )
        assert replay_res.status_code == 200

        second_accept_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex},
            json={"create_credit_note": True}
        )
        assert second_accept_res.status_code == 409

        perm_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex}
        )
        assert perm_res.status_code in (403, 409)

        other_comp_res = await client.post(
            f"/api/v1/returns/{return_id}/accept",
            headers={**auth_admin_b, "Idempotency-Key": uuid4().hex}
        )
        assert other_comp_res.status_code in (403, 404, 409)
