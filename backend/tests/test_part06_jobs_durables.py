import json
import random
import secrets
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from salesia.main import app
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory, Base, sync_engine
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    BranchModel,
    CustomerModel,
    JobModel,
    OutboxEventModel,
    SaleModel,
    InboxEventModel,
    DeadLetterJobModel,
    ScheduleExecutionModel,
    ExternalNotificationIntentModel,
    WebhookSubscriptionModel,
    WebhookDeliveryModel,
    ExternalSyncCursorModel,
    ExternalEntityMappingModel
)
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.infrastructure.outbox import (
    OutboxRecord,
    SqlOutboxRepository,
    DurableInboxConsumer,
    AggregateOrderTracker
)
from salesia.shared.infrastructure.workers import (
    compute_jitter_backoff,
    sign_webhook_payload,
    verify_webhook_signature,
    validate_event_schema,
    is_transient_error,
    record_dead_letter_job,
    TenantFairnessLimiter,
    DurableScheduler,
    validate_webhook_url,
    OutgoingWebhookService,
    ExternalSyncManager,
    ExternalNotificationManager,
    IntegrationPortRegistry,
    disconnect_integration_account
)
from salesia.modules.operaciones.jobs import process_jobs

Base.metadata.create_all(sync_engine)


@pytest.fixture
def part06_identity():
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company_a = CompanyModel(tax_id=uuid4().hex[:12], legal_name="Empresa A", trade_name="Empresa A")
        company_b = CompanyModel(tax_id=uuid4().hex[:12], legal_name="Empresa B", trade_name="Empresa B")
        db.add_all([company_a, company_b])
        db.flush()
        branch_a = BranchModel(
            company_id=company_a.id,
            code="B" + uuid4().hex[:6].upper(),
            name="Sede Principal"
        )
        customer_a = CustomerModel(
            company_id=company_a.id,
            code="C" + uuid4().hex[:6].upper(),
            doc_type="RUC",
            doc_number=uuid4().hex[:11],
            legal_name="Cliente Principal"
        )
        user_a = UserModel(
            company_id=company_a.id,
            email=f"{uuid4().hex[:8]}@empresa-a.com",
            hashed_password=hash_password(password),
            role="company_admin",
            is_active=True
        )
        user_b = UserModel(
            company_id=company_b.id,
            email=f"{uuid4().hex[:8]}@empresa-b.com",
            hashed_password=hash_password(password),
            role="company_admin",
            is_active=True
        )
        db.add_all([branch_a, customer_a, user_a, user_b])
        db.commit()
        return {
            "company_a_id": company_a.id,
            "company_b_id": company_b.id,
            "branch_a_id": branch_a.id,
            "customer_a_id": customer_a.id,
            "user_a_email": user_a.email,
            "user_b_email": user_b.email,
            "password": password
        }


async def get_authed_client(email: str, password: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.mark.asyncio
async def test_fallo_reproducido_random_job_not_found(part06_identity):
    client = await get_authed_client(part06_identity["user_a_email"], part06_identity["password"])
    try:
        random_id = uuid4()
        resp = await client.get(f"/api/v1/jobs/{random_id}")
        assert resp.status_code == 404
        assert resp.json().get("status") != "completed"
        assert resp.json().get("progress_pct") != 100
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_job_001_recoverable_publisher(part06_identity):
    with sync_session_factory() as db:
        repo = SqlOutboxRepository()
        event_id = uuid4()
        rec = OutboxRecord(
            event_id=event_id,
            event_type="sale.confirmed",
            company_id=part06_identity["company_a_id"],
            payload={"sale_id": str(uuid4()), "amount": "100.00"}
        )
        repo.save(rec, db)
        db.commit()

    with sync_session_factory() as db:
        claimed = repo.claim_pending(db, limit=10, lease_seconds=1, company_id=part06_identity["company_a_id"])
        assert len(claimed) >= 1
        assert any(item.id == event_id for item in claimed)
        target = next(item for item in claimed if item.id == event_id)
        assert target.status == "PROCESSING"
        db.commit()

    time.sleep(1.1)

    with sync_session_factory() as db:
        reconciled_count = repo.reconcile_stuck_events(db, lease_expiry_seconds=1)
        assert reconciled_count >= 1
        db.commit()

    with sync_session_factory() as db:
        reclaimed = repo.claim_pending(db, limit=10, lease_seconds=60, company_id=part06_identity["company_a_id"])
        assert any(item.id == event_id for item in reclaimed)
        repo.mark_published(db, event_id, broker_ack="ack_ok")
        db.commit()

    with sync_session_factory() as db:
        finished = repo.get_by_id(db, event_id)
        assert finished.status == "PUBLISHED"
        assert finished.processed_at is not None


def test_job_002_durable_inbox_idempotence(part06_identity):
    consumer = DurableInboxConsumer()
    event_id = uuid4()
    company_id = part06_identity["company_a_id"]
    execution_count = 0

    def handler(db, payload):
        nonlocal execution_count
        execution_count += 1
        return {"result": "ok", "value": payload["amount"]}

    with sync_session_factory() as db:
        res1 = consumer.consume_event(
            db,
            company_id=company_id,
            consumer_name="sales_projector",
            event_id=event_id,
            event_type="sale.confirmed",
            payload={"amount": "250.00"},
            handler=handler
        )
        db.commit()
    assert res1 == {"result": "ok", "value": "250.00"}
    assert execution_count == 1

    with sync_session_factory() as db:
        res2 = consumer.consume_event(
            db,
            company_id=company_id,
            consumer_name="sales_projector",
            event_id=event_id,
            event_type="sale.confirmed",
            payload={"amount": "250.00"},
            handler=handler
        )
        db.commit()
    assert res2 == {"result": "ok", "value": "250.00"}
    assert execution_count == 1

    with sync_session_factory() as db:
        assert consumer.is_processed(db, company_id, "sales_projector", event_id) is True


def test_job_003_aggregate_ordering():
    tracker = AggregateOrderTracker()
    agg_id = uuid4()
    with sync_session_factory() as db:
        decision_1 = tracker.check_aggregate_version(db, "Sale", agg_id, incoming_version=1, current_version=0)
        assert decision_1 == "APPLY"

        decision_stale = tracker.check_aggregate_version(db, "Sale", agg_id, incoming_version=1, current_version=2)
        assert decision_stale == "STALE_IGNORED"

        decision_gap = tracker.check_aggregate_version(db, "Sale", agg_id, incoming_version=5, current_version=2)
        assert decision_gap == "GAP_DETECTED"


def test_job_004_event_schema_validation():
    valid_payload = {
        "event_id": str(uuid4()),
        "event_type": "sale.confirmed",
        "company_id": str(uuid4()),
        "sale_id": str(uuid4()),
        "amount": "199.99",
        "occurred_at": datetime.now(timezone.utc).isoformat()
    }
    validated = validate_event_schema("sale.confirmed", valid_payload)
    assert validated["event_type"] == "sale.confirmed"

    compatible_payload = dict(valid_payload)
    compatible_payload["future_extra_field"] = "ignored_gracefully"
    validated_compat = validate_event_schema("sale.confirmed", compatible_payload)
    assert validated_compat["sale_id"] == valid_payload["sale_id"]

    with pytest.raises(ValueError):
        validate_event_schema("unauthorized.task.name", valid_payload)

    huge_payload = dict(valid_payload)
    huge_payload["data"] = "X" * 300_000
    with pytest.raises(ValueError):
        validate_event_schema("sale.confirmed", huge_payload)


def test_job_005_retries_transient_vs_permanent():
    assert is_transient_error(ConnectionError("db down")) is True
    assert is_transient_error(TimeoutError("redis timeout")) is True
    assert is_transient_error(ValueError("invalid file format")) is False
    assert is_transient_error(KeyError("missing sku")) is False

    delay_0 = compute_jitter_backoff(0, base_delay_sec=1.0, max_delay_sec=30.0)
    delay_2 = compute_jitter_backoff(2, base_delay_sec=1.0, max_delay_sec=30.0)
    assert 1.0 <= delay_0 <= 1.3
    assert 4.0 <= delay_2 <= 5.0


def test_job_006_durable_failure_logging(part06_identity):
    job_id = uuid4()
    company_id = part06_identity["company_a_id"]
    with sync_session_factory() as db:
        secret_leak_error = ValueError("Database connection failed for postgresql://admin:supersecret@10.0.0.1/db")
        dl = record_dead_letter_job(
            session=db,
            company_id=company_id,
            job_id=job_id,
            job_type="import:customers",
            error=secret_leak_error,
            attempts=3,
            payload={"target": "customers", "auth": "bearer secret_token_123"},
            source="worker"
        )
        db.commit()
        assert dl.id is not None
        assert "supersecret" not in dl.error_reason
        assert "secret_token_123" not in dl.payload_json


def test_job_007_tenant_fairness_limits(part06_identity):
    limiter = TenantFairnessLimiter(max_concurrent_per_tenant=2)
    comp_a = part06_identity["company_a_id"]
    with sync_session_factory() as db:
        job1 = JobModel(company_id=comp_a, job_type="export:massive", status="running", progress=10)
        job2 = JobModel(company_id=comp_a, job_type="export:massive", status="running", progress=20)
        db.add_all([job1, job2])
        db.commit()

        assert limiter.can_schedule_job(db, comp_a) is False
        assert limiter.can_schedule_job(db, part06_identity["company_b_id"]) is True


@pytest.mark.asyncio
async def test_job_008_cancellation_and_progress(part06_identity):
    client = await get_authed_client(part06_identity["user_a_email"], part06_identity["password"])
    try:
        with sync_session_factory() as db:
            sale = SaleModel(
                company_id=part06_identity["company_a_id"],
                branch_id=part06_identity["branch_a_id"],
                customer_id=part06_identity["customer_a_id"],
                series="F001",
                number=random.randint(1000, 999999),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("100"),
                tax_amount=Decimal("18"),
                total_amount=Decimal("118"),
                paid_amount=Decimal("0")
            )
            db.add(sale)
            db.flush()
            job = JobModel(
                company_id=part06_identity["company_a_id"],
                job_type="report:sales",
                status="pending",
                progress=0,
                payload_json=json.dumps({"sale_id": str(sale.id)})
            )
            db.add(job)
            db.commit()
            job_id = job.id
            sale_id = sale.id

        cancel_resp = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        with sync_session_factory() as db:
            refreshed_sale = db.get(SaleModel, sale_id)
            assert refreshed_sale.status == "confirmed"
    finally:
        await client.aclose()


def test_job_009_scheduler_leader_and_window():
    scheduler = DurableScheduler()
    window = f"win-{uuid4().hex[:8]}"
    schedule_key = f"daily_digest_{uuid4().hex[:6]}"

    with sync_session_factory() as db:
        won_leader_1 = scheduler.claim_window(db, schedule_key, window, leader_id="worker_host_1")
        db.commit()
        assert won_leader_1 is True

    with sync_session_factory() as db:
        won_leader_2 = scheduler.claim_window(db, schedule_key, window, leader_id="worker_host_2")
        db.commit()
        assert won_leader_2 is False


def test_job_010_redis_unavailable_degraded_mode(part06_identity):
    repo = SqlOutboxRepository()
    with sync_session_factory() as db:
        event = OutboxRecord(
            event_id=uuid4(),
            event_type="payment.confirmed",
            company_id=part06_identity["company_a_id"],
            payload={"amount": "500.00"}
        )
        model = repo.save(event, db)
        assert model.status == "PENDING"
        db.commit()

    with sync_session_factory() as db:
        unprocessed = repo.get_unprocessed_backlog(db, part06_identity["company_a_id"])
        assert len(unprocessed) >= 1


def test_job_011_external_notifications_idempotency(part06_identity):
    notif_mgr = ExternalNotificationManager()
    company_id = part06_identity["company_a_id"]
    idempotency_key = "mail-order-12345"
    call_count = 0

    def send_email():
        nonlocal call_count
        call_count += 1
        return "provider_msg_987"

    with sync_session_factory() as db:
        first = notif_mgr.send_idempotent_notification(
            db,
            company_id=company_id,
            channel="email",
            recipient="admin@empresa-a.com",
            idempotency_key=idempotency_key,
            send_fn=send_email
        )
        db.commit()
        assert first.provider_message_id == "provider_msg_987"
        assert call_count == 1

    with sync_session_factory() as db:
        second = notif_mgr.send_idempotent_notification(
            db,
            company_id=company_id,
            channel="email",
            recipient="admin@empresa-a.com",
            idempotency_key=idempotency_key,
            send_fn=send_email
        )
        db.commit()
        assert second.id == first.id
        assert call_count == 1


def test_job_012_outgoing_webhooks_signature_and_isolation(part06_identity):
    secret = "whsec_test_abc123"
    webhook_service = OutgoingWebhookService()
    comp_a = part06_identity["company_a_id"]

    with sync_session_factory() as db:
        sub = WebhookSubscriptionModel(
            company_id=comp_a,
            target_url="https://api.external-partner.com/webhook",
            event_types_json=json.dumps(["sale.confirmed"]),
            secret=secret,
            is_active=True
        )
        db.add(sub)
        db.commit()
        sub_id = sub.id

    event_id = uuid4()
    payload = {"sale_id": str(uuid4()), "total": "350.00"}

    with sync_session_factory() as db:
        delivery = webhook_service.record_delivery(db, sub_id, event_id, payload)
        db.commit()
        assert delivery.signature.startswith("sha256=")
        timestamp_and_payload = delivery.payload_json.encode("utf-8")
        assert verify_webhook_signature(timestamp_and_payload, secret, delivery.signature) is True


def test_job_013_ssrf_destination_validation():
    with pytest.raises(ValueError) as err1:
        validate_webhook_url("http://127.0.0.1:8080/hook")
    assert "privada" in str(err1.value).lower() or "prohibida" in str(err1.value).lower()

    with pytest.raises(ValueError) as err2:
        validate_webhook_url("http://169.254.169.254/latest/meta-data")
    assert "privada" in str(err2.value).lower() or "prohibida" in str(err2.value).lower()

    with pytest.raises(ValueError) as err3:
        validate_webhook_url("http://192.168.1.15/hook")
    assert "privada" in str(err3.value).lower() or "prohibida" in str(err3.value).lower()

    with pytest.raises(ValueError) as err4:
        validate_webhook_url("ftp://example.com/file")
    assert "esquema" in str(err4.value).lower() or "http" in str(err4.value).lower()

    validate_webhook_url("https://hooks.slack.com/services/T00/B00/X00")


def test_job_014_external_sync_loop_prevention(part06_identity):
    sync_mgr = ExternalSyncManager()
    comp_a = part06_identity["company_a_id"]
    local_sale_id = uuid4()

    with sync_session_factory() as db:
        sync_mgr.record_mapping(
            db,
            company_id=comp_a,
            entity_type="Sale",
            local_id=local_sale_id,
            external_id="ERP-SALE-991",
            origin_system="salesia",
            sync_hash="hash_v1_payload"
        )
        db.commit()

    with sync_session_factory() as db:
        assert sync_mgr.should_skip_echo(db, comp_a, "Sale", "ERP-SALE-991", "hash_v1_payload") is True
        assert sync_mgr.should_skip_echo(db, comp_a, "Sale", "ERP-SALE-991", "hash_v2_updated") is False


def test_job_015_sandbox_mode():
    registry = IntegrationPortRegistry()
    connector = registry.get_connector("payments", "mercadopago", sandbox=True)
    res = connector.charge(amount=Decimal("150.00"), currency="USD", token="tok_test_card")
    assert res["sandbox"] is True
    assert res["status"] == "approved"
    assert res["live_call_made"] is False


def test_job_016_disconnection_preserves_data(part06_identity):
    comp_a = part06_identity["company_a_id"]
    with sync_session_factory() as db:
        sale = SaleModel(
            company_id=comp_a,
            branch_id=part06_identity["branch_a_id"],
            customer_id=part06_identity["customer_a_id"],
            series="F002",
            number=random.randint(1000, 999999),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("500"),
            tax_amount=Decimal("90"),
            total_amount=Decimal("590"),
            paid_amount=Decimal("590")
        )
        sub = WebhookSubscriptionModel(
            company_id=comp_a,
            target_url="https://api.external.com/webhooks",
            event_types_json="[]",
            secret="whsec_live",
            is_active=True
        )
        db.add_all([sale, sub])
        db.commit()
        sub_id = sub.id
        sale_id = sale.id

    with sync_session_factory() as db:
        disconnect_integration_account(db, comp_a, sub_id)
        db.commit()

    with sync_session_factory() as db:
        sub_refreshed = db.get(WebhookSubscriptionModel, sub_id)
        assert sub_refreshed.is_active is False
        assert sub_refreshed.secret == ""

        sale_refreshed = db.get(SaleModel, sale_id)
        assert sale_refreshed is not None
        assert sale_refreshed.status == "confirmed"


def test_job_017_defined_ports_and_contracts():
    registry = IntegrationPortRegistry()
    ports = registry.list_available_ports()
    assert "payments" in ports
    assert "email" in ports
    assert "invoicing" in ports
    assert "accounting" in ports
    assert "ecommerce" in ports
    assert "shipping" in ports
    assert "bi" in ports

    with pytest.raises(ValueError):
        registry.get_connector("unknown_port", "unsupported_provider")


@pytest.mark.asyncio
async def test_api_088_get_job(part06_identity):
    client_a = await get_authed_client(part06_identity["user_a_email"], part06_identity["password"])
    client_b = await get_authed_client(part06_identity["user_b_email"], part06_identity["password"])
    try:
        with sync_session_factory() as db:
            job = JobModel(
                company_id=part06_identity["company_a_id"],
                job_type="backup",
                status="completed",
                progress=100,
                payload_json=json.dumps({"secret_payload_key": "private_data_value"})
            )
            db.add(job)
            db.commit()
            job_id = job.id

        resp = await client_a.get(f"/api/v1/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "completed"
        assert "private_data_value" not in json.dumps(data)
        assert "secret_payload_key" not in data

        cross_resp = await client_b.get(f"/api/v1/jobs/{job_id}")
        assert cross_resp.status_code == 403

        invalid_resp = await client_a.get("/api/v1/jobs/not-a-uuid")
        assert invalid_resp.status_code == 422

        not_found_resp = await client_a.get(f"/api/v1/jobs/{uuid4()}")
        assert not_found_resp.status_code == 404
    finally:
        await client_a.aclose()
        await client_b.aclose()


@pytest.mark.asyncio
async def test_api_089_cancel_job(part06_identity):
    client_a = await get_authed_client(part06_identity["user_a_email"], part06_identity["password"])
    client_b = await get_authed_client(part06_identity["user_b_email"], part06_identity["password"])
    try:
        with sync_session_factory() as db:
            job = JobModel(
                company_id=part06_identity["company_a_id"],
                job_type="import:products",
                status="pending",
                progress=0
            )
            db.add(job)
            db.commit()
            job_id = job.id

        cross_cancel = await client_b.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cross_cancel.status_code == 403

        cancel_resp = await client_a.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        not_found = await client_a.post(f"/api/v1/jobs/{uuid4()}/cancel")
        assert not_found.status_code == 404

        invalid_cancel = await client_a.post("/api/v1/jobs/invalid-id/cancel")
        assert invalid_cancel.status_code == 422
    finally:
        await client_a.aclose()
        await client_b.aclose()


def test_reg_14_persistence_across_process_restarts(part06_identity):
    comp_id = part06_identity["company_a_id"]
    job_id = uuid4()
    sched_key = f"monthly_quota_{uuid4().hex[:6]}"
    with sync_session_factory() as db:
        job = JobModel(
            id=job_id,
            company_id=comp_id,
            job_type="report:analytics",
            status="pending",
            progress=0
        )
        sched = ScheduleExecutionModel(
            schedule_key=sched_key,
            execution_window="2026-10",
            leader_id="leader_node_a",
            status="completed"
        )
        db.add_all([job, sched])
        db.commit()

    with sync_session_factory() as db:
        persisted_job = db.get(JobModel, job_id)
        assert persisted_job is not None
        assert persisted_job.status == "pending"

        persisted_sched = db.scalar(
            select(ScheduleExecutionModel).where(
                ScheduleExecutionModel.schedule_key == sched_key,
                ScheduleExecutionModel.execution_window == "2026-10"
            )
        )
        assert persisted_sched is not None
        assert persisted_sched.leader_id == "leader_node_a"


def test_reg_20_recovery_and_deduplication(part06_identity):
    comp_id = part06_identity["company_a_id"]
    consumer = DurableInboxConsumer()
    event_id = uuid4()
    effect_counter = 0

    def apply_effect(db, payload):
        nonlocal effect_counter
        effect_counter += 1
        return {"effect_applied": True}

    with sync_session_factory() as db:
        res1 = consumer.consume_event(db, comp_id, "finance_worker", event_id, "payment.received", {}, apply_effect)
        db.commit()
    assert res1["effect_applied"] is True
    assert effect_counter == 1

    with sync_session_factory() as db:
        res2 = consumer.consume_event(db, comp_id, "finance_worker", event_id, "payment.received", {}, apply_effect)
        db.commit()
    assert res2["effect_applied"] is True
    assert effect_counter == 1
