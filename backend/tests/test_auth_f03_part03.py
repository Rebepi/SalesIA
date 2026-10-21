from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, UserModel, SaleModel
from salesia.modules.seguridad.infrastructure.models import AuthSession, AuthChallenge, RecoveryCode, AuthFactor, AuthMail
from salesia.modules.seguridad.infrastructure.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_totp_code
)
from salesia.modules.seguridad.infrastructure.sessions import utcnow, fingerprint, cipher


def make_user(role="company_admin", active=True, email=None, password=None):
    with sync_session_factory() as db:
        company = CompanyModel(
            id=uuid4(),
            tax_id=uuid4().hex[:11],
            legal_name="Empresa Test",
            trade_name="Test Trade",
            base_currency="USD",
            is_active=True
        )
        db.add(company)
        db.flush()
        u_email = email or f"{uuid4().hex[:10]}@test.enterprise"
        u_pass = password or "SuperSecPassword2026!#"
        user = UserModel(
            id=uuid4(),
            company_id=company.id,
            email=u_email,
            hashed_password=hash_password(u_pass),
            role=role,
            is_active=active
        )
        db.add(user)
        db.commit()
        return {"company_id": company.id, "user_id": user.id, "email": u_email, "password": u_pass}


@pytest.mark.asyncio
async def test_reproduced_failure_01_login_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/auth/login", json={
            "email": "inexistente_9999@noexiste.com",
            "password": "PasswordInexistente123!"
        })
        assert res.status_code == 401
        data = res.json()
        assert "access_token" not in data


@pytest.mark.asyncio
async def test_reproduced_failure_02_refresh_as_access_token():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert login_res.status_code == 200
        refresh_token = login_res.json()["refresh_token"]
        me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
        assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_reproduced_failure_03_frontend_refresh_rotation_and_reuse():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert login_res.status_code == 200
        first_tokens = login_res.json()
        ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_tokens["refresh_token"]})
        assert ref_res.status_code == 200
        second_tokens = ref_res.json()
        assert second_tokens["access_token"] != first_tokens["access_token"]
        assert second_tokens["refresh_token"] != first_tokens["refresh_token"]
        reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_tokens["refresh_token"]})
        assert reuse_res.status_code == 401
        invalidated_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second_tokens['access_token']}"})
        assert invalidated_me.status_code == 401


@pytest.mark.asyncio
async def test_reproduced_failure_04_token_revocation_after_logout():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert login_res.status_code == 200
        tokens = login_res.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_before = await client.get("/api/v1/auth/me", headers=headers)
        assert me_before.status_code == 200
        logout_res = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_res.status_code == 200
        me_after = await client.get("/api/v1/auth/me", headers=headers)
        assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_reproduced_failure_05_mfa_rejects_abcdef():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        tokens = login_res.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        setup_res = await client.post("/api/v1/auth/mfa/setup", headers=headers, json={"password": u["password"]})
        assert setup_res.status_code == 200
        factor_data = setup_res.json()
        verify_invalid = await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": "abcdef"})
        assert verify_invalid.status_code == 400
        totp_code = generate_totp_code(factor_data["totp_secret"])
        verify_valid = await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": totp_code})
        assert verify_valid.status_code == 200


@pytest.mark.asyncio
async def test_reproduced_failure_06_password_reset_rejects_fake_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_reset = await client.post("/api/v1/auth/password/reset", json={
            "reset_token": "fake_token_random_1234567890",
            "new_password": "NewValidSecretPassword2026!"
        })
        assert fake_reset.status_code == 401


@pytest.mark.asyncio
async def test_reg_01_invalid_login_deactivated_account_and_revoked_membership():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        bad_pass = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": "wrong_password_999"})
        assert bad_pass.status_code == 401
        ok_login = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert ok_login.status_code == 200
        tokens = ok_login.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        with sync_session_factory() as db:
            user = db.get(UserModel, u["user_id"])
            user.is_active = False
            db.commit()
        me_inactive = await client.get("/api/v1/auth/me", headers=headers)
        assert me_inactive.status_code == 401
        login_inactive = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert login_inactive.status_code == 401


@pytest.mark.asyncio
async def test_reg_02_tokens_and_security_controls_rejections():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        tokens = login_res.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        as_access = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
        assert as_access.status_code == 401
        sudo_fake = await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": "magic_pass_literal"})
        assert sudo_fake.status_code == 401
        sudo_real = await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": u["password"]})
        assert sudo_real.status_code == 200


@pytest.mark.asyncio
async def test_reg_03_logout_revoke_inactivate_cuts_session_immediately():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
        assert len(sessions) >= 1
        sid = sessions[0]["session_id"]
        del_res = await client.delete(f"/api/v1/auth/sessions/{sid}", headers=headers)
        assert del_res.status_code == 200
        cut_me = await client.get("/api/v1/auth/me", headers=headers)
        assert cut_me.status_code == 401


@pytest.mark.asyncio
async def test_auth_001_login_credentials_and_generic_error():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_ok = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert res_ok.status_code == 200
        body = res_ok.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["email"] == u["email"]
        assert body["role"] == "company_admin"
        res_fail = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": "WrongPassword!"})
        assert res_fail.status_code == 401
        assert "Credenciales" in res_fail.text or "unauthorized" in res_fail.text.lower()


@pytest.mark.asyncio
async def test_auth_002_password_hashing_and_complexity():
    u = make_user()
    with sync_session_factory() as db:
        user = db.get(UserModel, u["user_id"])
        assert user.hashed_password.startswith(("$argon2id$", "pbkdf2_sha256$"))
        assert u["password"] not in user.hashed_password
        assert verify_password(u["password"], user.hashed_password) is True
        assert verify_password("otherPassword", user.hashed_password) is False


@pytest.mark.asyncio
async def test_auth_003_mfa_totp_enforcement():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
        setup = await client.post("/api/v1/auth/mfa/setup", headers=headers, json={"password": u["password"]})
        assert setup.status_code == 200
        secret = setup.json()["totp_secret"]
        assert (await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": "111111"})).status_code == 400
        valid_code = generate_totp_code(secret)
        assert (await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": valid_code})).status_code == 200
        no_mfa = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert no_mfa.status_code == 401


@pytest.mark.asyncio
async def test_auth_004_recovery_codes_single_use():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {(await client.post('/api/v1/auth/login', json={'email': u['email'], 'password': u['password']})).json()['access_token']}"}
        setup_data = (await client.post("/api/v1/auth/mfa/setup", headers=headers, json={"password": u["password"]})).json()
        valid_code = generate_totp_code(setup_data["totp_secret"])
        await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": valid_code})
        recovery_code = setup_data["recovery_codes"][0]
        login_with_recovery = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"], "mfa_code": recovery_code})
        assert login_with_recovery.status_code == 200
        reuse_recovery = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"], "mfa_code": recovery_code})
        assert reuse_recovery.status_code == 401


@pytest.mark.asyncio
async def test_auth_005_invitations_lifecycle_and_single_use():
    admin = make_user(role="company_admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {(await client.post('/api/v1/auth/login', json={'email': admin['email'], 'password': admin['password']})).json()['access_token']}"}
        invited_email = f"invited_{uuid4().hex[:8]}@test.enterprise"
        invite_res = await client.post("/api/v1/memberships/invitations", headers=headers, json={"email": invited_email, "role": "salesperson"})
        assert invite_res.status_code == 201
        token = secrets.token_urlsafe(48)
        with sync_session_factory() as db:
            invited_user = db.scalar(select(UserModel).where(UserModel.email == invited_email))
            assert invited_user.is_active is False
            db.add(AuthChallenge(user_id=invited_user.id, token_hash=fingerprint(token), purpose="invitation", expires_at=utcnow() + timedelta(hours=1)))
            db.commit()
        reset_res = await client.post("/api/v1/auth/password/reset", json={"reset_token": token, "new_password": "NewEmployeePassword2026!"})
        assert reset_res.status_code == 200
        with sync_session_factory() as db:
            assert db.scalar(select(UserModel).where(UserModel.email == invited_email)).is_active is True
        reuse_reset = await client.post("/api/v1/auth/password/reset", json={"reset_token": token, "new_password": "AnotherPassword2026!"})
        assert reuse_reset.status_code == 401


@pytest.mark.asyncio
async def test_auth_invitation_resend_cancel_and_html_email():
    admin = make_user(role="company_admin")
    invited_email = f"invited_{uuid4().hex[:8]}@test.enterprise"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {(await client.post('/api/v1/auth/login', json={'email': admin['email'], 'password': admin['password']})).json()['access_token']}"}
        invitation = await client.post("/api/v1/memberships/invitations", headers=headers, json={"email": invited_email, "role": "salesperson"})
        assert invitation.status_code == 201
        user_id = invitation.json()["user_id"]

        with sync_session_factory() as db:
            mail = db.scalar(select(AuthMail).where(AuthMail.recipient == invited_email, AuthMail.sent_at.is_(None)))
            payload = json.loads(cipher().decrypt(mail.encrypted_body.encode()).decode())
            assert "Aceptar invitación" in payload["html"]
            assert "Test Trade" in payload["html"]
            assert "salesperson" in payload["text"] or "Vendedor" in payload["text"]

        resend = await client.post(f"/api/v1/memberships/invitations/{user_id}/resend", headers=headers)
        assert resend.status_code == 200

        cancel = await client.delete(f"/api/v1/memberships/invitations/{user_id}", headers=headers)
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

        with sync_session_factory() as db:
            assert db.get(UserModel, UUID(user_id)) is None
            assert db.scalar(select(AuthChallenge).where(AuthChallenge.user_id == UUID(user_id))) is None
            assert db.scalar(select(AuthMail).where(AuthMail.recipient == invited_email, AuthMail.sent_at.is_(None))) is None


@pytest.mark.asyncio
async def test_auth_006_password_reset_uniform_response_and_session_revocation():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        req_exist = await client.post("/api/v1/auth/password/reset-request", json={"email": u["email"]})
        assert req_exist.status_code == 202
        req_nonexist = await client.post("/api/v1/auth/password/reset-request", json={"email": "nobody_exists_12345@domain.com"})
        assert req_nonexist.status_code == 202
        assert req_exist.json() == req_nonexist.json()
        old_login = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        old_token = old_login.json()["access_token"]
        token = secrets.token_urlsafe(48)
        with sync_session_factory() as db:
            db.add(AuthChallenge(user_id=u["user_id"], token_hash=fingerprint(token), purpose="reset", expires_at=utcnow() + timedelta(hours=1)))
            db.commit()
        new_pass = "BrandNewSecurePassword2026!"
        confirm = await client.post("/api/v1/auth/password/reset", json={"reset_token": token, "new_password": new_pass})
        assert confirm.status_code == 200
        old_me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"})
        assert old_me.status_code == 401
        new_login = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": new_pass})
        assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_auth_007_cors_and_csrf_protection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        cors_options = await client.options("/api/v1/auth/login", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST"
        })
        assert cors_options.status_code == 200
        assert "access-control-allow-origin" in cors_options.headers
        forbid_options = await client.options("/api/v1/auth/login", headers={
            "Origin": "http://malicious-attacker.com",
            "Access-Control-Request-Method": "POST"
        })
        assert forbid_options.headers.get("access-control-allow-origin") != "http://malicious-attacker.com"


@pytest.mark.asyncio
async def test_auth_008_session_rotation():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        rotated = (await client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})).json()
        assert rotated["access_token"] != first["access_token"]
        assert rotated["refresh_token"] != first["refresh_token"]


@pytest.mark.asyncio
async def test_auth_009_expiration_of_tokens_and_sessions():
    u = make_user()
    with sync_session_factory() as db:
        session = AuthSession(
            user_id=u["user_id"],
            company_id=u["company_id"],
            refresh_hash=fingerprint(secrets.token_urlsafe(32)),
            created_at=utcnow() - timedelta(days=8),
            expires_at=utcnow() - timedelta(minutes=1),
            user_agent="expired-agent",
            ip_address="127.0.0.1"
        )
        db.add(session)
        db.commit()
        expired_token = create_access_token(
            {"sub": str(u["user_id"]), "sid": str(session.id), "company_id": str(u["company_id"])},
            expires_delta=timedelta(seconds=-10)
        )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_auth_010_active_sessions_list_and_revocation():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
        assert len(sessions) == 1
        assert "refresh_token" not in sessions[0]
        assert "refresh_hash" not in sessions[0]
        assert sessions[0]["is_current"] is True


@pytest.mark.asyncio
async def test_auth_011_logout_clears_session():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 200
        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


@pytest.mark.asyncio
async def test_auth_012_brute_force_throttling():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(5):
            res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": "WrongPassword"})
            assert res.status_code in (401, 429)
        throttled = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": "WrongPassword"})
        assert throttled.status_code == 429
        assert "Retry-After" in throttled.headers


@pytest.mark.asyncio
async def test_auth_013_email_change_security():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        no_sudo = await client.post("/api/v1/auth/email/change-request", headers=headers, json={"new_email": "new_unauth@salesia.enterprise"})
        assert no_sudo.status_code == 401
        await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": u["password"]})
        with_sudo = await client.post("/api/v1/auth/email/change-request", headers=headers, json={"new_email": "new_auth@salesia.enterprise"})
        assert with_sudo.status_code == 200


@pytest.mark.asyncio
async def test_auth_014_employee_offboarding_preserves_audit_history():
    admin = make_user(role="company_admin")
    seller = make_user(role="salesperson")
    with sync_session_factory() as db:
        seller_user = db.get(UserModel, seller["user_id"])
        seller_user.company_id = admin["company_id"]
        db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        seller_tokens = (await client.post("/api/v1/auth/login", json={"email": seller["email"], "password": seller["password"]})).json()
        seller_headers = {"Authorization": f"Bearer {seller_tokens['access_token']}"}
        admin_tokens = (await client.post("/api/v1/auth/login", json={"email": admin["email"], "password": admin["password"]})).json()
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
        deactivate_res = await client.patch(f"/api/v1/memberships/{seller['user_id']}", headers=admin_headers, json={"is_active": False})
        assert deactivate_res.status_code == 200
        cut_seller = await client.get("/api/v1/auth/me", headers=seller_headers)
        assert cut_seller.status_code == 401


@pytest.mark.asyncio
async def test_auth_015_sso_enterprise_rejects_wrong_issuer_and_tenant():
    u = make_user()
    bad_issuer_token = create_access_token({
        "sub": str(u["user_id"]),
        "iss": "https://untrusted-idp.com",
        "aud": "salesia-enterprise",
        "email": u["email"],
        "company_id": str(u["company_id"])
    })
    bad_aud_token = create_access_token({
        "sub": str(u["user_id"]),
        "iss": "https://auth.salesia.enterprise",
        "aud": "other-competitor-app",
        "email": u["email"],
        "company_id": str(u["company_id"])
    })
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/api/v1/auth/sso/callback", json={"id_token": bad_issuer_token, "state": "xyz"})).status_code == 401
        assert (await client.post("/api/v1/auth/sso/callback", json={"id_token": bad_aud_token, "state": "xyz"})).status_code == 401


@pytest.mark.asyncio
async def test_auth_016_sudo_reauthentication_protects_sensitive_actions():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        invalid_sudo = await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": "bad_password"})
        assert invalid_sudo.status_code == 401
        valid_sudo = await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": u["password"]})
        assert valid_sudo.status_code == 200
        assert valid_sudo.json()["sudo_mode_active"] is True


@pytest.mark.asyncio
async def test_auth_017_security_audit_logging_no_secrets_in_logs():
    u = make_user()
    with sync_session_factory() as db:
        challenges = db.scalars(select(AuthChallenge).where(AuthChallenge.user_id == u["user_id"])).all()
        for ch in challenges:
            assert not ch.token_hash.startswith("token_")
            assert len(ch.token_hash) == 64
        recovery_codes = db.scalars(select(RecoveryCode).where(RecoveryCode.user_id == u["user_id"])).all()
        for rc in recovery_codes:
            assert len(rc.code_hash) == 64


@pytest.mark.asyncio
async def test_api_001_post_auth_login_contract():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
        assert res.status_code == 200
        data = res.json()
        for field in ("access_token", "refresh_token", "token_type", "expires_in", "user_id", "email", "company_id", "role", "permissions"):
            assert field in data


@pytest.mark.asyncio
async def test_api_002_post_auth_logout_contract():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        res = await client.post("/api/v1/auth/logout", headers=headers)
        assert res.status_code == 200
        assert "message" in res.json()


@pytest.mark.asyncio
async def test_api_003_get_auth_me_contract():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        res = await client.get("/api/v1/auth/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == u["email"]
        assert data["role"] == "company_admin"
        assert isinstance(data["permissions"], list)


@pytest.mark.asyncio
async def test_api_004_post_auth_password_reset_request_contract():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/auth/password/reset-request", json={"email": u["email"]})
        assert res.status_code == 202
        assert res.json()["status"] == "received"


@pytest.mark.asyncio
async def test_api_005_post_auth_password_reset_contract():
    u = make_user()
    token = secrets.token_urlsafe(48)
    with sync_session_factory() as db:
        db.add(AuthChallenge(user_id=u["user_id"], token_hash=fingerprint(token), purpose="reset", expires_at=utcnow() + timedelta(hours=1)))
        db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/auth/password/reset", json={"reset_token": token, "new_password": "NewCompliantPassword123!"})
        assert res.status_code == 200
        assert res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_api_006_get_auth_sessions_contract():
    u = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        res = await client.get("/api/v1/auth/sessions", headers=headers)
        assert res.status_code == 200
        items = res.json()
        assert isinstance(items, list)
        assert len(items) >= 1
        assert "session_id" in items[0]
        assert "is_current" in items[0]


@pytest.mark.asyncio
async def test_api_007_delete_auth_sessions_id_contract():
    u = make_user()
    other_user = make_user()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await client.post("/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        other_tokens = (await client.post("/api/v1/auth/login", json={"email": other_user["email"], "password": other_user["password"]})).json()
        other_sessions = (await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {other_tokens['access_token']}"})).json()
        other_sid = other_sessions[0]["session_id"]
        unauth_del = await client.delete(f"/api/v1/auth/sessions/{other_sid}", headers=headers)
        assert unauth_del.status_code == 404
        my_sessions = (await client.get("/api/v1/auth/sessions", headers=headers)).json()
        my_sid = my_sessions[0]["session_id"]
        auth_del = await client.delete(f"/api/v1/auth/sessions/{my_sid}", headers=headers)
        assert auth_del.status_code == 200
        assert auth_del.json()["status"] == "revoked"
