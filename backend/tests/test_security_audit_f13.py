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
    CustomerModel,
    UserModel
)
from salesia.modules.seguridad.infrastructure.security import create_access_token, generate_totp_code, hash_password
from salesia.modules.seguridad.infrastructure.models import AuthFactor, RecoveryCode
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000005")


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

        user = session.execute(
            select(UserModel).where(UserModel.id == TEST_USER_ID)
        ).scalar_one_or_none()
        if not user:
            user = UserModel(
                id=TEST_USER_ID,
                company_id=TEST_COMPANY_ID,
                email="audit_admin_f13@salesia.enterprise",
                hashed_password=hash_password("valid_password"),
                role="company_admin",
                is_active=True,
                mfa_enabled=False,
                mfa_secret=None
            )
            session.add(user)
        else:
            user.company_id = TEST_COMPANY_ID
            user.role = "company_admin"
            user.is_active = True
            user.email = "audit_admin_f13@salesia.enterprise"
            user.hashed_password = hash_password("valid_password")
            user.mfa_enabled = False
            user.mfa_secret = None

        downgraded_ids = list(session.scalars(
            select(UserModel.id).where(
                UserModel.company_id == TEST_COMPANY_ID,
                UserModel.id != TEST_USER_ID,
                UserModel.role == "company_admin"
            )
        ).all())
        if downgraded_ids:
            session.query(UserModel).filter(
                UserModel.id.in_(downgraded_ids)
            ).update({"role": "cashier"}, synchronize_session=False)

        session.query(AuthFactor).filter(AuthFactor.user_id == TEST_USER_ID).delete()
        session.query(RecoveryCode).filter(RecoveryCode.user_id == TEST_USER_ID).delete()

        cust = session.execute(
            select(CustomerModel).where(CustomerModel.id == TEST_CUSTOMER_ID)
        ).scalar_one_or_none()
        if not cust:
            cust = CustomerModel(
                id=TEST_CUSTOMER_ID,
                company_id=TEST_COMPANY_ID,
                code="CLI-PRIV-01",
                doc_type="DNI",
                doc_number="44889922",
                legal_name="JUAN PEREZ CIUDADANO",
                credit_limit=Decimal("1000.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            )
            session.add(cust)

        session.commit()
    yield
    if downgraded_ids:
        with sync_session_factory() as teardown_session:
            teardown_session.query(UserModel).filter(
                UserModel.id.in_(downgraded_ids)
            ).update({"role": "company_admin"}, synchronize_session=False)
            teardown_session.commit()


@pytest.fixture
def auth_headers():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="company_admin",
        email="audit_admin_f13@salesia.enterprise",
        password="valid_password"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_security_headers_and_correlation_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        custom_corr = "test-corr-" + uuid4().hex[:8]
        res = await client.get("/api/v1/health", headers={"X-Correlation-ID": custom_corr})
        assert res.status_code == 200
        assert res.headers.get("X-Correlation-ID") == custom_corr
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert "max-age=31536000" in res.headers.get("Strict-Transport-Security", "")
        assert "default-src 'self'" in res.headers.get("Content-Security-Policy", "")


@pytest.mark.asyncio
async def test_iam_and_last_admin_protection(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        demote_res = await client.patch(
            f"/api/v1/memberships/{TEST_USER_ID}",
            json={"role": "cashier"},
            headers=auth_headers
        )
        assert demote_res.status_code == 409
        assert "administrador activo" in demote_res.json()["detail"].lower()

        deact_res = await client.patch(
            f"/api/v1/memberships/{TEST_USER_ID}",
            json={"is_active": False},
            headers=auth_headers
        )
        assert deact_res.status_code == 409

        invalid_role_invite = await client.post(
            "/api/v1/memberships/invitations",
            json={"email": f"test-{uuid4().hex[:6]}@example.com", "role": "super_root_fake"},
            headers=auth_headers
        )
        assert invalid_role_invite.status_code == 422

        escalate_role = await client.post(
            "/api/v1/roles",
            json={
                "role_key": "role_super_escalate",
                "title": "Super Rol",
                "permissions": ["platform:manage"]
            },
            headers=auth_headers
        )
        assert escalate_role.status_code == 403

        role_key_unique = "sec_analyst_" + uuid4().hex[:6]
        valid_custom_role = await client.post(
            "/api/v1/roles",
            json={
                "role_key": role_key_unique,
                "title": "Auditor Financiero",
                "permissions": ["audit:logs:read"]
            },
            headers=auth_headers
        )
        assert valid_custom_role.status_code == 201

        list_roles_res = await client.get("/api/v1/roles", headers=auth_headers)
        assert list_roles_res.status_code == 200
        assert any(r["role"] == role_key_unique for r in list_roles_res.json()["roles"])

        list_users_res = await client.get("/api/v1/users", headers=auth_headers)
        assert list_users_res.status_code == 200
        assert len(list_users_res.json()) >= 1


@pytest.mark.asyncio
async def test_auth_mfa_sudo_and_brute_force(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mfa_setup = await client.post(
            "/api/v1/auth/mfa/setup",
            json={"password": "valid_password"},
            headers=auth_headers
        )
        assert mfa_setup.status_code == 200
        mfa_data = mfa_setup.json()
        assert "totp_secret" in mfa_data
        assert len(mfa_data["recovery_codes"]) == 8

        totp_code = generate_totp_code(mfa_data["totp_secret"])
        mfa_verify = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"code": totp_code},
            headers=auth_headers
        )
        assert mfa_verify.status_code == 200
        assert mfa_verify.json()["verified"] is True

        sudo_res = await client.post(
            "/api/v1/auth/sudo/verify",
            json={"password": "valid_password", "mfa_code": mfa_data["recovery_codes"][0]},
            headers=auth_headers
        )
        assert sudo_res.status_code == 200
        assert sudo_res.json()["sudo_mode_active"] is True

        attack_email = f"target-{uuid4().hex[:6]}@empresa.com"
        for _ in range(5):
            fail_res = await client.post(
                "/api/v1/auth/login",
                json={"email": attack_email, "password": "clave_erronea"}
            )
            assert fail_res.status_code == 401

        blocked_res = await client.post(
            "/api/v1/auth/login",
            json={"email": attack_email, "password": "clave_erronea"}
        )
        assert blocked_res.status_code == 429


@pytest.mark.asyncio
async def test_audit_trail_and_cryptographic_export(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        log_res = await client.post(
            "/api/v1/audit/logs",
            json={
                "action": "CONFIG_UPDATE",
                "entity_type": "company_settings",
                "entity_id": str(TEST_COMPANY_ID),
                "payload_diff": {"old": {"currency": "USD"}, "new": {"currency": "USD"}}
            },
            headers=auth_headers
        )
        assert log_res.status_code == 201
        log_id = log_res.json()["id"]
        assert "chain_hash" in log_res.json()

        detail_res = await client.get(f"/api/v1/audit/logs/{log_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["action"] == "CONFIG_UPDATE"

        list_res = await client.get(
            "/api/v1/audit/logs?entity_type=company_settings",
            headers=auth_headers
        )
        assert list_res.status_code == 200
        assert list_res.json()["count"] >= 1

        export_res = await client.post("/api/v1/audit/logs/export", headers=auth_headers)
        assert export_res.status_code == 200
        assert export_res.json()["cryptographic_seal"].startswith("sha256-")
        assert export_res.json()["exported_records"] >= 1


@pytest.mark.asyncio
async def test_security_hardening_ssrf_xss_apikeys(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_key = await client.post(
            "/api/v1/security/api-keys",
            json={"name": "Integracion ERP", "scope": "integration"},
            headers=auth_headers
        )
        assert create_key.status_code == 201
        key_data = create_key.json()
        assert key_data["raw_secret_key"].startswith("sal_live_")
        key_id = key_data["key_id"]

        list_keys = await client.get("/api/v1/security/api-keys", headers=auth_headers)
        assert list_keys.status_code == 200
        assert any(k["key_id"] == key_id for k in list_keys.json()["items"])

        revoke_key = await client.delete(f"/api/v1/security/api-keys/{key_id}", headers=auth_headers)
        assert revoke_key.status_code == 200
        assert revoke_key.json()["revoked"] is True

        ssrf_loopback = await client.post(
            "/api/v1/security/validate-url",
            json={"url": "http://127.0.0.1:8080/admin"},
            headers=auth_headers
        )
        assert ssrf_loopback.status_code == 200
        assert ssrf_loopback.json()["is_safe"] is False

        ssrf_private = await client.post(
            "/api/v1/security/validate-url",
            json={"url": "http://192.168.1.100/webhook"},
            headers=auth_headers
        )
        assert ssrf_private.status_code == 200
        assert ssrf_private.json()["is_safe"] is False

        ssrf_valid = await client.post(
            "/api/v1/security/validate-url",
            json={"url": "https://api.sunat.gob.pe/v1/comprobantes"},
            headers=auth_headers
        )
        assert ssrf_valid.status_code == 200
        assert ssrf_valid.json()["is_safe"] is True

        xss_check = await client.post(
            "/api/v1/security/sanitize-input",
            json={"raw_text": "<script>alert('XSS')</script>Bienvenido a SalesIA"},
            headers=auth_headers
        )
        assert xss_check.status_code == 200
        assert "<script>" not in xss_check.json()["sanitized_text"]
        assert "Bienvenido a SalesIA" in xss_check.json()["sanitized_text"]


@pytest.mark.asyncio
async def test_privacy_gdpr_arco_and_legal_hold(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        inv_res = await client.get("/api/v1/privacy/data-inventory", headers=auth_headers)
        assert inv_res.status_code == 200
        assert len(inv_res.json()["inventory"]) >= 1

        mask_res = await client.post(
            "/api/v1/privacy/mask-data",
            json={"data": {"email": "director@empresa.com", "dni": "44889922"}},
            headers=auth_headers
        )
        assert mask_res.status_code == 200
        assert mask_res.json()["masked_data"]["email"].startswith("d***@")

        export_res = await client.post(
            f"/api/v1/privacy/export-personal-data?customer_id={TEST_CUSTOMER_ID}",
            headers=auth_headers
        )
        assert export_res.status_code == 200
        assert export_res.json()["customer_id"] == str(TEST_CUSTOMER_ID)

        hold_place = await client.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(TEST_CUSTOMER_ID),
                "hold_reason": "Auditoría tributaria SUNAT expediente 2026-09"
            },
            headers=auth_headers
        )
        assert hold_place.status_code == 200
        assert hold_place.json()["status"] == "hold_placed"

        anon_blocked = await client.post(
            "/api/v1/privacy/anonymize-customer",
            json={"customer_id": str(TEST_CUSTOMER_ID)},
            headers=auth_headers
        )
        assert anon_blocked.status_code == 423

        hold_lift = await client.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(TEST_CUSTOMER_ID),
                "hold_reason": "Auditoría finalizada",
                "action": "lift"
            },
            headers=auth_headers
        )
        assert hold_lift.status_code == 200
        assert hold_lift.json()["status"] == "hold_lifted"

        anon_success = await client.post(
            "/api/v1/privacy/anonymize-customer",
            json={"customer_id": str(TEST_CUSTOMER_ID)},
            headers=auth_headers
        )
        assert anon_success.status_code == 200
        assert anon_success.json()["status"] == "anonymized"
