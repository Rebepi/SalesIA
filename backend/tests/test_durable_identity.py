import secrets
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.modules.seguridad.infrastructure.models import AuthSession, AuthChallenge
from salesia.modules.seguridad.infrastructure.security import hash_password, generate_totp_code
from salesia.modules.seguridad.infrastructure.sessions import utcnow, fingerprint
from datetime import timedelta


@pytest.fixture
def identity():
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Prueba aislada", trade_name="Prueba")
        db.add(company)
        db.flush()
        email = f"{uuid4().hex}@example.com"
        password = secrets.token_urlsafe(24)
        user = UserModel(company_id=company.id, email=email, hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add(user)
        db.commit()
        return {"email": email, "password": password, "user_id": user.id}


async def login(client, identity, **extra):
    return await client.post("/api/v1/auth/login", json={"email": identity["email"], "password": identity["password"], **extra})


@pytest.mark.asyncio
async def test_unknown_user_and_demo_credentials_are_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for email, password in [(f"{uuid4().hex}@example.com", "invented-password"), ("admin@empresa.com", "Admin123456!")]:
            response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
            assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_access_and_refresh(identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        result = await login(client, identity)
        assert result.status_code == 200, result.text
        tokens = result.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        sessions = await client.get("/api/v1/auth/sessions", headers=headers)
        assert len(sessions.json()) == 1
        assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})).status_code == 401
        assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 200
        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
        assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code == 401


@pytest.mark.asyncio
async def test_refresh_replay_revokes_family(identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = (await login(client, identity)).json()
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert response.status_code == 200, response.text
        second = response.json()
        assert second["refresh_token"] != first["refresh_token"]
        assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})).status_code == 401
        assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"})).status_code == 401


@pytest.mark.asyncio
async def test_live_permissions_and_disabled_user(identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await login(client, identity)).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        with sync_session_factory() as db:
            user = db.get(UserModel, identity["user_id"])
            user.role = "salesperson"
            db.commit()
        assert (await client.get("/api/v1/users", headers=headers)).status_code == 403
        with sync_session_factory() as db:
            db.get(UserModel, identity["user_id"]).is_active = False
            db.commit()
        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


@pytest.mark.asyncio
async def test_mfa_enforced_and_recovery_single_use(identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await login(client, identity)).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        result = await client.post("/api/v1/auth/mfa/setup", headers=headers, json={"password": identity["password"]})
        assert result.status_code == 200, result.text
        factor = result.json()
        assert (await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": "abcd-efgh"})).status_code == 400
        code = generate_totp_code(factor["totp_secret"])
        assert (await client.post("/api/v1/auth/mfa/verify", headers=headers, json={"code": code})).status_code == 200
        assert (await login(client, identity)).status_code == 401
        assert (await login(client, identity, mfa_code=code)).status_code == 401
        recovery = factor["recovery_codes"][0]
        assert (await login(client, identity, mfa_code=recovery)).status_code == 200
        assert (await login(client, identity, mfa_code=recovery)).status_code == 401


@pytest.mark.asyncio
async def test_password_reset_changes_password_and_revokes_sessions(identity):
    token = secrets.token_urlsafe(48)
    with sync_session_factory() as db:
        db.add(AuthChallenge(user_id=identity["user_id"], token_hash=fingerprint(token), purpose="reset", expires_at=utcnow()+timedelta(minutes=10)))
        db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        old = (await login(client, identity)).json()
        new_password = secrets.token_urlsafe(24)
        payload = {"reset_token": token, "new_password": new_password}
        assert (await client.post("/api/v1/auth/password/reset", json=payload)).status_code == 200
        assert (await client.post("/api/v1/auth/password/reset", json=payload)).status_code == 401
        assert (await login(client, identity)).status_code == 401
        assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old['access_token']}"})).status_code == 401
        identity["password"] = new_password
        assert (await login(client, identity)).status_code == 200


@pytest.mark.asyncio
async def test_sudo_rejects_magic_password(identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tokens = (await login(client, identity)).json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        assert (await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": "valid_password"})).status_code == 401
        assert (await client.post("/api/v1/auth/sudo/verify", headers=headers, json={"password": identity["password"]})).status_code == 200
        with sync_session_factory() as db:
            session = db.scalar(select(AuthSession).where(AuthSession.user_id == identity["user_id"]))
            assert session.sudo_until is not None
