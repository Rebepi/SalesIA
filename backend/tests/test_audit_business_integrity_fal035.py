from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, update, func
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
    UserModel,
    AuditLogModel
)
from salesia.modules.finanzas.infrastructure_models import PaymentMethodConfigModel
from salesia.modules.operaciones.infrastructure_models import LegalHold
from salesia.modules.seguridad.infrastructure.security import hash_password
from tests.support.auth_helpers import create_durable_identity

AUDIT_TEST_COMPANY_A = UUID("11111111-2222-3333-4444-555555555551")
AUDIT_TEST_COMPANY_B = UUID("11111111-2222-3333-4444-555555555552")
AUDIT_TEST_COMPANY_HOLD = UUID("11111111-2222-3333-4444-555555555553")
AUDIT_TEST_USER_A = UUID("22222222-3333-4444-5555-666666666661")
AUDIT_TEST_USER_B = UUID("22222222-3333-4444-5555-666666666662")
AUDIT_TEST_USER_HOLD = UUID("22222222-3333-4444-5555-666666666663")
AUDIT_TEST_BRANCH_A = UUID("33333333-4444-5555-6666-777777777771")
AUDIT_TEST_WAREHOUSE_A = UUID("44444444-5555-6666-7777-888888888881")
AUDIT_TEST_CUSTOMER_A = UUID("55555555-6666-7777-8888-999999999991")
AUDIT_TEST_CUSTOMER_HOLD = UUID("55555555-6666-7777-8888-999999999993")
AUDIT_TEST_PRODUCT_A = UUID("66666666-7777-8888-9999-000000000001")


@pytest.fixture(autouse=True, scope="module")
def setup_fal035_environment():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [
            (AUDIT_TEST_COMPANY_A, "20350000001", "AUDIT EMPRESA A S.A."),
            (AUDIT_TEST_COMPANY_B, "20350000002", "AUDIT EMPRESA B S.A."),
            (AUDIT_TEST_COMPANY_HOLD, "20350000003", "AUDIT EMPRESA HOLD S.A.")
        ]:
            c = session.get(CompanyModel, cid)
            if not c:
                session.add(CompanyModel(
                    id=cid,
                    tax_id=tax,
                    legal_name=name,
                    trade_name=name,
                    base_currency="USD",
                    is_active=True
                ))
        session.flush()

        for cid, uid, email, role in [
            (AUDIT_TEST_COMPANY_A, AUDIT_TEST_USER_A, "audit_admin_a@enterprise.com", "company_admin"),
            (AUDIT_TEST_COMPANY_B, AUDIT_TEST_USER_B, "audit_admin_b@enterprise.com", "company_admin"),
            (AUDIT_TEST_COMPANY_HOLD, AUDIT_TEST_USER_HOLD, "audit_admin_hold@enterprise.com", "company_admin")
        ]:
            u = session.get(UserModel, uid)
            if not u:
                session.add(UserModel(
                    id=uid,
                    company_id=cid,
                    email=email,
                    hashed_password=hash_password("ValidPassword2026!"),
                    role=role,
                    is_active=True
                ))
            else:
                u.company_id = cid
                u.email = email
                u.hashed_password = hash_password("ValidPassword2026!")
                u.role = role
                u.is_active = True

        br = session.get(BranchModel, AUDIT_TEST_BRANCH_A)
        if not br:
            session.add(BranchModel(
                id=AUDIT_TEST_BRANCH_A,
                company_id=AUDIT_TEST_COMPANY_A,
                code="BR-AUDIT-01",
                name="Sucursal Auditoria",
                timezone="UTC",
                is_active=True
            ))
        session.flush()

        wh = session.get(WarehouseModel, AUDIT_TEST_WAREHOUSE_A)
        if not wh:
            session.add(WarehouseModel(
                id=AUDIT_TEST_WAREHOUSE_A,
                company_id=AUDIT_TEST_COMPANY_A,
                branch_id=AUDIT_TEST_BRANCH_A,
                code="WH-AUDIT-01",
                name="Almacen Auditoria",
                is_active=True
            ))

        cust = session.get(CustomerModel, AUDIT_TEST_CUSTOMER_A)
        if not cust:
            session.add(CustomerModel(
                id=AUDIT_TEST_CUSTOMER_A,
                company_id=AUDIT_TEST_COMPANY_A,
                code="CUST-AUDIT-01",
                doc_type="RUC",
                doc_number="20999888777",
                legal_name="CLIENTE AUDITABLE S.A.",
                credit_limit=Decimal("10000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            ))

        cust_hold = session.get(CustomerModel, AUDIT_TEST_CUSTOMER_HOLD)
        if not cust_hold:
            session.add(CustomerModel(
                id=AUDIT_TEST_CUSTOMER_HOLD,
                company_id=AUDIT_TEST_COMPANY_HOLD,
                code="CUST-AUDIT-HOLD-01",
                doc_type="RUC",
                doc_number="20999888666",
                legal_name="CLIENTE EN DISPUTA LEGAL S.A.",
                credit_limit=Decimal("1000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            ))

        prod = session.get(ProductModel, AUDIT_TEST_PRODUCT_A)
        if not prod:
            session.add(ProductModel(
                id=AUDIT_TEST_PRODUCT_A,
                company_id=AUDIT_TEST_COMPANY_A,
                sku="SKU-AUDIT-01",
                name="Producto Para Pruebas Auditoria",
                category="General",
                unit_of_measure="NIU",
                unit_cost=Decimal("50.00"),
                unit_price=Decimal("100.00"),
                tax_rate=Decimal("0.1800"),
                is_active=True
            ))
        session.flush()

        stk = session.scalar(select(InventoryStockModel).where(
            InventoryStockModel.company_id == AUDIT_TEST_COMPANY_A,
            InventoryStockModel.product_id == AUDIT_TEST_PRODUCT_A,
            InventoryStockModel.warehouse_id == AUDIT_TEST_WAREHOUSE_A
        ))
        if not stk:
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=AUDIT_TEST_COMPANY_A,
                product_id=AUDIT_TEST_PRODUCT_A,
                warehouse_id=AUDIT_TEST_WAREHOUSE_A,
                physical_quantity=Decimal("200.00"),
                reserved_quantity=Decimal("0.00"),
                average_cost=Decimal("50.00")
            ))

        session.commit()
    yield


@pytest.fixture
def headers_company_a():
    identity = create_durable_identity(
        company_id=AUDIT_TEST_COMPANY_A,
        user_id=AUDIT_TEST_USER_A,
        role="company_admin",
        email="audit_admin_a@enterprise.com",
        password="ValidPassword2026!"
    )
    return identity["headers"]


@pytest.fixture
def headers_company_b():
    identity = create_durable_identity(
        company_id=AUDIT_TEST_COMPANY_B,
        user_id=AUDIT_TEST_USER_B,
        role="company_admin",
        email="audit_admin_b@enterprise.com",
        password="ValidPassword2026!"
    )
    return identity["headers"]


@pytest.fixture
def headers_cashier_a():
    cashier_id = UUID("22222222-3333-4444-5555-666666666669")
    identity = create_durable_identity(
        company_id=AUDIT_TEST_COMPANY_A,
        user_id=cashier_id,
        role="cashier",
        email="cashier_a@enterprise.com",
        password="ValidPassword2026!"
    )
    return identity["headers"]


@pytest.fixture
def headers_company_hold():
    identity = create_durable_identity(
        company_id=AUDIT_TEST_COMPANY_HOLD,
        user_id=AUDIT_TEST_USER_HOLD,
        role="company_admin",
        email="audit_admin_hold@enterprise.com",
        password="ValidPassword2026!"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_aud_001_critical_events_audit_coverage(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "audit_admin_a@enterprise.com", "password": "ValidPassword2026!"}
        )
        assert login_res.status_code == 200

        with sync_session_factory() as session:
            login_log = session.scalar(
                select(AuditLogModel).where(
                    AuditLogModel.company_id == AUDIT_TEST_COMPANY_A,
                    AuditLogModel.action == "LOGIN_SUCCESS"
                ).order_by(AuditLogModel.created_at.desc())
            )
            assert login_log is not None
            assert login_log.actor_email == "audit_admin_a@enterprise.com"
            assert login_log.entity_type == "User"


@pytest.mark.asyncio
async def test_aud_002_atomicity_and_commit_guarantee(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_key = f"draft-aud2-{uuid4().hex}"
        sale_res = await client.post(
            "/api/v1/sales/draft",
            json={
                "customer_id": str(AUDIT_TEST_CUSTOMER_A),
                "branch_id": str(AUDIT_TEST_BRANCH_A),
                "warehouse_id": str(AUDIT_TEST_WAREHOUSE_A),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(AUDIT_TEST_PRODUCT_A),
                        "sku": "SKU-AUDIT-01",
                        "product_name": "Producto Para Pruebas Auditoria",
                        "quantity": 2,
                        "unit_price": "100.00"
                    }
                ]
            },
            headers={**headers_company_a, "Idempotency-Key": draft_key}
        )
        assert sale_res.status_code == 201
        sale_data = sale_res.json()
        sale_id = sale_data.get("sale_id") or sale_data.get("id")

        confirm_res = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**headers_company_a, "Idempotency-Key": f"confirm-aud2-{uuid4().hex}"}
        )
        assert confirm_res.status_code == 200

        with sync_session_factory() as session:
            sale_db = session.get(SaleModel, UUID(sale_id))
            assert sale_db.status == "confirmed"
            audit_entry = session.scalar(
                select(AuditLogModel).where(
                    AuditLogModel.company_id == AUDIT_TEST_COMPANY_A,
                    AuditLogModel.entity_type == "Sale",
                    AuditLogModel.entity_id == UUID(sale_id),
                    AuditLogModel.action == "CONFIRM_SALE"
                )
            )
            assert audit_entry is not None
            assert audit_entry.actor_email == "audit_admin_a@enterprise.com"


@pytest.mark.asyncio
async def test_aud_003_diff_redaction_secrets_and_pii(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from salesia.modules.auditoria.service import record_audit_event, redact_diff
        raw_diff = {
            "password": "SecretPassword123!",
            "hashed_password": "pbkdf2_sha256$hidden",
            "token": "bearer_secret_token",
            "card_number": "4111111111111234",
            "cvv": "999",
            "safe_field": "updated_description"
        }
        redacted = redact_diff(raw_diff)
        assert redacted["password"] == "[REDACTED]"
        assert redacted["hashed_password"] == "[REDACTED]"
        assert redacted["token"] == "[REDACTED]"
        assert redacted["card_number"] == "[REDACTED]"
        assert redacted["cvv"] == "[REDACTED]"
        assert redacted["safe_field"] == "updated_description"

        with sync_session_factory() as session:
            event = record_audit_event(
                session,
                company_id=AUDIT_TEST_COMPANY_A,
                actor_id=AUDIT_TEST_USER_A,
                actor_email="audit_admin_a@enterprise.com",
                action="UPDATE_SECURITY_CREDENTIALS",
                entity_type="Customer",
                entity_id=AUDIT_TEST_CUSTOMER_A,
                diff=raw_diff,
                reason="Actualizacion con datos sensibles"
            )
            session.commit()
            loaded = session.get(AuditLogModel, event.id)
            assert loaded is not None
            assert "SecretPassword123!" not in loaded.payload_diff
            assert "4111111111111234" not in loaded.payload_diff
            assert "[REDACTED]" in loaded.payload_diff


@pytest.mark.asyncio
async def test_aud_004_correlation_propagation(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        custom_corr = f"corr-trace-{uuid4().hex[:12]}"
        res = await client.get(
            "/api/v1/audit/logs",
            headers={**headers_company_a, "X-Correlation-ID": custom_corr}
        )
        assert res.status_code == 200
        assert res.headers.get("X-Correlation-ID") == custom_corr


@pytest.mark.asyncio
async def test_aud_005_practical_immutability(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            entry = session.scalar(
                select(AuditLogModel).where(AuditLogModel.company_id == AUDIT_TEST_COMPANY_A).limit(1)
            )
            if not entry:
                from salesia.modules.auditoria.service import record_audit_event
                entry = record_audit_event(
                    session,
                    company_id=AUDIT_TEST_COMPANY_A,
                    actor_id=AUDIT_TEST_USER_A,
                    actor_email="audit_admin_a@enterprise.com",
                    action="SEED_FOR_IMMUTABILITY_TEST",
                    entity_type="Test",
                    entity_id=uuid4()
                )
                session.commit()
            target_id = entry.id

        del_res = await client.delete(f"/api/v1/audit/logs/{target_id}", headers=headers_company_a)
        assert del_res.status_code in (404, 405)

        del_res_alt = await client.delete(f"/api/v1/audit-logs/{target_id}", headers=headers_company_a)
        assert del_res_alt.status_code in (404, 405)


@pytest.mark.asyncio
async def test_aud_006_additional_cryptographic_integrity(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            count = session.scalar(
                select(func.count()).select_from(AuditLogModel).where(AuditLogModel.company_id == AUDIT_TEST_COMPANY_A)
            )
            if not count:
                from salesia.modules.auditoria.service import record_audit_event
                record_audit_event(
                    session,
                    company_id=AUDIT_TEST_COMPANY_A,
                    actor_id=AUDIT_TEST_USER_A,
                    actor_email="audit_admin_a@enterprise.com",
                    action="SEED_CHAIN_INTEGRITY",
                    entity_type="Security",
                    entity_id=uuid4()
                )
                session.commit()

        verify_res = await client.get("/api/v1/audit/logs/verify", headers=headers_company_a)
        assert verify_res.status_code == 200
        data = verify_res.json()
        assert data["is_valid"] is True
        assert data["verified_count"] >= 1


@pytest.mark.asyncio
async def test_aud_007_query_filtering_and_pagination(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/audit-logs?action=CONFIRM_SALE&limit=10",
            headers=headers_company_a
        )
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        for it in data["items"]:
            assert it["action"] == "CONFIRM_SALE"


@pytest.mark.asyncio
async def test_aud_008_business_timeline_sale_payment_return_refund(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_key = f"draft-aud8-{uuid4().hex}"
        sale_res = await client.post(
            "/api/v1/sales/draft",
            json={
                "customer_id": str(AUDIT_TEST_CUSTOMER_A),
                "branch_id": str(AUDIT_TEST_BRANCH_A),
                "warehouse_id": str(AUDIT_TEST_WAREHOUSE_A),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(AUDIT_TEST_PRODUCT_A),
                        "sku": "SKU-AUDIT-01",
                        "product_name": "Producto Para Pruebas Auditoria",
                        "quantity": 1,
                        "unit_price": "100.00"
                    }
                ]
            },
            headers={**headers_company_a, "Idempotency-Key": draft_key}
        )
        assert sale_res.status_code == 201
        sale_data = sale_res.json()
        sale_id = sale_data.get("sale_id") or sale_data.get("id")

        confirm_res = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**headers_company_a, "Idempotency-Key": f"confirm-aud8-{uuid4().hex}"}
        )
        assert confirm_res.status_code == 200

        pay_res = await client.post(
            "/api/v1/payments",
            json={
                "sale_id": sale_id,
                "payment_method": "CASH",
                "amount": "100.00",
                "currency": "USD",
                "cash_tendered": "100.00"
            },
            headers={**headers_company_a, "Idempotency-Key": f"pay-audit-{uuid4().hex[:8]}"}
        )
        assert pay_res.status_code == 201

        timeline_res = await client.get(
            f"/api/v1/audit/timeline/Sale/{sale_id}",
            headers=headers_company_a
        )
        assert timeline_res.status_code == 200
        tl = timeline_res.json()
        assert "events" in tl
        actions = [e["action"] for e in tl["events"]]
        assert "CONFIRM_SALE" in actions


@pytest.mark.asyncio
async def test_aud_009_export_audit_trail_and_logging(headers_company_a, headers_company_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        export_res = await client.post("/api/v1/audit/logs/export", headers=headers_company_a)
        assert export_res.status_code == 200
        exp_data = export_res.json()
        assert exp_data["cryptographic_seal"].startswith("sha256-")
        assert "data" in exp_data

        with sync_session_factory() as session:
            exp_log = session.scalar(
                select(AuditLogModel).where(
                    AuditLogModel.company_id == AUDIT_TEST_COMPANY_A,
                    AuditLogModel.action == "AUDIT_LOGS_EXPORT"
                ).order_by(AuditLogModel.created_at.desc())
            )
            assert exp_log is not None
            assert exp_log.actor_email == "audit_admin_a@enterprise.com"

        export_b = await client.post("/api/v1/audit/logs/export", headers=headers_company_b)
        assert export_b.status_code == 200
        for record in export_b.json()["data"]:
            assert record["actor"] != "audit_admin_a@enterprise.com"


@pytest.mark.asyncio
async def test_aud_010_clock_and_causal_order(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from salesia.modules.auditoria.service import record_audit_event
        test_entity = uuid4()
        with sync_session_factory() as session:
            e1 = record_audit_event(
                session,
                company_id=AUDIT_TEST_COMPANY_A,
                actor_id=AUDIT_TEST_USER_A,
                actor_email="audit_admin_a@enterprise.com",
                action="STEP_1_SUBMITTED",
                entity_type="WorkflowDoc",
                entity_id=test_entity,
                entity_version=1
            )
            e2 = record_audit_event(
                session,
                company_id=AUDIT_TEST_COMPANY_A,
                actor_id=AUDIT_TEST_USER_A,
                actor_email="audit_admin_a@enterprise.com",
                action="STEP_2_APPROVED",
                entity_type="WorkflowDoc",
                entity_id=test_entity,
                entity_version=2
            )
            session.commit()

        tl_res = await client.get(
            f"/api/v1/audit/timeline/WorkflowDoc/{test_entity}",
            headers=headers_company_a
        )
        assert tl_res.status_code == 200
        events = tl_res.json()["events"]
        assert len(events) == 2
        assert events[0]["action"] == "STEP_1_SUBMITTED"
        assert events[1]["action"] == "STEP_2_APPROVED"


@pytest.mark.asyncio
async def test_aud_011_retention_and_legal_hold_protection(headers_company_hold):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        target_cust = AUDIT_TEST_CUSTOMER_HOLD
        from salesia.modules.auditoria.service import record_audit_event
        with sync_session_factory() as session:
            old_log = record_audit_event(
                session,
                company_id=AUDIT_TEST_COMPANY_HOLD,
                actor_id=AUDIT_TEST_USER_HOLD,
                actor_email="audit_admin_hold@enterprise.com",
                action="OLD_ACTION",
                entity_type="Customer",
                entity_id=target_cust,
                category="OPERATIONAL",
                created_at=datetime.now(timezone.utc) - timedelta(days=400)
            )
            session.commit()
            old_id = old_log.id

        hold_res = await client.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(target_cust),
                "hold_reason": "Retencion especial bajo disputa legal 2026"
            },
            headers=headers_company_hold
        )
        assert hold_res.status_code == 200

        purge_res = await client.post(
            "/api/v1/audit/retention/purge",
            json={"category": "OPERATIONAL", "retention_days": 365},
            headers=headers_company_hold
        )
        assert purge_res.status_code == 200

        with sync_session_factory() as session:
            assert session.get(AuditLogModel, old_id) is not None

        lift_res = await client.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(target_cust),
                "hold_reason": "Disputa concluida",
                "action": "lift"
            },
            headers=headers_company_hold
        )
        assert lift_res.status_code == 200


@pytest.mark.asyncio
async def test_aud_012_privileged_access_logging(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        exp_res = await client.post(
            f"/api/v1/privacy/export-personal-data?customer_id={AUDIT_TEST_CUSTOMER_A}",
            headers=headers_company_a
        )
        assert exp_res.status_code == 200

        with sync_session_factory() as session:
            priv_log = session.scalar(
                select(AuditLogModel).where(
                    AuditLogModel.company_id == AUDIT_TEST_COMPANY_A,
                    AuditLogModel.action == "PRIVILEGED_ACCESS_EXPORT_PII",
                    AuditLogModel.entity_id == AUDIT_TEST_CUSTOMER_A
                ).order_by(AuditLogModel.created_at.desc())
            )
            assert priv_log is not None
            assert priv_log.actor_email == "audit_admin_a@enterprise.com"


@pytest.mark.asyncio
async def test_api_090_get_audit_logs_contract_and_isolation(headers_company_a, headers_company_b, headers_cashier_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        success_res = await client.get("/api/v1/audit-logs", headers=headers_company_a)
        assert success_res.status_code == 200
        data = success_res.json()
        assert "items" in data
        assert "count" in data

        invalid_limit = await client.get("/api/v1/audit-logs?limit=9999", headers=headers_company_a)
        assert invalid_limit.status_code == 422

        forbidden_res = await client.get("/api/v1/audit-logs", headers=headers_cashier_a)
        assert forbidden_res.status_code == 403

        res_b = await client.get("/api/v1/audit-logs", headers=headers_company_b)
        assert res_b.status_code == 200
        for item in res_b.json()["items"]:
            assert item["company_id"] == str(AUDIT_TEST_COMPANY_B)
            assert item["actor_email"] != "audit_admin_a@enterprise.com"


@pytest.mark.asyncio
async def test_fal_035_reconstruct_full_lifecycle(headers_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_key = f"draft-fal35-{uuid4().hex}"
        sale_res = await client.post(
            "/api/v1/sales/draft",
            json={
                "customer_id": str(AUDIT_TEST_CUSTOMER_A),
                "branch_id": str(AUDIT_TEST_BRANCH_A),
                "warehouse_id": str(AUDIT_TEST_WAREHOUSE_A),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(AUDIT_TEST_PRODUCT_A),
                        "sku": "SKU-AUDIT-01",
                        "product_name": "Producto Para Pruebas Auditoria",
                        "quantity": 1,
                        "unit_price": "100.00"
                    }
                ]
            },
            headers={**headers_company_a, "Idempotency-Key": draft_key}
        )
        assert sale_res.status_code == 201
        sale_data = sale_res.json()
        sale_id = sale_data.get("sale_id") or sale_data.get("id")

        confirm_res = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**headers_company_a, "Idempotency-Key": f"confirm-fal35-{uuid4().hex}"}
        )
        assert confirm_res.status_code == 200

        pay_key = f"fal035-pay-{uuid4().hex[:8]}"
        pay_res = await client.post(
            "/api/v1/payments",
            json={
                "sale_id": sale_id,
                "payment_method": "CASH",
                "amount": "100.00",
                "currency": "USD",
                "cash_tendered": "100.00"
            },
            headers={**headers_company_a, "Idempotency-Key": pay_key}
        )
        assert pay_res.status_code == 201
        payment_id = pay_res.json()["id"]

        ref_key = f"fal035-ref-{uuid4().hex[:8]}"
        ref_res = await client.post(
            "/api/v1/refunds",
            json={
                "payment_id": payment_id,
                "amount": "100.00",
                "reason": "Reembolso por devolucion comercial acordada"
            },
            headers={**headers_company_a, "Idempotency-Key": ref_key}
        )
        assert ref_res.status_code == 201

        with sync_session_factory() as session:
            logs = session.scalars(
                select(AuditLogModel).where(
                    AuditLogModel.company_id == AUDIT_TEST_COMPANY_A
                ).order_by(AuditLogModel.created_at.asc())
            ).all()
            actions = [l.action for l in logs]
            assert "CONFIRM_SALE" in actions
            assert "PAYMENT_RECEIVED" in actions or "PAYMENT_REGISTERED" in actions
            assert "REFUND_ISSUED" in actions
