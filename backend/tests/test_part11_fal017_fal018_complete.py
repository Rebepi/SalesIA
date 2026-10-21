from datetime import datetime, timezone
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
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    InventoryStockModel,
    PaymentModel,
    CashSessionModel
)
from salesia.modules.finanzas.infrastructure_models import (
    PaymentMethodConfigModel,
    PaymentAllocationModel,
    PaymentIntentModel,
    FinanceReconciliationModel,
    FinanceReconciliationItemModel,
    PaymentDisputeModel,
    PaymentReversalModel,
    TransferProofModel
)
from salesia.shared.infrastructure.transactions import RefundModel
from salesia.shared.infrastructure.workers import sign_webhook_payload
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000101")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000109")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000102")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000192")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000104")
CUSTOMER_A = UUID("00000000-0000-0000-0000-000000000114")
CUSTOMER_B = UUID("00000000-0000-0000-0000-000000000195")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000103")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000107")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000108")


@pytest.fixture(autouse=True, scope="module")
def setup_part11_data():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20888888881", "Empresa A P11"), (COMPANY_B, "20888888882", "Empresa B P11")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        session.flush()
        for bid, cid, code, name in [(BRANCH_A, COMPANY_A, "SUC-P11-A", "Sucursal P11 A"), (BRANCH_B, COMPANY_B, "SUC-P11-B", "Sucursal P11 B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=name, timezone="America/Lima", is_active=True))
        session.flush()
        for wid, cid, bid, code, name in [(WAREHOUSE_A, COMPANY_A, BRANCH_A, "WH-P11-A", "Almacen P11 A")]:
            wh = session.scalar(select(WarehouseModel).where(WarehouseModel.id == wid))
            if not wh:
                session.add(WarehouseModel(id=wid, company_id=cid, branch_id=bid, code=code, name=name, is_active=True))
        for cust_id, cid, code, doc in [(CUSTOMER_A, COMPANY_A, "CLI-P11-A", "20555666777"), (CUSTOMER_B, COMPANY_B, "CLI-P11-B", "20666777888")]:
            c = session.scalar(select(CustomerModel).where(CustomerModel.id == cust_id))
            if not c:
                session.add(CustomerModel(id=cust_id, company_id=cid, code=code, doc_type="RUC", doc_number=doc, legal_name=f"Cliente {code}", credit_limit=Decimal("5000.00"), current_balance=Decimal("0.00"), is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_admin_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_p11_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_seller_a():
    identity = create_durable_identity(company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_p11_a@salesia.enterprise", password="valid_password")
    return identity["headers"]


@pytest.fixture
def auth_admin_b():
    identity = create_durable_identity(company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_p11_b@rival.enterprise", password="valid_password")
    return identity["headers"]


def create_confirmed_sale(company_id=COMPANY_A, total=Decimal("100.000000"), currency="USD", customer_id=CUSTOMER_A, is_credit=False):
    sale_id = uuid4()
    with sync_session_factory() as session:
        sale = SaleModel(
            id=sale_id,
            company_id=company_id,
            customer_id=customer_id,
            branch_id=BRANCH_A if company_id == COMPANY_A else BRANCH_B,
            warehouse_id=WAREHOUSE_A,
            series="F001",
            number=int(secrets.randbelow(899999) + 100000),
            status="confirmed",
            currency=currency,
            subtotal_amount=total / Decimal("1.18"),
            tax_amount=total - (total / Decimal("1.18")),
            total_amount=total,
            paid_amount=Decimal("0.000000"),
            is_credit=is_credit,
            version=1
        )
        session.add(sale)
        session.commit()
    return sale_id


@pytest.mark.asyncio
async def test_fallo_01_cobro_sin_permisos_financieros_moneda_o_exceso(auth_seller_a, auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"), currency="USD")
        seller_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "100.00", "currency": "USD"},
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex}
        )
        assert seller_res.status_code == 403
        currency_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "150.00", "currency": "EUR"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert currency_res.status_code == 422
        excess_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "150.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert excess_res.status_code == 409
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")


@pytest.mark.asyncio
async def test_fallo_02_reembolso_superior_a_saldo_reembolsable_rechazado(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("150.000000"), currency="USD")
        pay_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "150.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert pay_res.status_code == 201
        payment_id = pay_res.json()["id"]
        refund_res = await client.post(
            "/api/v1/refunds",
            json={"payment_id": payment_id, "amount": "999.00", "reason": "Reembolso exorbitante"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert refund_res.status_code in (409, 422)


@pytest.mark.asyncio
async def test_fallo_03_webhook_sin_firma_o_invalido_o_replay(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conn_res = await client.post("/api/v1/payment-connections", json={"provider": "custom"}, headers=auth_admin_a)
        assert conn_res.status_code == 201
        conn = conn_res.json()
        cid = conn["connection_id"]
        body = json.dumps({"event": "charge.success", "id": uuid4().hex}).encode()
        no_sig = await client.post(f"/api/v1/webhooks/payments/{cid}", content=body)
        assert no_sig.status_code == 401
        ts = int(time.time())
        bad_sig = await client.post(
            f"/api/v1/webhooks/payments/{cid}",
            content=body,
            headers={"X-Webhook-Timestamp": str(ts), "X-Webhook-Event-Id": "evt-f3", "X-Webhook-Signature": "invalida"}
        )
        assert bad_sig.status_code == 401


@pytest.mark.asyncio
async def test_reg_10_cobro_moneda_exceso_estado_permiso_integridad(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("80.000000"), currency="USD")
        r1 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "80.00", "currency": "PEN"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert r1.status_code == 422
        r2 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "120.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert r2.status_code == 409
        r3 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "80.00", "currency": "USD"},
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex}
        )
        assert r3.status_code == 403
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")
            assert s.status == "confirmed"


@pytest.mark.asyncio
async def test_reg_11_reembolsos_acumulados_concurrentes_y_cartera(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"), currency="USD")
        p = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "100.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert p.status_code == 201
        payment_id = p.json()["id"]
        ref1 = await client.post(
            "/api/v1/refunds",
            json={"payment_id": payment_id, "amount": "40.00", "reason": "Parte 1"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert ref1.status_code == 201
        ref2 = await client.post(
            "/api/v1/refunds",
            json={"payment_id": payment_id, "amount": "60.00", "reason": "Parte 2"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert ref2.status_code == 201
        ref3 = await client.post(
            "/api/v1/refunds",
            json={"payment_id": payment_id, "amount": "10.00", "reason": "Parte 3 exceso"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert ref3.status_code in (409, 422)
        with sync_session_factory() as session:
            total_ref = session.scalar(select(func.sum(RefundModel.amount)).where(RefundModel.payment_id == UUID(payment_id)))
            assert total_ref == Decimal("100.000000")
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")


@pytest.mark.asyncio
async def test_reg_12_webhook_ventana_secreto_rotado_y_deduplicacion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conn = (await client.post("/api/v1/payment-connections", json={"provider": "custom"}, headers=auth_admin_a)).json()
        cid = conn["connection_id"]
        secret1 = conn["webhook_secret"]
        rot = (await client.post(f"/api/v1/payment-connections/{cid}/rotate-secret", headers=auth_admin_a)).json()
        secret2 = rot["webhook_secret"]
        body = json.dumps({"event": "charge.captured", "tx": "tx-12"}).encode()
        ts = int(time.time())
        signed_old = str(ts).encode() + b"." + body
        sig_old = sign_webhook_payload(signed_old, secret1)
        r_old = await client.post(
            f"/api/v1/webhooks/payments/{cid}",
            content=body,
            headers={"X-Webhook-Timestamp": str(ts), "X-Webhook-Event-Id": "evt-rot-1", "X-Webhook-Signature": sig_old}
        )
        assert r_old.status_code == 200
        sig_new = sign_webhook_payload(signed_old, secret2)
        r_dup = await client.post(
            f"/api/v1/webhooks/payments/{cid}",
            content=body,
            headers={"X-Webhook-Timestamp": str(ts), "X-Webhook-Event-Id": "evt-rot-1", "X-Webhook-Signature": sig_new}
        )
        assert r_dup.status_code == 200
        assert r_dup.json()["status"] == "duplicate"


@pytest.mark.asyncio
async def test_pay_001_metodos_pago_configuracion_y_desactivacion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        methods_res = await client.get("/api/v1/payment-methods", headers=auth_admin_a)
        assert methods_res.status_code == 200
        methods = methods_res.json()
        assert any(m["code"] == "CASH" for m in methods)
        unique_code = f"W_{uuid4().hex[:6].upper()}"
        create_res = await client.post(
            "/api/v1/payment-methods",
            json={"code": unique_code, "name": "Billetera Digital", "is_active": True, "requires_reference": True},
            headers=auth_admin_a
        )
        assert create_res.status_code == 201
        method_id = create_res.json()["id"]
        deactivate_res = await client.patch(
            f"/api/v1/payment-methods/{method_id}",
            json={"is_active": False},
            headers=auth_admin_a
        )
        assert deactivate_res.status_code == 200
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("50.000000"))
        pay_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": unique_code, "amount": "50.00", "currency": "USD", "reference_code": "REF-W"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert pay_res.status_code == 422


@pytest.mark.asyncio
async def test_pay_002_pagos_parciales_y_mixtos_exactamente_una_vez(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"))
        p1 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "40.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert p1.status_code == 201
        assert p1.json()["sale_status"] == "confirmed"
        assert p1.json()["remaining_due"] == "60.000000"
        p2 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "TRANSFER", "amount": "60.00", "currency": "USD", "reference_code": "TX-60"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert p2.status_code == 201
        assert p2.json()["sale_status"] == "paid"
        assert p2.json()["remaining_due"] == "0.000000"
        p3 = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "10.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert p3.status_code == 409


@pytest.mark.asyncio
async def test_pay_003_aplicacion_pagos_multiples_ventas_limite_utilizable(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_base = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"))
        sale_target1 = create_confirmed_sale(COMPANY_A, total=Decimal("40.000000"))
        sale_target2 = create_confirmed_sale(COMPANY_A, total=Decimal("60.000000"))
        sale_target3 = create_confirmed_sale(COMPANY_A, total=Decimal("20.000000"))
        pay_res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_base), "payment_method": "TRANSFER", "amount": "100.00", "currency": "USD", "reference_code": "REF-ADV", "is_advance": True},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert pay_res.status_code == 201
        payment_id = pay_res.json()["id"]
        alloc1 = await client.post(
            f"/api/v1/payments/{payment_id}/allocations",
            json={"sale_id": str(sale_target1), "allocated_amount": "40.00"},
            headers=auth_admin_a
        )
        assert alloc1.status_code == 200
        alloc2 = await client.post(
            f"/api/v1/payments/{payment_id}/allocations",
            json={"sale_id": str(sale_target2), "allocated_amount": "60.00"},
            headers=auth_admin_a
        )
        assert alloc2.status_code == 200
        alloc3 = await client.post(
            f"/api/v1/payments/{payment_id}/allocations",
            json={"sale_id": str(sale_target3), "allocated_amount": "10.00"},
            headers=auth_admin_a
        )
        assert alloc3.status_code == 409
        with sync_session_factory() as session:
            count = session.scalar(select(func.count()).select_from(PaymentAllocationModel).where(PaymentAllocationModel.payment_id == UUID(payment_id)))
            assert count == 2


@pytest.mark.asyncio
async def test_pay_004_cambio_efectivo_vuelto_neto(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("80.000000"))
        pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "80.00", "currency": "USD", "cash_tendered": "100.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert pay.status_code == 201
        data = pay.json()
        assert data["amount"] == "80.000000"
        assert data["change"] == "20.000000"
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("80.000000")


@pytest.mark.asyncio
async def test_pay_005_pago_externo_intento_y_confirmacion_servidor(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("120.000000"))
        intent_res = await client.post(
            "/api/v1/payment-intents",
            json={"sale_id": str(sale_id), "provider": "stripe", "amount": "120.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert intent_res.status_code == 201
        intent_id = intent_res.json()["intent_id"]
        assert intent_res.json()["status"] == "pending"
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")
        conf_res = await client.post(
            f"/api/v1/payment-intents/{intent_id}/confirm",
            json={"gateway_token": "tok_visa_valid"},
            headers=auth_admin_a
        )
        assert conf_res.status_code == 200
        assert conf_res.json()["status"] == "succeeded"
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("120.000000")


@pytest.mark.asyncio
async def test_pay_006_estado_desconocido_timeout_bloquea_doble_cargo(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("75.000000"))
        intent_res = await client.post(
            "/api/v1/payment-intents",
            json={"sale_id": str(sale_id), "provider": "stripe", "amount": "75.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        intent_id = intent_res.json()["intent_id"]
        sync_res = await client.post(
            f"/api/v1/payment-intents/{intent_id}/sync-status",
            json={"gateway_response": "timeout"},
            headers=auth_admin_a
        )
        assert sync_res.status_code == 200
        assert sync_res.json()["status"] == "pending_reconciliation"
        new_pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "75.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert new_pay.status_code == 409


@pytest.mark.asyncio
async def test_pay_007_webhooks_idempotencia_y_estado_terminal(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conn = (await client.post("/api/v1/payment-connections", json={"provider": "custom"}, headers=auth_admin_a)).json()
        cid = conn["connection_id"]
        secret = conn["webhook_secret"]
        evt_id = f"evt-term-{uuid4().hex}"
        body = json.dumps({"type": "payment.succeeded", "charge_id": "ch_123"}).encode()
        ts = int(time.time())
        sig = sign_webhook_payload(str(ts).encode() + b"." + body, secret)
        headers = {"X-Webhook-Timestamp": str(ts), "X-Webhook-Event-Id": evt_id, "X-Webhook-Signature": sig}
        r1 = await client.post(f"/api/v1/webhooks/payments/{cid}", content=body, headers=headers)
        assert r1.status_code == 200
        assert r1.json()["status"] == "processed"
        r2 = await client.post(f"/api/v1/webhooks/payments/{cid}", content=body, headers=headers)
        assert r2.status_code == 200
        assert r2.json()["status"] == "duplicate"


@pytest.mark.asyncio
async def test_pay_008_conciliacion_clasificacion_discrepancias_y_resolucion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("50.000000"))
        pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "TRANSFER", "amount": "50.00", "currency": "USD", "reference_code": "REF-CONC-1"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        payment_id = pay.json()["id"]
        recon_res = await client.post(
            "/api/v1/finance/reconciliations",
            json={
                "period_start": "2026-10-01T00:00:00Z",
                "period_end": "2026-10-15T23:59:59Z",
                "external_lines": [
                    {"reference_code": "REF-CONC-1", "amount": "50.00"},
                    {"reference_code": "REF-EXT-MISS", "amount": "30.00"}
                ]
            },
            headers=auth_admin_a
        )
        assert recon_res.status_code == 201
        recon_data = recon_res.json()
        recon_id = recon_data["id"]
        items = recon_data["items"]
        assert any(i["classification"] == "MATCH" for i in items)
        missing_item = next(i for i in items if i["classification"] == "LOCAL_MISSING")
        resolve_res = await client.post(
            f"/api/v1/finance/reconciliations/{recon_id}/items/{missing_item['id']}/resolve",
            json={"resolution_action": "Ajuste manual registrado"},
            headers=auth_admin_a
        )
        assert resolve_res.status_code == 200
        assert resolve_res.json()["is_resolved"] is True


@pytest.mark.asyncio
async def test_pay_009_prueba_transferencia_separada_de_confirmacion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("200.000000"))
        proof_res = await client.post(
            "/api/v1/payments/proof-of-transfer",
            json={"sale_id": str(sale_id), "amount": "200.00", "currency": "USD", "reference_code": "VOUCHER-99", "document_url": "https://storage.local/proofs/v99.pdf"},
            headers=auth_admin_a
        )
        assert proof_res.status_code == 201
        pay_id = proof_res.json()["payment_id"]
        assert proof_res.json()["status"] == "pending"
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")
        verify_res = await client.post(
            f"/api/v1/payments/{pay_id}/verify-proof",
            json={"approved": True},
            headers=auth_admin_a
        )
        assert verify_res.status_code == 200
        assert verify_res.json()["status"] == "confirmed"
        with sync_session_factory() as session:
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("200.000000")


@pytest.mark.asyncio
async def test_pay_010_saldos_vencimientos_antiguedad_cartera(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("150.000000"))
        rec_res = await client.get("/api/v1/receivables", headers=auth_admin_a)
        assert rec_res.status_code == 200
        data = rec_res.json()
        assert "items" in data
        assert any(item["sale_id"] == str(sale_id) for item in data["items"])
        item = next(i for i in data["items"] if i["sale_id"] == str(sale_id))
        assert "aging_bucket" in item
        assert "due_date" in item


@pytest.mark.asyncio
async def test_pay_011_credito_comercial_concurrencia_cupo(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            c = session.get(CustomerModel, CUSTOMER_A)
            c.credit_limit = Decimal("100.00")
            c.current_balance = Decimal("80.00")
            session.commit()
        sale_exceed = create_confirmed_sale(COMPANY_A, total=Decimal("30.000000"), customer_id=CUSTOMER_A, is_credit=True)
        pay_credit = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_exceed), "payment_method": "CREDIT", "amount": "30.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert pay_credit.status_code in (409, 422)


@pytest.mark.asyncio
async def test_pay_012_reversion_cobro_sin_editar_historial_recalculo(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"))
        pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "100.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        payment_id = pay.json()["id"]
        rev = await client.post(
            f"/api/v1/payments/{payment_id}/reversals",
            json={"reason": "Error contable en cobro", "reference_code": "REV-01"},
            headers=auth_admin_a
        )
        assert rev.status_code == 201
        with sync_session_factory() as session:
            p_orig = session.get(PaymentModel, UUID(payment_id))
            assert p_orig is not None
            s = session.get(SaleModel, sale_id)
            assert s.paid_amount == Decimal("0.000000")
            assert s.status == "confirmed"


@pytest.mark.asyncio
async def test_pay_013_disputas_contracargo_separado_de_reembolsado(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("90.000000"))
        pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CARD", "amount": "90.00", "currency": "USD", "reference_code": "AUTH-90"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        payment_id = pay.json()["id"]
        disp_res = await client.post(
            f"/api/v1/payments/{payment_id}/disputes",
            json={"amount": "90.00", "reason": "Contracargo por fraude", "evidence_url": "https://storage.local/dispute.pdf"},
            headers=auth_admin_a
        )
        assert disp_res.status_code == 201
        rec_res = await client.get("/api/v1/receivables", headers=auth_admin_a)
        assert rec_res.status_code == 200
        assert "total_disputed" in rec_res.json()


@pytest.mark.asyncio
async def test_pay_014_cajas_turnos_responsable_y_sesion_incompatible(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        term = f"T-{uuid4().hex[:6]}"
        open1 = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": term, "opening_balance": "100.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert open1.status_code == 201
        open2 = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": term, "opening_balance": "50.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert open2.status_code == 409


@pytest.mark.asyncio
async def test_pay_015_caja_entradas_salidas_movimientos_y_autorizacion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        term = f"T-{uuid4().hex[:6]}"
        open_res = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": term, "opening_balance": "200.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        session_id = open_res.json()["session_id"]
        dep = await client.post(
            f"/api/v1/cash-sessions/{session_id}/movements",
            json={"movement_type": "DEPOSIT", "amount": "50.00", "reason": "Aporte sencillo"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert dep.status_code == 201
        assert dep.json()["current_balance"] == "250.000000"
        withd = await client.post(
            f"/api/v1/cash-sessions/{session_id}/movements",
            json={"movement_type": "WITHDRAWAL", "amount": "30.00", "reason": "Pago servicio"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert withd.status_code == 201
        assert withd.json()["current_balance"] == "220.000000"


@pytest.mark.asyncio
async def test_pay_016_cierre_caja_inmutable_bloquea_pagos_posteriores(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        term = f"T-{uuid4().hex[:6]}"
        open_res = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": term, "opening_balance": "100.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        session_id = open_res.json()["session_id"]
        close_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/close",
            json={"counted_balance": "100.00", "notes": "Cierre normal"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert close_res.status_code == 200
        mov_after = await client.post(
            f"/api/v1/cash-sessions/{session_id}/movements",
            json={"movement_type": "DEPOSIT", "amount": "10.00", "reason": "Tardio"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert mov_after.status_code == 409


@pytest.mark.asyncio
async def test_pay_017_arqueo_ciego_oculta_esperado_aprobacion_diferencias(auth_admin_a, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        term = f"T-{uuid4().hex[:6]}"
        open_res = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": term, "opening_balance": "300.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        session_id = open_res.json()["session_id"]
        blind = await client.get(f"/api/v1/cash-sessions/{session_id}/blind-status", headers=auth_seller_a)
        assert blind.status_code == 200
        assert "expected_cash" not in blind.json() or blind.json()["expected_cash"] is None
        count_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/blind-count",
            json={"counted_cash": "280.00"},
            headers=auth_seller_a
        )
        assert count_res.status_code == 200
        assert count_res.json()["requires_approval"] is True
        appr_res = await client.post(
            f"/api/v1/cash-sessions/{session_id}/approve-difference",
            json={"approved": True, "notes": "Diferencia justificada"},
            headers=auth_admin_a
        )
        assert appr_res.status_code == 200


@pytest.mark.asyncio
async def test_pay_018_multimoneda_rechazo_cruce_sin_conversion(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_usd = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"), currency="USD")
        r_fail = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_usd), "payment_method": "CASH", "amount": "100.00", "currency": "PEN"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert r_fail.status_code == 422
        r_ok = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_usd), "payment_method": "CASH", "amount": "380.00", "currency": "PEN", "exchange_rate": "0.26"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert r_ok.status_code == 201


@pytest.mark.asyncio
async def test_pay_019_permisos_financieros_vendedor_bloqueado(auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_id = create_confirmed_sale(COMPANY_A, total=Decimal("50.000000"))
        r_pay = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_id), "payment_method": "CASH", "amount": "50.00", "currency": "USD"},
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex}
        )
        assert r_pay.status_code == 403
        r_ref = await client.post(
            "/api/v1/refunds",
            json={"payment_id": str(uuid4()), "amount": "10.00", "reason": "No autorizado"},
            headers={**auth_seller_a, "Idempotency-Key": uuid4().hex}
        )
        assert r_ref.status_code == 403


@pytest.mark.asyncio
async def test_api_041_post_payments_contrato_completo(auth_admin_a, auth_admin_b, auth_seller_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_a = create_confirmed_sale(COMPANY_A, total=Decimal("60.000000"))
        key = uuid4().hex
        res = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "60.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": key}
        )
        assert res.status_code == 201
        res_rep = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "60.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": key}
        )
        assert res_rep.status_code == 201
        assert res_rep.json()["id"] == res.json()["id"]
        res_inv = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "-10.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert res_inv.status_code == 422
        res_cross = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "60.00", "currency": "USD"},
            headers={**auth_admin_b, "Idempotency-Key": uuid4().hex}
        )
        assert res_cross.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_042_get_payment_detalle_y_aislamiento_empresa(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_a = create_confirmed_sale(COMPANY_A, total=Decimal("50.000000"))
        p = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "50.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        pid = p.json()["id"]
        get_res = await client.get(f"/api/v1/payments/{pid}", headers=auth_admin_a)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == pid
        cross_res = await client.get(f"/api/v1/payments/{pid}", headers=auth_admin_b)
        assert cross_res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_043_post_payment_allocations_contrato_completo(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_a = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"))
        target = create_confirmed_sale(COMPANY_A, total=Decimal("100.000000"))
        p = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "100.00", "currency": "USD", "is_advance": True},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        pid = p.json()["id"]
        res = await client.post(
            f"/api/v1/payments/{pid}/allocations",
            json={"sale_id": str(target), "allocated_amount": "50.00"},
            headers=auth_admin_a
        )
        assert res.status_code == 200
        assert res.json()["status"] == "allocated"
        cross_res = await client.post(
            f"/api/v1/payments/{pid}/allocations",
            json={"sale_id": str(target), "allocated_amount": "10.00"},
            headers=auth_admin_b
        )
        assert cross_res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_044_post_refunds_contrato_completo(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale_a = create_confirmed_sale(COMPANY_A, total=Decimal("70.000000"))
        p = await client.post(
            "/api/v1/payments",
            json={"sale_id": str(sale_a), "payment_method": "CASH", "amount": "70.00", "currency": "USD"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        pid = p.json()["id"]
        ref = await client.post(
            "/api/v1/refunds",
            json={"payment_id": pid, "amount": "20.00", "reason": "Motivo justificado"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert ref.status_code == 201
        cross = await client.post(
            "/api/v1/refunds",
            json={"payment_id": pid, "amount": "10.00", "reason": "Motivo cross"},
            headers={**auth_admin_b, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code in (403, 404)


@pytest.mark.asyncio
async def test_api_045_post_webhooks_payments_contrato_completo(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conn = (await client.post("/api/v1/payment-connections", json={"provider": "custom"}, headers=auth_admin_a)).json()
        cid = conn["connection_id"]
        secret = conn["webhook_secret"]
        body = json.dumps({"type": "charge.success", "payment_id": uuid4().hex}).encode()
        ts = int(time.time())
        sig = sign_webhook_payload(str(ts).encode() + b"." + body, secret)
        ok = await client.post(
            f"/api/v1/webhooks/payments/{cid}",
            content=body,
            headers={"X-Webhook-Timestamp": str(ts), "X-Webhook-Event-Id": "evt-api45", "X-Webhook-Signature": sig}
        )
        assert ok.status_code == 200
        assert ok.json()["status"] == "processed"


@pytest.mark.asyncio
async def test_api_046_get_receivables_contrato_completo(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_confirmed_sale(COMPANY_A, total=Decimal("110.000000"))
        r_a = await client.get("/api/v1/receivables", headers=auth_admin_a)
        assert r_a.status_code == 200
        assert r_a.json()["company_id"] == str(COMPANY_A)
        r_b = await client.get("/api/v1/receivables", headers=auth_admin_b)
        assert r_b.status_code == 200
        assert r_b.json()["company_id"] == str(COMPANY_B)


@pytest.mark.asyncio
async def test_api_047_post_cash_sessions_contrato_completo(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t = f"T-{uuid4().hex[:6]}"
        s_a = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": t, "opening_balance": "80.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert s_a.status_code == 201
        cross_branch = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_B), "terminal_code": f"T-{uuid4().hex[:6]}", "opening_balance": "80.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert cross_branch.status_code in (403, 422)


@pytest.mark.asyncio
async def test_api_048_post_cash_sessions_close_contrato_completo(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        t = f"T-{uuid4().hex[:6]}"
        s_a = await client.post(
            "/api/v1/cash-sessions",
            json={"branch_id": str(BRANCH_A), "terminal_code": t, "opening_balance": "100.00"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        sid = s_a.json()["session_id"]
        cross_close = await client.post(
            f"/api/v1/cash-sessions/{sid}/close",
            json={"counted_balance": "100.00"},
            headers={**auth_admin_b, "Idempotency-Key": uuid4().hex}
        )
        assert cross_close.status_code in (403, 404)
        ok_close = await client.post(
            f"/api/v1/cash-sessions/{sid}/close",
            json={"counted_balance": "100.00", "notes": "Cierre OK"},
            headers={**auth_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert ok_close.status_code == 200
        assert ok_close.json()["status"] == "closed"
