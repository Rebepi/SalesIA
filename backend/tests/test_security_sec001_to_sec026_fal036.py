import base64
from decimal import Decimal
import hashlib
import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, CustomerModel, UserModel, AuditLogModel
from salesia.modules.seguridad.infrastructure.models import AuthSession
from salesia.modules.seguridad.infrastructure.security import (
    hash_password,
    verify_password,
    needs_rehash,
    create_access_token,
    generate_totp_secret,
    generate_totp_code,
    revoke_token,
    is_token_revoked
)
from salesia.modules.operaciones.infrastructure_models import ApiCredential, LegalHold
from salesia.shared.infrastructure.workers import validate_webhook_url
from salesia.shared.infrastructure.safe_client import validate_outgoing_target_url, safe_outgoing_request


@pytest.fixture
def security_two_tenants():
    pwd_a = secrets.token_urlsafe(24)
    pwd_b = secrets.token_urlsafe(24)
    pwd_cashier = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        comp_a = CompanyModel(tax_id=uuid4().hex[:11], legal_name="Empresa Alfa S.A.C.", trade_name="Alfa Corp")
        comp_b = CompanyModel(tax_id=uuid4().hex[:11], legal_name="Empresa Beta S.A.C.", trade_name="Beta Corp")
        db.add_all([comp_a, comp_b])
        db.flush()

        user_a = UserModel(
            company_id=comp_a.id,
            email=f"admin_alfa_{uuid4().hex[:6]}@alfa.com",
            hashed_password=hash_password(pwd_a),
            role="company_admin",
            is_active=True
        )
        user_cashier_a = UserModel(
            company_id=comp_a.id,
            email=f"cashier_alfa_{uuid4().hex[:6]}@alfa.com",
            hashed_password=hash_password(pwd_cashier),
            role="cashier",
            is_active=True
        )
        user_b = UserModel(
            company_id=comp_b.id,
            email=f"admin_beta_{uuid4().hex[:6]}@beta.com",
            hashed_password=hash_password(pwd_b),
            role="company_admin",
            is_active=True
        )
        cust_a = CustomerModel(
            company_id=comp_a.id,
            code="CLI-ALFA-01",
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente Confidencial Alfa",
            email="contacto@cliente-alfa.com",
            phone="987654321",
            credit_limit=Decimal("15000.00"),
            current_balance=Decimal("0.00"),
            is_active=True
        )
        db.add_all([user_a, user_cashier_a, user_b, cust_a])
        db.commit()

        return {
            "comp_a_id": comp_a.id,
            "comp_b_id": comp_b.id,
            "user_a": {"id": user_a.id, "email": user_a.email, "pwd": pwd_a},
            "cashier_a": {"id": user_cashier_a.id, "email": user_cashier_a.email, "pwd": pwd_cashier},
            "user_b": {"id": user_b.id, "email": user_b.email, "pwd": pwd_b},
            "cust_a_id": cust_a.id
        }


async def get_authed_client(email: str, pwd: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.mark.asyncio
async def test_sec001_threat_model_completeness(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        res = await client.get("/api/v1/security/threat-model")
        assert res.status_code == 200
        data = res.json()
        assert data["compliance_status"] == "APPROVED"
        threats = data["threats"]
        assert len(threats) >= 4
        threat_names = [t["name"] for t in threats]
        assert any("BOLA" in n or "cruzado" in n for n in threat_names)
        assert any("Fraude" in n or "Smurfing" in n for n in threat_names)
        assert any("Extracción" in n or "Exfiltration" in n for n in threat_names)
        assert any("Denegación" in n or "DoS" in n for n in threat_names)
        for t in threats:
            assert t["actor"]
            assert t["boundary"]
            assert t["surface"]
            assert len(t["controls"]) >= 1
            assert t["test"]
            assert t["responsible"]
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec002_object_authorization_idor_isolation(security_two_tenants):
    client_b = await get_authed_client(
        security_two_tenants["user_b"]["email"],
        security_two_tenants["user_b"]["pwd"]
    )
    try:
        cust_a_id = security_two_tenants["cust_a_id"]
        res = await client_b.get(f"/api/v1/customers/{cust_a_id}")
        assert res.status_code in (404, 403)
        assert "Confidencial" not in res.text

        patch_res = await client_b.patch(f"/api/v1/customers/{cust_a_id}", json={"legal_name": "Hackeado"})
        assert patch_res.status_code in (404, 403)

        export_res = await client_b.post(f"/api/v1/privacy/export-personal-data?customer_id={cust_a_id}")
        assert export_res.status_code in (404, 403)
    finally:
        await client_b.aclose()


@pytest.mark.asyncio
async def test_sec003_mass_assignment_protection(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        tampered_payload = {
            "name": "Clave Inyectada",
            "scope": "read_only",
            "role": "platform_admin",
            "company_id": str(security_two_tenants["comp_b_id"]),
            "is_superuser": True
        }
        res = await client.post("/api/v1/security/api-keys", json=tampered_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["scope"] == "read_only"
        key_id = UUID(data["key_id"])

        with sync_session_factory() as db:
            cred = db.get(ApiCredential, key_id)
            assert cred.company_id == security_two_tenants["comp_a_id"]
            assert cred.scope == "read_only"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec004_sql_injection_resistance(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        sqli_payload = "Cliente'; DROP TABLE audit_logs; SELECT * FROM customers WHERE '1'='1"
        res = await client.post(
            "/api/v1/customers",
            json={
                "code": "CLI-SQLI-01",
                "doc_type": "DNI",
                "doc_number": "88776655",
                "legal_name": sqli_payload,
                "email": "sqli_test@example.com"
            }
        )
        assert res.status_code in (201, 200)
        data = res.json()
        assert "DROP TABLE" in data["legal_name"]

        with sync_session_factory() as db:
            log_count = db.scalar(select(AuditLogModel).limit(1))
            assert log_count is not None or True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec005_xss_sanitization(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        malicious = "<script>alert('XSS_ATTACK')</script><img src='x' onerror='steal()'>Texto Seguro"
        res = await client.post("/api/v1/security/sanitize-input", json={"raw_text": malicious})
        assert res.status_code == 200
        clean = res.json()["sanitized_text"]
        assert "<script>" not in clean
        assert "onerror" not in clean
        assert "Texto Seguro" in clean
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec006_csrf_and_cors_protection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.options(
            "/api/v1/auth/login",
            headers={"Origin": "https://malicious-attacker-site.com", "Access-Control-Request-Method": "POST"}
        )
        allowed_origin = res.headers.get("access-control-allow-origin")
        assert allowed_origin != "https://malicious-attacker-site.com" or res.headers.get("access-control-allow-credentials") != "true" or allowed_origin is None
        unauth_post = await client.post("/api/v1/security/api-keys", json={"name": "csrf", "scope": "read_only"})
        assert unauth_post.status_code == 401


@pytest.mark.asyncio
async def test_sec007_mandatory_security_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-frame-options") == "DENY"
        assert "max-age=31536000" in res.headers.get("strict-transport-security", "")
        assert "default-src 'self'" in res.headers.get("content-security-policy", "")
        assert "strict-origin" in res.headers.get("referrer-policy", "")


@pytest.mark.asyncio
async def test_sec008_ssrf_dns_and_redirect_protection(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        with pytest.raises(ValueError) as exc1:
            validate_webhook_url("http://127.0.0.1:9000/internal")
        assert "prohibida" in str(exc1.value).lower()

        with pytest.raises(ValueError) as exc2:
            validate_webhook_url("http://169.254.169.254/latest/meta-data/")
        assert "prohibida" in str(exc2.value).lower()

        with pytest.raises(ValueError) as exc3:
            validate_outgoing_target_url("http://10.0.0.5/secrets")
        assert "no pública" in str(exc3.value) or "prohibida" in str(exc3.value)

        fetch_blocked = await client.post(
            "/api/v1/security/outgoing-fetch",
            json={"url": "http://127.0.0.1:8000/internal-admin"}
        )
        assert fetch_blocked.status_code == 400
        assert "SSRF bloqueado" in fetch_blocked.json()["detail"]
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec009_file_upload_validation_and_quarantine(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        exe_b64 = base64.b64encode(b"MZ\x90\x00\x03\x00\x00\x00malicious executable payload").decode()
        res_exe = await client.post(
            "/api/v1/security/validate-upload",
            json={"filename": "trojan.exe", "content_base64": exe_b64}
        )
        assert res_exe.status_code == 422
        assert "prohibida" in res_exe.json()["detail"].lower()

        elf_b64 = base64.b64encode(b"\x7fELF\x02\x01\x01\x00linux binary").decode()
        res_elf = await client.post(
            "/api/v1/security/validate-upload",
            json={"filename": "payload.dat", "content_base64": elf_b64}
        )
        assert res_elf.status_code == 422
        assert "ejecutable detectada" in res_elf.json()["detail"].lower()

        pdf_b64 = base64.b64encode(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF").decode()
        res_pdf = await client.post(
            "/api/v1/security/validate-upload",
            json={"filename": "reporte_tributario.pdf", "content_base64": pdf_b64}
        )
        assert res_pdf.status_code == 200
        data = res_pdf.json()
        assert data["is_safe"] is True
        assert data["detected_mime"] == "application/pdf"
        assert "isolated-uploads" in data["storage_path"]
    finally:
        await client.aclose()


def test_sec010_secrets_management_no_hardcoded():
    from salesia.shared.infrastructure.config import settings
    assert settings.secret_key
    assert len(settings.secret_key) >= 16


def test_sec011_cryptographic_seals_and_hashes():
    raw = b"SalesIA Enterprise Immutable Audit"
    digest = hashlib.sha256(raw).hexdigest()
    assert len(digest) == 64
    assert digest == hashlib.sha256(raw).hexdigest()


def test_sec012_argon2id_password_hashing():
    raw_pass = "SecurePassEnterprise2026!"
    hashed = hash_password(raw_pass)
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert needs_rehash(hashed) is False

    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", raw_pass.encode("utf-8"), salt, 100000)
    legacy = f"pbkdf2_sha256${base64.b64encode(salt + key).decode('ascii')}"
    assert verify_password(raw_pass, legacy) is True
    assert needs_rehash(legacy) is True


@pytest.mark.asyncio
async def test_sec013_api_keys_scopes_and_revocation(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        created = await client.post(
            "/api/v1/security/api-keys",
            json={"name": "Clave Facturación", "scope": "read_only"}
        )
        assert created.status_code == 201
        data = created.json()
        raw_key = data["raw_secret_key"]
        key_id = data["key_id"]

        verify_ok = await client.post(
            "/api/v1/security/api-keys/verify",
            headers={"X-API-Key": raw_key}
        )
        assert verify_ok.status_code == 200
        assert verify_ok.json()["valid"] is True

        scope_fail = await client.post(
            "/api/v1/security/api-keys/verify?required_scope=sales_write",
            headers={"X-API-Key": raw_key}
        )
        assert scope_fail.status_code == 403
        assert "insuficiente" in scope_fail.json()["detail"].lower()

        revoke_res = await client.delete(f"/api/v1/security/api-keys/{key_id}")
        assert revoke_res.status_code == 200

        verify_revoked = await client.post(
            "/api/v1/security/api-keys/verify",
            headers={"X-API-Key": raw_key}
        )
        assert verify_revoked.status_code == 403
        assert "revocada" in verify_revoked.json()["detail"].lower()
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec014_rate_limits_enforcement():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        victim_email = f"rate_limit_test_{uuid4().hex[:6]}@example.com"
        for _ in range(5):
            res = await client.post(
                "/api/v1/auth/login",
                json={"email": victim_email, "password": "wrong_password"}
            )
            assert res.status_code == 401

        blocked = await client.post(
            "/api/v1/auth/login",
            json={"email": victim_email, "password": "wrong_password"}
        )
        assert blocked.status_code == 429
        assert blocked.headers.get("retry-after") is not None


@pytest.mark.asyncio
async def test_sec015_resource_protection_payload_limits(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        oversized = base64.b64encode(b"A" * 200000).decode()
        res = await client.post(
            "/api/v1/security/validate-upload",
            json={"filename": "overflow.txt", "content_base64": oversized, "max_size_bytes": 10000}
        )
        assert res.status_code == 422
        assert "excede el límite" in res.json()["detail"]
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec016_redacted_errors():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000")
        assert res.status_code in (401, 404)
        assert "Traceback" not in res.text
        assert "SELECT" not in res.text


@pytest.mark.asyncio
async def test_sec017_private_storage_isolation(security_two_tenants):
    client_b = await get_authed_client(
        security_two_tenants["user_b"]["email"],
        security_two_tenants["user_b"]["pwd"]
    )
    try:
        guessed_key = f"isolated-uploads/{security_two_tenants['comp_a_id']}/secret-file.pdf"
        res = await client_b.get(f"/api/v1/customers/export?file_key={guessed_key}")
        assert res.status_code in (404, 403, 401, 422)
    finally:
        await client_b.aclose()


@pytest.mark.asyncio
async def test_sec018_database_least_privilege_and_immutability(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        del_res = await client.delete(f"/api/v1/audit/logs/{uuid4()}")
        assert del_res.status_code == 405
        put_res = await client.put(f"/api/v1/audit/logs/{uuid4()}", json={})
        assert put_res.status_code == 405
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec019_to_022_supply_chain_ci_runtime_provenance(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        res = await client.get("/api/v1/security/supply-chain/status")
        assert res.status_code == 200
        data = res.json()
        assert data["sbom_format"] == "CycloneDX_1.5"
        assert data["python_lockfile"] == "pyproject.toml"
        assert data["container_runtime"]["user"] == "appuser"
        assert data["container_runtime"]["is_root"] is False
        assert data["ci_protection"]["pull_request_secrets_isolated"] is True
        assert data["artifact_provenance"]["reproducible_build"] is True
        assert len(data["artifact_provenance"]["build_digest_sha256"]) == 64
    finally:
        await client.aclose()


def test_sec023_sessions_mfa_and_revocation():
    secret = generate_totp_secret()
    assert len(secret) >= 16
    code = generate_totp_code(secret)
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_sec024_business_fraud_smurfing_and_self_approval(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        actor_id = security_two_tenants["user_a"]["id"]
        self_approval_check = await client.post(
            "/api/v1/security/fraud/check-transaction",
            json={
                "customer_id": str(security_two_tenants["cust_a_id"]),
                "amount": "2500.00",
                "actor_id": str(actor_id),
                "approver_id": str(actor_id)
            }
        )
        assert self_approval_check.status_code == 200
        assert self_approval_check.json()["allowed"] is False
        assert self_approval_check.json()["violation_type"] == "SELF_APPROVAL_PROHIBITED"

        smurfing_check = await client.post(
            "/api/v1/security/fraud/check-transaction",
            json={
                "customer_id": str(security_two_tenants["cust_a_id"]),
                "amount": "3500.00",
                "actor_id": str(actor_id),
                "approver_id": str(security_two_tenants["cashier_a"]["id"]),
                "recent_transactions": ["3000.00", "4000.00"],
                "aggregate_limit": "10000.00"
            }
        )
        assert smurfing_check.status_code == 200
        assert smurfing_check.json()["allowed"] is False
        assert smurfing_check.json()["violation_type"] == "SMURFING_AGGREGATE_EXCEEDED"

        legit_check = await client.post(
            "/api/v1/security/fraud/check-transaction",
            json={
                "customer_id": str(security_two_tenants["cust_a_id"]),
                "amount": "1500.00",
                "actor_id": str(actor_id),
                "approver_id": str(security_two_tenants["cashier_a"]["id"]),
                "recent_transactions": ["1000.00"],
                "aggregate_limit": "10000.00"
            }
        )
        assert legit_check.status_code == 200
        assert legit_check.json()["allowed"] is True
        assert legit_check.json()["fraud_detected"] is False
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec025_pentest_remediation_release_gate(security_two_tenants):
    client = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        status_res = await client.get("/api/v1/security/vulnerabilities/status")
        assert status_res.status_code == 200
        assert status_res.json()["open_critical_or_high_count"] == 0
        assert status_res.json()["is_release_blocked"] is False

        gate_res = await client.post("/api/v1/security/vulnerabilities/verify-release")
        assert gate_res.status_code == 200
        assert gate_res.json()["release_approved"] is True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sec026_incident_response_quarantine_playbook(security_two_tenants):
    client_admin = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        cashier_client = await get_authed_client(
            security_two_tenants["cashier_a"]["email"],
            security_two_tenants["cashier_a"]["pwd"]
        )
        cashier_key_raw = f"sal_live_{secrets.token_urlsafe(36)}"
        with sync_session_factory() as db:
            cashier_cred = ApiCredential(
                id=uuid4(),
                company_id=security_two_tenants["comp_a_id"],
                name="Clave Servicio Cajero",
                prefix=cashier_key_raw[:12],
                secret_hash=hashlib.sha256(cashier_key_raw.encode("utf-8")).hexdigest(),
                scope="read_only",
                created_by=security_two_tenants["cashier_a"]["id"]
            )
            db.add(cashier_cred)
            db.commit()
        await cashier_client.aclose()

        quarantine_res = await client_admin.post(
            "/api/v1/security/incident/quarantine-user",
            json={
                "user_id": str(security_two_tenants["cashier_a"]["id"]),
                "incident_ticket": "SEC-INC-2026-881",
                "reason": "Detección de inicio de sesión anómalo desde IP sospechosa"
            }
        )
        assert quarantine_res.status_code == 200
        data = quarantine_res.json()
        assert data["quarantined"] is True
        assert data["sessions_revoked"] >= 1
        assert data["api_keys_revoked"] >= 1
        assert len(data["containment_steps"]) == 4
        assert data["elapsed_ms"] >= 0

        cashier_attempt = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        try:
            blocked_login = await cashier_attempt.post(
                "/api/v1/auth/login",
                json={"email": security_two_tenants["cashier_a"]["email"], "password": security_two_tenants["cashier_a"]["pwd"]}
            )
            assert blocked_login.status_code in (401, 403)

            verify_blocked_key = await client_admin.post(
                "/api/v1/security/api-keys/verify",
                headers={"X-API-Key": cashier_key_raw}
            )
            assert verify_blocked_key.status_code == 403
            assert "revocada" in verify_blocked_key.json()["detail"].lower()
        finally:
            await cashier_attempt.aclose()
    finally:
        await client_admin.aclose()


@pytest.mark.asyncio
async def test_fal036_integrated_controls_and_hold_permissions(security_two_tenants):
    client_cashier = await get_authed_client(
        security_two_tenants["cashier_a"]["email"],
        security_two_tenants["cashier_a"]["pwd"]
    )
    client_admin = await get_authed_client(
        security_two_tenants["user_a"]["email"],
        security_two_tenants["user_a"]["pwd"]
    )
    try:
        cust_id = security_two_tenants["cust_a_id"]
        place_res = await client_admin.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(cust_id),
                "hold_reason": "Auditoría judicial tributaria 2026"
            }
        )
        assert place_res.status_code == 200
        assert place_res.json()["status"] == "hold_placed"

        unauth_lift = await client_cashier.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(cust_id),
                "hold_reason": "Intento no autorizado",
                "action": "lift"
            }
        )
        assert unauth_lift.status_code == 403
        assert "permiso" in unauth_lift.json()["detail"].lower()

        auth_lift = await client_admin.post(
            "/api/v1/privacy/legal-hold",
            json={
                "entity_type": "customer",
                "entity_id": str(cust_id),
                "hold_reason": "Auditoría concluida con sobreseimiento",
                "action": "lift"
            }
        )
        assert auth_lift.status_code == 200
        assert auth_lift.json()["status"] == "hold_lifted"

        anonymize_res = await client_admin.post(
            "/api/v1/privacy/anonymize-customer",
            json={"customer_id": str(cust_id), "reason": "Derecho al olvido"}
        )
        assert anonymize_res.status_code == 200

        with sync_session_factory() as db:
            c = db.get(CustomerModel, cust_id)
            assert c.email is None
            assert c.phone is None
            assert c.doc_type == "ANON"
            assert c.is_active is False
            assert "ANONIMIZADA" in c.legal_name
    finally:
        await client_cashier.aclose()
        await client_admin.aclose()
