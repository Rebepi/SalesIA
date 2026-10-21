import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.operaciones.infrastructure_models import ApiCredential, LegalHold
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import AuditLogModel, CompanyModel, CustomerModel, UserModel


@pytest.fixture
def governance_identity():
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Gobierno", trade_name="Gobierno")
        db.add(company)
        db.flush()
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        customer = CustomerModel(company_id=company.id, code=uuid4().hex[:8], doc_type="RUC", doc_number=uuid4().hex, legal_name="Persona Original", email="private@example.com", phone="999999999")
        db.add_all([user, customer])
        db.commit()
        return {"email": user.email, "password": password, "company": company.id, "customer": customer.id}


async def client_for(data):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    login = await client.post("/api/v1/auth/login", json={"email": data["email"], "password": data["password"]})
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    return client


@pytest.mark.asyncio
async def test_api_keys_and_legal_holds_are_durable(governance_identity):
    client = await client_for(governance_identity)
    try:
        created = await client.post("/api/v1/security/api-keys", json={"name": "Integración", "scope": "integration"})
        assert created.status_code == 201, created.text
        assert created.json()["raw_secret_key"].startswith("sal_live_")
        key_id = created.json()["key_id"]
        assert (await client.get("/api/v1/security/api-keys")).json()["count"] == 1
        assert (await client.delete(f"/api/v1/security/api-keys/{key_id}")).status_code == 200
        hold = {"entity_type": "customer", "entity_id": str(governance_identity["customer"]), "hold_reason": "Investigación contractual", "action": "place"}
        assert (await client.post("/api/v1/privacy/legal-hold", json=hold)).status_code == 200
        anonymize = {"customer_id": str(governance_identity["customer"]), "reason": "Solicitud del titular"}
        assert (await client.post("/api/v1/privacy/anonymize-customer", json=anonymize)).status_code == 423
        assert (await client.post("/api/v1/privacy/legal-hold", json={**hold, "action": "lift"})).status_code == 200
        assert (await client.post("/api/v1/privacy/anonymize-customer", json=anonymize)).status_code == 200
        with sync_session_factory() as db:
            key = db.get(ApiCredential, uuid4())
            customer = db.get(CustomerModel, governance_identity["customer"])
            assert key is None
            assert customer.email is None and customer.phone is None and customer.doc_type == "ANON"
            assert db.scalar(select(LegalHold).where(LegalHold.company_id == governance_identity["company"])).lifted_at is not None
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_audit_log_is_sealed_and_append_only(governance_identity):
    client = await client_for(governance_identity)
    try:
        created = await client.post("/api/v1/audit/logs", json={"action": "MANUAL_REVIEW", "entity_type": "Customer", "entity_id": str(governance_identity["customer"]), "payload_diff": {"reviewed": True}})
        assert created.status_code == 201, created.text
        log_id = created.json()["id"]
        assert len(created.json()["chain_hash"]) == 64
        with sync_session_factory() as db:
            row = db.get(AuditLogModel, UUID(log_id))
            row.action = "TAMPERED"
            with pytest.raises(DBAPIError):
                db.commit()
    finally:
        await client.aclose()
