from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import CompanyModel, UserModel, ProductModel
from salesia.modules.operaciones.infrastructure_models import Notification
from salesia.modules.seguridad.infrastructure.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    generate_totp_code,
    verify_totp_code
)
from salesia.shared.infrastructure.workers import (
    compute_jitter_backoff,
    sign_webhook_payload,
    verify_webhook_signature
)
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


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
                legal_name="EMPRESA MATRIZ TEST S.A.C.",
                trade_name="SALESIA CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp)
            session.flush()

        user = session.execute(
            select(UserModel).where(UserModel.id == TEST_USER_ID)
        ).scalar_one_or_none()
        if not user:
            user = UserModel(
                id=TEST_USER_ID,
                company_id=TEST_COMPANY_ID,
                email="admin_api_f05@salesia.enterprise",
                hashed_password=hash_password("SuperSecretSecurePassword2026!"),
                role="company_admin",
                is_active=True
            )
            session.add(user)
        else:
            user.company_id = TEST_COMPANY_ID
            user.hashed_password = hash_password("SuperSecretSecurePassword2026!")
            user.is_active = True
            user.role = "company_admin"

        admin = session.execute(
            select(UserModel).where(UserModel.email == "admin@salesia.enterprise")
        ).scalar_one_or_none()
        if admin:
            admin.hashed_password = hash_password("SuperSecretSecurePassword2026!")
            admin.is_active = True
            admin.mfa_enabled = False
        else:
            admin = UserModel(
                id=uuid4(),
                company_id=TEST_COMPANY_ID,
                email="admin@salesia.enterprise",
                hashed_password=hash_password("SuperSecretSecurePassword2026!"),
                role="company_admin",
                is_active=True
            )
            session.add(admin)
        session.commit()
    yield


@pytest.fixture
def auth_headers():
    with sync_session_factory() as session:
        user = session.execute(
            select(UserModel).where(UserModel.id == TEST_USER_ID)
        ).scalar_one()
        identity = create_durable_identity(
            session,
            company_id=TEST_COMPANY_ID,
            user_id=TEST_USER_ID,
            role="company_admin",
            email=user.email,
            password="SuperSecretSecurePassword2026!"
        )
        return identity["headers"]


@pytest.mark.asyncio
async def test_auth_security_crypto_primitives():
    password = "SuperSecretSecurePassword2026!"
    hashed = hash_password(password)
    assert hashed.startswith(("$argon2id$", "pbkdf2_sha256$"))
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

    totp_secret = generate_totp_secret()
    code = generate_totp_code(totp_secret)
    assert len(code) == 6
    assert verify_totp_code(totp_secret, code) is True
    assert verify_totp_code(totp_secret, "000000") is False

    user_id = uuid4()
    company_id = uuid4()
    access = create_access_token(user_id=user_id, email="ceo@salesia.com", company_id=company_id, role="DIRECTOR_GENERAL")
    payload = decode_token(access)
    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == str(company_id)
    assert payload["role"] == "DIRECTOR_GENERAL"
    assert payload["token_type"] == "access"

    refresh = create_refresh_token(user_id=user_id, email="ceo@salesia.com", company_id=company_id, role="DIRECTOR_GENERAL")
    r_payload = decode_token(refresh)
    assert r_payload["token_type"] == "refresh"


@pytest.mark.asyncio
async def test_worker_backoff_and_webhook_signatures():
    backoffs = [compute_jitter_backoff(attempt) for attempt in range(1, 6)]
    assert len(backoffs) == 5
    for b in backoffs:
        assert b >= 2.0

    secret = "whsec_test_secret_key_12345"
    payload = b'{"event":"PAYMENT_RECEIVED","amount":"150.00"}'
    sig = sign_webhook_payload(payload, secret)
    assert sig.startswith("sha256=")
    assert verify_webhook_signature(payload, secret, sig) is True
    assert verify_webhook_signature(b'tampered payload', secret, sig) is False


@pytest.mark.asyncio
async def test_api_auth_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@salesia.enterprise", "password": "SuperSecretSecurePassword2026!"}
        )
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_res.status_code == 200
        user_info = me_res.json()
        assert user_info["email"] == "admin@salesia.enterprise"

        unauth_res = await client.get("/api/v1/auth/me")
        assert unauth_res.status_code == 401


@pytest.mark.asyncio
async def test_api_statistical_engine(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mean_res = await client.post(
            "/api/v1/statistics/mean",
            json={"values": ["10.5", "20.5", "30.0", "40.0"]},
            headers=auth_headers
        )
        assert mean_res.status_code == 200
        assert mean_res.json()["mean"] == "25.250000"

        median_res = await client.post(
            "/api/v1/statistics/median",
            json={"values": ["10", "20", "30", "40", "50"]},
            headers=auth_headers
        )
        assert median_res.status_code == 200
        assert median_res.json()["median"] == "30.000000"

        compare_res = await client.post(
            "/api/v1/statistics/compare",
            json={
                "label_a": "Norte",
                "values_a": ["100", "200"],
                "label_b": "Sur",
                "values_b": ["150", "250"]
            },
            headers=auth_headers
        )
        assert compare_res.status_code == 200
        comp = compare_res.json()
        assert comp["differences"]["delta_mean"] == "50.000000"

        var_res = await client.post(
            "/api/v1/random-variables/analyze",
            json={
                "name": "tiempo_entrega",
                "scale": "quantitative_continuous",
                "observations": ["12.5", "14.2", "11.8", "15.0", "13.1"]
            },
            headers=auth_headers
        )
        assert var_res.status_code == 200
        assert var_res.json()["observations_count"] == 5

        prob_res = await client.post(
            "/api/v1/probability/events",
            json={
                "event_a_count": 40,
                "event_b_count": 30,
                "intersection_count": 10,
                "sample_space_size": 100
            },
            headers=auth_headers
        )
        assert prob_res.status_code == 200
        assert prob_res.json()["probability_union"] == "0.600000"

        bayes_res = await client.post(
            "/api/v1/probability/bayes",
            json={
                "prior_a": "0.0100",
                "likelihood_b_given_a": "0.9500",
                "likelihood_b_given_not_a": "0.0500"
            },
            headers=auth_headers
        )
        assert bayes_res.status_code == 200
        assert "posterior_a_given_b" in bayes_res.json()


@pytest.mark.asyncio
async def test_api_commercial_and_supply_chain(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cust_res = await client.post(
            "/api/v1/customers",
            headers=auth_headers,
            json={
                "code": f"CLI-{uuid4().hex[:6]}",
                "doc_type": "RUC",
                "doc_number": f"20{uuid4().int % 1000000000:09d}",
                "legal_name": "CORPORACION LOGISTICA ANDINA S.A.C.",
                "credit_limit": 50000.00
            }
        )
        assert cust_res.status_code == 201

        prod_res = await client.post(
            "/api/v1/products",
            headers=auth_headers,
            json={
                "sku": f"PROD-{uuid4().hex[:6]}",
                "name": "Laptop Corporativa Ultra 16GB",
                "category": "Computo",
                "unit_cost": 850.00,
                "unit_price": 1250.00,
                "tax_rate": 0.18
            }
        )
        assert prod_res.status_code == 201

        inv_res = await client.get("/api/v1/inventory", headers=auth_headers)
        assert inv_res.status_code == 200

        dash_res = await client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert dash_res.status_code == 200
        assert "total_revenue" in dash_res.json()


@pytest.mark.asyncio
async def test_api_operations_and_search(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with sync_session_factory() as session:
            prod = session.scalar(select(ProductModel).where(ProductModel.company_id == TEST_COMPANY_ID, ProductModel.name.ilike("%Corporativa%")))
            if not prod:
                prod = ProductModel(
                    id=uuid4(),
                    company_id=TEST_COMPANY_ID,
                    sku=f"SKU-{uuid4().hex[:6]}",
                    name="Laptop Corporativa Ultra 16GB",
                    category="Computo",
                    unit_price=Decimal("1250.00"),
                    unit_cost=Decimal("850.00"),
                    tax_rate=Decimal("0.18"),
                    is_active=True
                )
                session.add(prod)
            admin_user = session.scalar(select(UserModel).where(UserModel.id == TEST_USER_ID))
            notif = session.scalar(select(Notification).where(Notification.company_id == TEST_COMPANY_ID, Notification.user_id == admin_user.id, Notification.read_at.is_(None)))
            if not notif:
                notif = Notification(
                    id=uuid4(),
                    company_id=TEST_COMPANY_ID,
                    user_id=admin_user.id,
                    title="Alerta del Sistema",
                    message="Notificacion no leida",
                    event_type="system"
                )
                session.add(notif)
            session.commit()

        search_res = await client.get("/api/v1/search?q=Corporativa", headers=auth_headers)
        assert search_res.status_code == 200
        assert "results" in search_res.json()
        assert len(search_res.json()["results"]) >= 1

        notif_res = await client.get("/api/v1/notifications", headers=auth_headers)
        assert notif_res.status_code == 200
        assert notif_res.json()["unread_count"] >= 1

        csv_content = b"code,doc_type,doc_number,legal_name\nC1,RUC,20999001,Cliente Uno\n"
        intent = await client.post(
            "/api/v1/attachments/upload-intents",
            headers=auth_headers,
            json={
                "file_name": "catalogo_precios_2026.csv",
                "mime_type": "text/csv",
                "file_size_bytes": len(csv_content),
                "related_entity_type": "import"
            }
        )
        assert intent.status_code == 201
        data = intent.json()
        upload_res = await client.put(
            data["upload_url"],
            content=csv_content,
            headers={**auth_headers, "X-Upload-Token": data["upload_token"], "Content-Type": "text/csv"}
        )
        assert upload_res.status_code == 200
        complete_res = await client.post(
            f"/api/v1/attachments/{data['attachment_id']}/complete",
            headers=auth_headers
        )
        assert complete_res.status_code == 200

        import_res = await client.post(
            "/api/v1/imports",
            headers={**auth_headers, "Idempotency-Key": uuid4().hex},
            json={
                "target_entity": "customers",
                "attachment_id": data["attachment_id"]
            }
        )
        assert import_res.status_code == 202
        assert import_res.json()["status"] == "staged"

