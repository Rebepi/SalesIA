from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    ProductModel,
    InventoryStockModel,
    WarehouseModel,
    BranchModel,
    CustomerModel,
    SaleModel,
    UserModel
)
from salesia.modules.seguridad.infrastructure.security import (
    create_access_token,
    create_refresh_token,
    hash_password
)
from tests.support.auth_helpers import create_durable_identity

COMPANY_A_ID = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B_ID = UUID("00000000-0000-0000-0000-000000000099")
USER_A_ID = UUID("00000000-0000-0000-0000-000000000002")
USER_B_ID = UUID("00000000-0000-0000-0000-000000000098")
BRANCH_A_ID = UUID("00000000-0000-0000-0000-000000000002")
WAREHOUSE_A_ID = UUID("00000000-0000-0000-0000-000000000003")
CUSTOMER_A_ID = UUID("00000000-0000-0000-0000-000000000004")


@pytest.fixture(autouse=True, scope="module")
def setup_remediation_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp_a = session.execute(
            select(CompanyModel).where(CompanyModel.id == COMPANY_A_ID)
        ).scalar_one_or_none()
        if not comp_a:
            comp_a = CompanyModel(
                id=COMPANY_A_ID,
                tax_id="20100000001",
                legal_name="EMPRESA A AUDITORIA S.A.",
                trade_name="EMPRESA A",
                base_currency="USD",
                is_active=True
            )
            session.add(comp_a)

        comp_b = session.execute(
            select(CompanyModel).where(CompanyModel.id == COMPANY_B_ID)
        ).scalar_one_or_none()
        if not comp_b:
            comp_b = CompanyModel(
                id=COMPANY_B_ID,
                tax_id="20100000099",
                legal_name="EMPRESA B AUDITORIA S.A.",
                trade_name="EMPRESA B",
                base_currency="USD",
                is_active=True
            )
            session.add(comp_b)

        branch_a = session.execute(
            select(BranchModel).where(BranchModel.id == BRANCH_A_ID)
        ).scalar_one_or_none()
        if not branch_a:
            branch_a = BranchModel(
                id=BRANCH_A_ID,
                company_id=COMPANY_A_ID,
                code="BR-01",
                name="Sucursal Principal",
                timezone="UTC",
                is_active=True
            )
            session.add(branch_a)

        wh_a = session.execute(
            select(WarehouseModel).where(WarehouseModel.id == WAREHOUSE_A_ID)
        ).scalar_one_or_none()
        if not wh_a:
            wh_a = WarehouseModel(
                id=WAREHOUSE_A_ID,
                company_id=COMPANY_A_ID,
                branch_id=BRANCH_A_ID,
                code="WH-01",
                name="Almacén Central",
                is_active=True
            )
            session.add(wh_a)

        cust_a = session.execute(
            select(CustomerModel).where(CustomerModel.id == CUSTOMER_A_ID)
        ).scalar_one_or_none()
        if not cust_a:
            cust_a = CustomerModel(
                id=CUSTOMER_A_ID,
                company_id=COMPANY_A_ID,
                code="CUST-001",
                doc_type="RUC",
                doc_number="20555555555",
                legal_name="CLIENTE CORPORATIVO 1",
                credit_limit=Decimal("5000.000000"),
                current_balance=Decimal("0.000000")
            )
            session.add(cust_a)

        session.commit()
    yield


@pytest.fixture
def auth_headers_admin_a():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            user_id=USER_A_ID,
            role="company_admin",
            email="admin@salesia.enterprise",
            password="SuperSecretSecurePassword2026!"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_sales_a():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            user_id=UUID("00000000-0000-0000-0000-000000000004"),
            role="salesperson",
            email="vendedor@empresa.com",
            password="SuperSecretSecurePassword2026!"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_admin_b():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_B_ID,
            user_id=USER_B_ID,
            role="company_admin",
            email="admin@empresa-b.com",
            password="SuperSecretSecurePassword2026!"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_platform():
    with sync_session_factory() as session:
        identity = create_durable_identity(
            session,
            company_id=COMPANY_A_ID,
            role="platform_admin",
            email="platform@salesia.enterprise",
            password="SuperSecretSecurePassword2026!"
        )
        return identity["headers"]


@pytest.mark.asyncio
async def test_case_1_login_invalid_credentials_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": f"noexiste_{uuid4().hex}@empresa.com", "password": "password123"}
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_case_2_refresh_token_cannot_be_used_as_bearer_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        refresh_token = create_refresh_token(
            user_id=USER_A_ID,
            email="admin@salesia.enterprise",
            company_id=COMPANY_A_ID,
            role="company_admin"
        )
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_case_3_auth_refresh_rotates_and_detects_reuse(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@salesia.enterprise", "password": "SuperSecretSecurePassword2026!"}
        )
        assert login_res.status_code == 200
        refresh_token = login_res.json()["refresh_token"]

        res_refresh = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert res_refresh.status_code == 200
        data = res_refresh.json()
        assert "access_token" in data
        assert "refresh_token" in data

        res_reuse = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert res_reuse.status_code == 401


@pytest.mark.asyncio
async def test_case_4_token_revocation_after_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@salesia.enterprise", "password": "SuperSecretSecurePassword2026!"}
        )
        assert login_res.status_code == 200
        access_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        res_me_before = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me_before.status_code == 200

        res_logout = await client.post("/api/v1/auth/logout", headers=headers)
        assert res_logout.status_code == 200

        res_me_after = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me_after.status_code == 401


@pytest.mark.asyncio
async def test_case_5_mfa_invalid_string_rejected(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_alpha = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "abcdef"},
            headers=auth_headers_admin_a
        )
        assert res_alpha.status_code == 400

        res_wrong_numeric = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": "000000"},
            headers=auth_headers_admin_a
        )
        assert res_wrong_numeric.status_code == 400


@pytest.mark.asyncio
async def test_case_6_password_reset_invalid_token_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_fake_token = await client.post(
            "/api/v1/auth/password/reset",
            json={"reset_token": "token_completamente_falso_123456", "new_password": "NewValidPassword2026!"}
        )
        assert res_fake_token.status_code == 401


@pytest.mark.asyncio
async def test_case_7_create_sale_without_session_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "company_id": str(COMPANY_A_ID),
            "currency": "USD",
            "lines": [
                {
                    "sku": "SKU-TEST-001",
                    "product_name": "Producto Prueba",
                    "quantity": 1,
                    "unit_price": "100.00"
                }
            ]
        }
        res = await client.post("/api/v1/sales/draft", json=payload)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_case_8_confirm_sale_twice_idempotent(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    prod_id = uuid4()
    with sync_session_factory() as session:
        prod = ProductModel(
            id=prod_id,
            company_id=COMPANY_A_ID,
            sku=f"SKU-IDEM-{uuid4().hex[:6]}",
            name="Articulo Idempotencia",
            category="GENERAL",
            unit_of_measure="NIU",
            unit_price=Decimal("50.000000"),
            unit_cost=Decimal("30.000000"),
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(prod)
        stock = InventoryStockModel(
            id=uuid4(),
            company_id=COMPANY_A_ID,
            warehouse_id=WAREHOUSE_A_ID,
            product_id=prod_id,
            physical_quantity=Decimal("10.000000"),
            reserved_quantity=Decimal("0.000000")
        )
        session.add(stock)
        session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_res = await client.post(
            "/api/v1/sales/draft",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A_ID),
                "customer_id": str(CUSTOMER_A_ID),
                "warehouse_id": str(WAREHOUSE_A_ID),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(prod_id),
                        "sku": "SKU-IDEM",
                        "product_name": "Articulo Idempotencia",
                        "quantity": 1,
                        "unit_price": "50.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert draft_res.status_code == 201
        sale_id = draft_res.json()["sale_id"]

        confirm_key = uuid4().hex
        confirm_1 = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_admin_a, "Idempotency-Key": confirm_key}
        )
        assert confirm_1.status_code == 200

        with sync_session_factory() as session:
            stock_after_1 = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == COMPANY_A_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stock_after_1.physical_quantity == Decimal("9.000000")

        confirm_2 = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_admin_a, "Idempotency-Key": confirm_key}
        )
        assert confirm_2.status_code == 200

        with sync_session_factory() as session:
            stock_after_2 = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == COMPANY_A_ID,
                    InventoryStockModel.product_id == prod_id
                )
            ).scalar_one()
            assert stock_after_2.physical_quantity == Decimal("9.000000")


@pytest.mark.asyncio
async def test_case_9_payment_currency_mismatch_and_overpayment_rejected(auth_headers_admin_a, auth_headers_sales_a):
    sale_id = uuid4()
    with sync_session_factory() as session:
        sale = SaleModel(
            id=sale_id,
            company_id=COMPANY_A_ID,
            branch_id=BRANCH_A_ID,
            customer_id=CUSTOMER_A_ID,
            series=f"S{uuid4().hex[:3].upper()}",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("100.000000"),
            tax_amount=Decimal("0.000000"),
            total_amount=Decimal("100.000000"),
            paid_amount=Decimal("0.000000")
        )
        session.add(sale)
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_no_perm = await client.post(
            "/api/v1/payments",
            headers={**auth_headers_sales_a, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "CASH",
                "amount": "50.00",
                "currency": "USD"
            }
        )
        assert res_no_perm.status_code == 403

        res_diff_curr = await client.post(
            "/api/v1/payments",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "TRANSFER",
                "reference_code": "TRF-001",
                "amount": "100.00",
                "currency": "EUR"
            }
        )
        assert res_diff_curr.status_code in (400, 422)

        res_overpay = await client.post(
            "/api/v1/payments",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "CASH",
                "amount": "150.00",
                "currency": "USD"
            }
        )
        assert res_overpay.status_code in (400, 409)


@pytest.mark.asyncio
async def test_case_10_refund_excess_amount_rejected(auth_headers_admin_a):
    sale_id = uuid4()
    with sync_session_factory() as session:
        sale = SaleModel(
            id=sale_id,
            company_id=COMPANY_A_ID,
            branch_id=BRANCH_A_ID,
            customer_id=CUSTOMER_A_ID,
            series=f"S{uuid4().hex[:3].upper()}",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("150.000000"),
            tax_amount=Decimal("0.000000"),
            total_amount=Decimal("150.000000"),
            paid_amount=Decimal("0.000000")
        )
        session.add(sale)
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pay_res = await client.post(
            "/api/v1/payments",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "sale_id": str(sale_id),
                "payment_method": "CASH",
                "amount": "150.00",
                "currency": "USD"
            }
        )
        assert pay_res.status_code == 201
        payment_id = pay_res.json().get("payment_id") or pay_res.json().get("id")

        refund_res = await client.post(
            "/api/v1/refunds",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex},
            json={
                "payment_id": payment_id,
                "amount": "999.00",
                "reason": "Exceso de devolucion"
            }
        )
        assert refund_res.status_code in (400, 409)


@pytest.mark.asyncio
async def test_case_11_random_job_not_found(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/jobs/{uuid4()}",
            headers=auth_headers_admin_a
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_case_12_confirm_nonexistent_order_rejected(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/orders/{uuid4()}/confirm",
            headers={**auth_headers_admin_a, "Idempotency-Key": uuid4().hex}
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_case_13_complete_unuploaded_attachment_rejected(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_missing = await client.post(
            f"/api/v1/attachments/{uuid4()}/complete",
            headers=auth_headers_admin_a
        )
        assert res_missing.status_code == 404

        intent_res = await client.post(
            "/api/v1/attachments/upload-intents",
            headers=auth_headers_admin_a,
            json={
                "file_name": "contrato.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 1024,
                "related_entity_type": "import"
            }
        )
        assert intent_res.status_code == 201
        intent_id = intent_res.json()["attachment_id"]

        res_unuploaded = await client.post(
            f"/api/v1/attachments/{intent_id}/complete",
            headers=auth_headers_admin_a
        )
        assert res_unuploaded.status_code in (400, 409)


@pytest.mark.asyncio
async def test_case_14_payment_webhook_without_signature_rejected(auth_headers_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        conn_res = await client.post(
            "/api/v1/payment-connections",
            headers=auth_headers_admin_a,
            json={"provider": "custom"}
        )
        assert conn_res.status_code == 201
        conn_id = conn_res.json()["connection_id"]

        res_no_sig = await client.post(
            f"/api/v1/webhooks/payments/{conn_id}",
            json={"event": "charge.success", "amount": 100}
        )
        assert res_no_sig.status_code == 401

        res_bad_sig = await client.post(
            f"/api/v1/webhooks/payments/{conn_id}",
            headers={"X-Webhook-Signature": "sha256=invalidsignature"},
            json={"event": "charge.success", "amount": 100}
        )
        assert res_bad_sig.status_code == 401


@pytest.mark.asyncio
async def test_case_15_trigger_backup_without_session_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/operations/backup/trigger")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_case_16_restore_nonexistent_snapshot_rejected(auth_headers_platform):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_checksum = "a" * 64
        res = await client.post(
            "/api/v1/operations/restore/verify",
            headers=auth_headers_platform,
            json={
                "snapshot_id": str(uuid4()),
                "checksum": fake_checksum
            }
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_case_17_cross_tenant_sale_access_forbidden(auth_headers_admin_a, auth_headers_admin_b):
    sale_id = uuid4()
    with sync_session_factory() as session:
        sale = SaleModel(
            id=sale_id,
            company_id=COMPANY_A_ID,
            branch_id=BRANCH_A_ID,
            customer_id=CUSTOMER_A_ID,
            series=f"S{uuid4().hex[:3].upper()}",
            number=int(uuid4().int % 900000 + 100000),
            status="draft",
            currency="USD",
            subtotal_amount=Decimal("100.000000"),
            tax_amount=Decimal("18.000000"),
            total_amount=Decimal("118.000000"),
            paid_amount=Decimal("0.000000")
        )
        session.add(sale)
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_same_tenant = await client.get(
            f"/api/v1/sales/{sale_id}",
            headers=auth_headers_admin_a
        )
        assert res_same_tenant.status_code == 200

        res_cross_get = await client.get(
            f"/api/v1/sales/{sale_id}",
            headers=auth_headers_admin_b
        )
        assert res_cross_get.status_code in (403, 404)

        res_cross_confirm = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**auth_headers_admin_b, "Idempotency-Key": uuid4().hex}
        )
        assert res_cross_confirm.status_code in (403, 404)
