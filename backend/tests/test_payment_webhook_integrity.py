import json
import secrets
import time
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.operaciones.infrastructure_models import WebhookReceipt
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.workers import sign_webhook_payload


@pytest.fixture
def webhook_identity():
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Webhook", trade_name="Webhook")
        db.add(company)
        db.flush()
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add(user)
        db.commit()
        return {"email": user.email, "password": password, "company": company.id}


@pytest.mark.asyncio
async def test_webhook_requires_real_secret_window_and_deduplicates(webhook_identity):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json={"email": webhook_identity["email"], "password": webhook_identity["password"]})
        auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        created = await client.post("/api/v1/payment-connections", json={"provider": "custom"}, headers=auth)
        assert created.status_code == 201, created.text
        connection = created.json()
        body = json.dumps({"type": "payment.confirmed", "payment_id": uuid4().hex}, separators=(",", ":")).encode()
        timestamp = int(time.time())
        signed = str(timestamp).encode() + b"." + body
        headers = {"X-Webhook-Timestamp": str(timestamp), "X-Webhook-Event-Id": "evt-1", "X-Webhook-Signature": sign_webhook_payload(signed, connection["webhook_secret"]), "Content-Type": "application/json"}
        first = await client.post(f"/api/v1/webhooks/payments/{connection['connection_id']}", content=body, headers=headers)
        assert first.status_code == 200, first.text
        second = await client.post(f"/api/v1/webhooks/payments/{connection['connection_id']}", content=body, headers=headers)
        assert second.json()["status"] == "duplicate"
        invalid = {**headers, "X-Webhook-Event-Id": "evt-2", "X-Webhook-Signature": sign_webhook_payload(signed, "invented")}
        assert (await client.post(f"/api/v1/webhooks/payments/{connection['connection_id']}", content=body, headers=invalid)).status_code == 401
        stale_time = timestamp - 301
        stale = {**headers, "X-Webhook-Event-Id": "evt-3", "X-Webhook-Timestamp": str(stale_time), "X-Webhook-Signature": sign_webhook_payload(str(stale_time).encode() + b"." + body, connection["webhook_secret"])}
        assert (await client.post(f"/api/v1/webhooks/payments/{connection['connection_id']}", content=body, headers=stale)).status_code == 401
        with sync_session_factory() as db:
            assert db.scalar(select(func.count()).select_from(WebhookReceipt).where(WebhookReceipt.company_id == webhook_identity["company"])) == 1
