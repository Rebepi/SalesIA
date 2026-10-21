import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    AttachmentModel,
    PaymentModel
)
from salesia.modules.operaciones.infrastructure_models import UploadGrant, Notification
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.domain.exceptions import (
    StockInsufficientException,
    VersionConflictException,
    CreditLimitExceededException,
    PaymentPendingException,
    DatasetEmptyException
)
from salesia.shared.infrastructure.pagination import encode_cursor, decode_cursor
from salesia.shared.infrastructure.safe_filter import (
    build_safe_filter,
    validate_filter_field,
    validate_filter_operator,
    sanitize_filter_value
)
from salesia.shared.infrastructure.transactions import claim_request, complete_request
from tests.support.auth_helpers import create_durable_identity
from fastapi import HTTPException

TEST_COMP_A_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_A_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_COMP_B_ID = UUID("00000000-0000-0000-0000-000000000099")
TEST_USER_B_ID = UUID("00000000-0000-0000-0000-000000000098")


@pytest.fixture(autouse=True, scope="module")
def setup_part24_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        ca = session.scalar(select(CompanyModel).where(CompanyModel.id == TEST_COMP_A_ID))
        if not ca:
            ca = CompanyModel(
                id=TEST_COMP_A_ID,
                tax_id="20999999001",
                legal_name="EMPRESA A PART24 S.A.C.",
                trade_name="SALESIA A",
                base_currency="USD",
                is_active=True
            )
            session.add(ca)

        cb = session.scalar(select(CompanyModel).where(CompanyModel.id == TEST_COMP_B_ID))
        if not cb:
            cb = CompanyModel(
                id=TEST_COMP_B_ID,
                tax_id="20999999002",
                legal_name="EMPRESA B PART24 S.A.C.",
                trade_name="SALESIA B",
                base_currency="USD",
                is_active=True
            )
            session.add(cb)

        ua = session.scalar(select(UserModel).where(UserModel.id == TEST_USER_A_ID))
        if not ua:
            ua = UserModel(
                id=TEST_USER_A_ID,
                company_id=TEST_COMP_A_ID,
                email="admin_part24_a@salesia.enterprise",
                hashed_password=hash_password("SuperSecret2026!"),
                role="company_admin",
                is_active=True
            )
            session.add(ua)
        else:
            ua.is_active = True

        ub = session.scalar(select(UserModel).where(UserModel.id == TEST_USER_B_ID))
        if not ub:
            ub = UserModel(
                id=TEST_USER_B_ID,
                company_id=TEST_COMP_B_ID,
                email="admin_part24_b@salesia.enterprise",
                hashed_password=hash_password("SuperSecret2026!"),
                role="company_admin",
                is_active=True
            )
            session.add(ub)
        else:
            ub.is_active = True

        session.commit()
    yield


@pytest.fixture
def auth_headers_a():
    with sync_session_factory() as session:
        user = session.scalar(select(UserModel).where(UserModel.id == TEST_USER_A_ID))
        identity = create_durable_identity(
            session,
            company_id=TEST_COMP_A_ID,
            user_id=TEST_USER_A_ID,
            role="company_admin",
            email=user.email,
            password="SuperSecret2026!"
        )
        return identity["headers"]


@pytest.fixture
def auth_headers_b():
    with sync_session_factory() as session:
        user = session.scalar(select(UserModel).where(UserModel.id == TEST_USER_B_ID))
        identity = create_durable_identity(
            session,
            company_id=TEST_COMP_B_ID,
            user_id=TEST_USER_B_ID,
            role="company_admin",
            email=user.email,
            password="SuperSecret2026!"
        )
        return identity["headers"]


@pytest.mark.asyncio
async def test_api_097_health_live_probe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["app"] == "SalesIA Enterprise"
        assert "version" in data
        assert "timestamp" in data
        for forbidden_key in ["password", "secret", "database_url", "dsn", "jwt_secret"]:
            assert forbidden_key not in json.dumps(data).lower()

        res_post = await client.post("/api/v1/health/live", json={"unexpected": "data"})
        assert res_post.status_code == 405


@pytest.mark.asyncio
async def test_api_098_health_ready_probe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "timestamp" in data
        for forbidden_key in ["password", "postgres://", "sqlite://", "secret"]:
            assert forbidden_key not in json.dumps(data).lower()

        res_post = await client.post("/api/v1/health/ready")
        assert res_post.status_code == 405


@pytest.mark.asyncio
async def test_api_099_business_errors_contract(auth_headers_a):
    from fastapi import FastAPI, APIRouter
    from salesia.shared.infrastructure.errors import register_exception_handlers

    sub_app = FastAPI()
    register_exception_handlers(sub_app)

    test_router = APIRouter(prefix="/api/v1/test-errors-contract")

    @test_router.get("/stock-insufficient")
    def route_stock():
        raise StockInsufficientException(sku="SKU-TEST-99", requested=10, available=2)

    @test_router.get("/version-conflict")
    def route_version():
        raise VersionConflictException("Documento modificado por otro usuario")

    @test_router.get("/credit-limit")
    def route_credit():
        raise CreditLimitExceededException("Limite de credito excedido")

    @test_router.get("/payment-pending")
    def route_payment():
        raise PaymentPendingException("Pago en confirmacion")

    @test_router.get("/dataset-empty")
    def route_dataset():
        raise DatasetEmptyException("No hay filas para calcular")

    sub_app.include_router(test_router)

    transport = ASGITransport(app=sub_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cases = [
            ("/api/v1/test-errors-contract/stock-insufficient", 409, "STOCK_INSUFFICIENT"),
            ("/api/v1/test-errors-contract/version-conflict", 409, "VERSION_CONFLICT"),
            ("/api/v1/test-errors-contract/credit-limit", 400, "CREDIT_LIMIT_EXCEEDED"),
            ("/api/v1/test-errors-contract/payment-pending", 409, "PAYMENT_PENDING"),
            ("/api/v1/test-errors-contract/dataset-empty", 422, "DATASET_EMPTY"),
        ]

        for path, expected_status, expected_code in cases:
            res = await client.get(path, headers=auth_headers_a)
            assert res.status_code == expected_status
            payload = res.json()
            assert payload["code"] == expected_code
            assert "type" in payload
            assert "title" in payload
            assert "trace_id" in payload
            assert "detail" in payload
            assert len(payload["trace_id"]) > 10


def test_api_100_stable_pagination_invariants():
    t0 = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    id1 = uuid4()
    scope = "scope_comp_a"

    token = encode_cursor(t0, id1, scope)
    assert isinstance(token, str)
    assert len(token) > 10

    decoded_time, decoded_id = decode_cursor(token, expected_scope_hash=scope)
    assert decoded_time == t0
    assert decoded_id == id1

    with pytest.raises(HTTPException) as exc_scope:
        decode_cursor(token, expected_scope_hash="different_scope")
    assert exc_scope.value.status_code == 422

    with pytest.raises(HTTPException) as exc_malformed:
        decode_cursor("not-a-valid-base64-cursor!")
    assert exc_malformed.value.status_code == 422

    items = [
        {"created_at": t0 + timedelta(seconds=i), "id": uuid4(), "seq": i}
        for i in range(10)
    ]
    sorted_items = sorted(items, key=lambda x: (x["created_at"], x["id"]), reverse=True)

    page1 = sorted_items[:5]
    last_p1 = page1[-1]
    p1_cursor = encode_cursor(last_p1["created_at"], last_p1["id"])

    concurrent_item = {"created_at": t0 + timedelta(seconds=20), "id": uuid4(), "seq": 999}
    updated_list = sorted(items + [concurrent_item], key=lambda x: (x["created_at"], x["id"]), reverse=True)

    c_time, c_id = decode_cursor(p1_cursor)
    page2 = [x for x in updated_list if (x["created_at"] < c_time) or (x["created_at"] == c_time and x["id"] < c_id)][:5]

    visited_ids = {x["id"] for x in page1}.intersection({x["id"] for x in page2})
    assert len(visited_ids) == 0


def test_api_101_safe_filtering_invariants():
    allowlist = {"sku", "category", "price", "status", "created_at"}

    valid_field = validate_filter_field("SKU", allowlist)
    assert valid_field == "sku"

    with pytest.raises(HTTPException) as exc_field:
        validate_filter_field("password_hash", allowlist)
    assert exc_field.value.status_code == 422

    valid_op = validate_filter_operator("GTE")
    assert valid_op == "gte"

    with pytest.raises(HTTPException) as exc_op:
        validate_filter_operator("raw_sql")
    assert exc_op.value.status_code == 422

    with pytest.raises(HTTPException) as exc_inj:
        sanitize_filter_value("PROD-1'; DROP TABLE sales; --")
    assert exc_inj.value.status_code == 422

    large_in_list = [f"item_{i}" for i in range(100)]
    with pytest.raises(HTTPException) as exc_list:
        sanitize_filter_value(large_in_list)
    assert exc_list.value.status_code == 422

    filters_payload = [
        {"field": "category", "operator": "eq", "value": "Computo"},
        {"field": "status", "operator": "in", "value": ["active", "draft"]}
    ]
    safe_clauses = build_safe_filter(filters_payload, allowlist)
    assert len(safe_clauses) == 2
    assert safe_clauses[0].field == "category"
    assert safe_clauses[1].operator == "in"


def test_api_102_idempotency_policy_invariants():
    with sync_session_factory() as db:
        op_name = "test.policy"
        key = uuid4().hex
        payload = {"total": "1200.00", "currency": "USD"}

        rec1, cached1 = claim_request(db, TEST_COMP_A_ID, op_name, key, payload)
        assert rec1 is not None
        assert cached1 is None

        with pytest.raises(HTTPException) as in_flight_exc:
            claim_request(db, TEST_COMP_A_ID, op_name, key, payload)
        assert in_flight_exc.value.status_code == 409

        complete_request(rec1, {"success": True, "transaction_id": "TX-100"})
        db.commit()

        rec2, cached2 = claim_request(db, TEST_COMP_A_ID, op_name, key, payload)
        assert cached2 is not None
        assert cached2["transaction_id"] == "TX-100"

        with pytest.raises(HTTPException) as diff_payload_exc:
            claim_request(db, TEST_COMP_A_ID, op_name, key, {"total": "9999.00"})
        assert diff_payload_exc.value.status_code == 409

        rec_comp_b, cached_comp_b = claim_request(db, TEST_COMP_B_ID, op_name, key, payload)
        assert rec_comp_b is not None
        assert cached_comp_b is None
        db.rollback()


@pytest.mark.asyncio
async def test_api_103_evolution_and_deprecation_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_legacy = await client.get("/api/v1/health")
        assert res_legacy.status_code == 200
        assert res_legacy.headers.get("Deprecation") == "true"
        assert "Sunset" in res_legacy.headers
        assert "Link" in res_legacy.headers

        res_v1 = await client.get("/api/v1/health/live")
        assert res_v1.status_code == 200
        assert "Deprecation" not in res_v1.headers


def test_api_104_openapi_contract_drift_detection():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    spec_path = os.path.join(root_dir, "contracts", "openapi", "openapi.json")
    assert os.path.isfile(spec_path)
    with open(spec_path, "r", encoding="utf-8") as f:
        saved_spec = json.load(f)

    live_spec = app.openapi()

    assert saved_spec["openapi"] == live_spec["openapi"]
    assert saved_spec["info"]["title"] == live_spec["info"]["title"]

    saved_paths = set(saved_spec.get("paths", {}).keys())
    live_paths = set(live_spec.get("paths", {}).keys())
    missing_in_saved = live_paths - saved_paths
    assert len(missing_in_saved) == 0

    saved_ops = sum(len(m) for m in saved_spec.get("paths", {}).values())
    live_ops = sum(len(m) for m in live_spec.get("paths", {}).values())
    assert saved_ops == live_ops
    assert live_ops >= 400


@pytest.mark.asyncio
async def test_api_105_downloads_expiration_and_streams_revocation(auth_headers_a, auth_headers_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        att_id = uuid4()
        with sync_session_factory() as session:
            att = AttachmentModel(
                id=att_id,
                company_id=TEST_COMP_A_ID,
                file_name="reporte_financiero_2026.csv",
                mime_type="text/csv",
                size_bytes=100,
                uploaded=True,
                verified=True,
                scan_status="clean"
            )
            session.add(att)
            session.flush()
            dummy_file = os.path.join(settings.private_storage_path, "dummy.csv")
            os.makedirs(os.path.dirname(dummy_file), exist_ok=True)
            with open(dummy_file, "wb") as f:
                f.write(b"content")
            grant_expired = UploadGrant(
                attachment_id=att_id,
                token_hash=uuid4().hex,
                expected_size=100,
                storage_path=dummy_file,
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                consumed_at=datetime.now(timezone.utc) - timedelta(hours=2)
            )
            session.add(grant_expired)
            session.commit()

        res_expired = await client.get(f"/api/v1/attachments/{att_id}/download", headers=auth_headers_a)
        assert res_expired.status_code == 410

        res_other_comp = await client.get(f"/api/v1/attachments/{att_id}/download", headers=auth_headers_b)
        assert res_other_comp.status_code in (403, 404)

        res_unauth = await client.get(f"/api/v1/events/stream")
        assert res_unauth.status_code == 401

        with sync_session_factory() as session:
            notif = Notification(
                id=uuid4(),
                company_id=TEST_COMP_A_ID,
                user_id=TEST_USER_A_ID,
                title="SSE Test Notification",
                message="Contenido de prueba de evento",
                event_type="test"
            )
            session.add(notif)
            session.commit()

        async with client.stream("GET", "/api/v1/events/stream?limit=1", headers=auth_headers_a) as stream_resp:
            assert stream_resp.status_code == 200
            assert "text/event-stream" in stream_resp.headers.get("content-type", "")
            lines = []
            async for chunk in stream_resp.aiter_lines():
                if chunk:
                    lines.append(chunk)
                if len(lines) >= 3:
                    break
            assert len(lines) > 0
            joined = "\n".join(lines)
            assert "notification" in joined or "heartbeat" in joined
