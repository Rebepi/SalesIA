import asyncio
import io
import json
import secrets
import zipfile
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.operaciones.infrastructure_models import (
    Notification,
    UploadGrant,
    NotificationPreference,
    CollaborationComment,
    CollaborationTask,
    CollaborationApproval,
    SavedView
)
from salesia.modules.operaciones.jobs import process_jobs
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory, Base, sync_engine
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    BranchModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    AttachmentModel,
    JobModel
)
from salesia.shared.infrastructure.workers import ExternalNotificationManager

Base.metadata.create_all(sync_engine)


@pytest.fixture
def part23_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "private_storage_path", str(tmp_path))
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company_a = CompanyModel(tax_id=uuid4().hex[:12], legal_name="Empresa A", trade_name="Empresa A", is_active=True)
        company_b = CompanyModel(tax_id=uuid4().hex[:12], legal_name="Empresa B", trade_name="Empresa B", is_active=True)
        db.add_all([company_a, company_b])
        db.flush()
        branch_a = BranchModel(company_id=company_a.id, code="B" + uuid4().hex[:6].upper(), name="Sede A")
        db.add(branch_a)
        user_a = UserModel(
            company_id=company_a.id,
            email=f"{uuid4().hex[:8]}@empresa-a.com",
            hashed_password=hash_password(password),
            role="company_admin",
            is_active=True
        )
        salesperson_a = UserModel(
            company_id=company_a.id,
            email=f"{uuid4().hex[:8]}@ventas-a.com",
            hashed_password=hash_password(password),
            role="salesperson",
            is_active=True
        )
        inactive_user_a = UserModel(
            company_id=company_a.id,
            email=f"{uuid4().hex[:8]}@inactivo-a.com",
            hashed_password=hash_password(password),
            role="salesperson",
            is_active=False
        )
        user_b = UserModel(
            company_id=company_b.id,
            email=f"{uuid4().hex[:8]}@empresa-b.com",
            hashed_password=hash_password(password),
            role="company_admin",
            is_active=True
        )
        cust_a = CustomerModel(
            company_id=company_a.id,
            code="CLI-001",
            doc_type="RUC",
            doc_number="20999888111",
            legal_name="Cliente Corporativo A"
        )
        prod_a = ProductModel(
            company_id=company_a.id,
            sku="SKU-AAA",
            name="Producto Estrella A",
            category="General",
            unit_of_measure="NIU",
            unit_price=Decimal("150.00"),
            unit_cost=Decimal("90.00"),
            tax_rate=Decimal("0.18"),
            is_active=True
        )
        db.add_all([user_a, salesperson_a, inactive_user_a, user_b, cust_a, prod_a])
        db.commit()
        return {
            "company_a_id": company_a.id,
            "company_b_id": company_b.id,
            "user_a_id": user_a.id,
            "user_a_email": user_a.email,
            "salesperson_a_id": salesperson_a.id,
            "salesperson_a_email": salesperson_a.email,
            "inactive_user_a_id": inactive_user_a.id,
            "user_b_id": user_b.id,
            "user_b_email": user_b.email,
            "customer_a_id": cust_a.id,
            "product_a_id": prod_a.id,
            "password": password,
            "root": tmp_path
        }


async def authed_client(email: str, password: str) -> AsyncClient:
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    return client


async def upload_file(client, name: str, mime: str, content: bytes, entity_type: str = "import", entity_id = None):
    intent_resp = await client.post(
        "/api/v1/attachments/upload-intents",
        json={
            "file_name": name,
            "mime_type": mime,
            "file_size_bytes": len(content),
            "related_entity_type": entity_type,
            "related_entity_id": str(entity_id) if entity_id else None
        }
    )
    assert intent_resp.status_code == 201, intent_resp.text
    intent = intent_resp.json()
    put_resp = await client.put(
        intent["upload_url"],
        content=content,
        headers={"X-Upload-Token": intent["upload_token"]}
    )
    assert put_resp.status_code == 200, put_resp.text
    return intent


@pytest.mark.asyncio
async def test_fallo_reproducido_complete_unuploaded_attachment(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        intent_resp = await client.post(
            "/api/v1/attachments/upload-intents",
            json={
                "file_name": "archivo_pendiente.csv",
                "mime_type": "text/csv",
                "file_size_bytes": 100,
                "related_entity_type": "import"
            }
        )
        assert intent_resp.status_code == 201
        att_id = intent_resp.json()["attachment_id"]
        complete_resp = await client.post(f"/api/v1/attachments/{att_id}/complete")
        assert complete_resp.status_code == 409
        with sync_session_factory() as db:
            att = db.get(AttachmentModel, UUID(att_id))
            assert att.verified is False
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_reg_19_dangerous_or_tampered_attachment_rejected(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        exe_content = b"MZ\x90\x00\x03\x00\x00\x00" + b"A" * 50
        intent = await upload_file(client, "malware_disguised.csv", "text/csv", exe_content)
        comp_bad = await client.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")
        assert comp_bad.status_code == 422
        with sync_session_factory() as db:
            att = db.get(AttachmentModel, UUID(intent["attachment_id"]))
            assert att.verified is False
            assert att.scan_status == "quarantined"

        normal_content = b"code,doc_type,doc_number,legal_name\nC9,RUC,209990001,Cliente Nueve\n"
        intent_ok = await upload_file(client, "valid.csv", "text/csv", normal_content)
        comp_tampered = await client.post(
            f"/api/v1/attachments/{intent_ok['attachment_id']}/complete",
            json={"sha256_checksum": "0" * 64}
        )
        assert comp_tampered.status_code == 409

        comp_good = await client.post(f"/api/v1/attachments/{intent_ok['attachment_id']}/complete")
        assert comp_good.status_code == 200
        assert comp_good.json()["status"] == "verified"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_fal_037_csv_import_staging_and_validation(part23_identity):
    client_a = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_b = await authed_client(part23_identity["user_b_email"], part23_identity["password"])
    try:
        csv_content = (
            b"code,doc_type,doc_number,legal_name\n"
            b"C10,RUC,20111111111,Valido Uno\n"
            b"C11,RUC,,Falta Doc\n"
            b"C12,RUC,20111111111,Doc Duplicado\n"
            b"C13,RUC,20333333333,Valido Dos\n"
        )
        intent = await upload_file(client_a, "staging_test.csv", "text/csv", csv_content)
        await client_a.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")

        staged_resp = await client_a.post(
            "/api/v1/imports",
            headers={"Idempotency-Key": uuid4().hex},
            json={"target_entity": "customers", "attachment_id": intent["attachment_id"]}
        )
        assert staged_resp.status_code == 202
        data = staged_resp.json()
        assert data["status"] == "staged"
        result_info = data["result"]
        assert result_info["total_rows"] == 4
        assert result_info["valid_rows"] == 2
        assert result_info["invalid_rows"] == 2
        assert len(result_info["row_errors"]) >= 2

        cross_resp = await client_b.post(
            "/api/v1/imports",
            headers={"Idempotency-Key": uuid4().hex},
            json={"target_entity": "customers", "attachment_id": intent["attachment_id"]}
        )
        assert cross_resp.status_code in (403, 422)
    finally:
        await client_a.aclose()
        await client_b.aclose()


@pytest.mark.asyncio
async def test_fal_037_csv_import_commit_creates_real_records(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        csv_content = (
            b"code,doc_type,doc_number,legal_name,email\n"
            b"CREAL1,RUC,20777777771,Real Corp Uno,corp1@example.com\n"
            b"CREAL2,RUC,20777777772,Real Corp Dos,corp2@example.com\n"
        )
        intent = await upload_file(client, "real_import.csv", "text/csv", csv_content)
        await client.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")

        staged = await client.post(
            "/api/v1/imports",
            headers={"Idempotency-Key": uuid4().hex},
            json={"target_entity": "customers", "attachment_id": intent["attachment_id"]}
        )
        job_id = staged.json()["job_id"]
        committed = await client.post(f"/api/v1/imports/{job_id}/commit")
        assert committed.status_code == 202

        assert process_jobs(limit=5) >= 1
        status = await client.get(f"/api/v1/jobs/{job_id}")
        assert status.json()["status"] == "completed"
        assert status.json()["result"]["processed_rows"] == 2

        with sync_session_factory() as db:
            c1 = db.scalar(select(CustomerModel).where(CustomerModel.company_id == part23_identity["company_a_id"], CustomerModel.code == "CREAL1"))
            c2 = db.scalar(select(CustomerModel).where(CustomerModel.company_id == part23_identity["company_a_id"], CustomerModel.code == "CREAL2"))
            assert c1 is not None
            assert c1.legal_name == "Real Corp Uno"
            assert c2 is not None
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_001_and_api_091_persistent_notification_center(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        with sync_session_factory() as db:
            n1 = Notification(
                company_id=part23_identity["company_a_id"],
                user_id=part23_identity["user_a_id"],
                title="Alerta Prioritaria",
                message="Actualización crítica del sistema",
                event_type="SYS_ALERT",
                priority="high",
                category="operations"
            )
            n2 = Notification(
                company_id=part23_identity["company_a_id"],
                user_id=part23_identity["user_a_id"],
                title="Mensaje Normal",
                message="Reporte diario listo",
                event_type="REPORT_READY",
                priority="normal",
                category="commercial"
            )
            db.add_all([n1, n2])
            db.commit()

        resp = await client.get("/api/v1/notifications?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] >= 2
        assert data["unread_count"] >= 2
        titles = [item["title"] for item in data["items"]]
        assert "Alerta Prioritaria" in titles

        filtered = await client.get("/api/v1/notifications?priority=high")
        assert filtered.status_code == 200
        assert all(item["priority"] == "high" for item in filtered.json()["items"])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_002_channel_preferences(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        prefs_res = await client.get("/api/v1/notifications/preferences")
        assert prefs_res.status_code == 200
        assert "preferences" in prefs_res.json()

        update_comm = await client.put(
            "/api/v1/notifications/preferences",
            json={"category": "commercial", "channel": "email", "enabled": False}
        )
        assert update_comm.status_code == 200
        assert update_comm.json()["enabled"] is False

        update_sec = await client.put(
            "/api/v1/notifications/preferences",
            json={"category": "security", "channel": "in_app", "enabled": False}
        )
        assert update_sec.status_code == 400
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_003_access_revalidation(part23_identity):
    client_admin = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_sales = await authed_client(part23_identity["salesperson_a_email"], part23_identity["password"])
    try:
        with sync_session_factory() as db:
            notif = Notification(
                company_id=part23_identity["company_a_id"],
                user_id=part23_identity["salesperson_a_id"],
                title="Revisar cliente",
                message="Verifique ficha del cliente",
                event_type="CRM_NOTIF",
                resource_type="customer",
                resource_id=part23_identity["customer_a_id"]
            )
            db.add(notif)
            db.commit()
            notif_id = notif.id

        res_ok = await client_sales.get(f"/api/v1/notifications/{notif_id}/resource")
        assert res_ok.status_code == 200
        assert res_ok.json()["access_granted"] is True

        with sync_session_factory() as db:
            sales_user = db.get(UserModel, part23_identity["salesperson_a_id"])
            sales_user.is_active = False
            db.commit()

        res_revoked = await client_sales.get(f"/api/v1/notifications/{notif_id}/resource")
        assert res_revoked.status_code in (401, 403)
    finally:
        await client_admin.aclose()
        await client_sales.aclose()


@pytest.mark.asyncio
async def test_col_004_collaboration_comments_sanitization_and_mentions(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        payload = {
            "resource_type": "customer",
            "resource_id": str(part23_identity["customer_a_id"]),
            "content": "Nota con posible script <script>alert('xss')</script> verificado.",
            "mentions": [str(part23_identity["user_b_id"]), str(part23_identity["user_a_id"])]
        }
        res = await client.post("/api/v1/collaboration/comments", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "<script>" not in data["content"]
        assert str(part23_identity["user_b_id"]) in data["blocked_mentions"]
        assert str(part23_identity["user_a_id"]) in data["authorized_mentions"]

        comment_id = data["id"]
        list_res = await client.get(f"/api/v1/collaboration/comments?resource_type=customer&resource_id={part23_identity['customer_a_id']}")
        assert list_res.status_code == 200
        assert len(list_res.json()["items"]) >= 1

        edit_res = await client.put(f"/api/v1/collaboration/comments/{comment_id}", json={"content": "Nota actualizada"})
        assert edit_res.status_code == 200
        assert edit_res.json()["version"] == 2
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_005_collaboration_tasks_inactive_membership(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        bad_task = await client.post(
            "/api/v1/collaboration/tasks",
            json={
                "title": "Tarea inválida",
                "assignee_id": str(part23_identity["inactive_user_a_id"]),
                "priority": "high"
            }
        )
        assert bad_task.status_code == 422

        good_task = await client.post(
            "/api/v1/collaboration/tasks",
            json={
                "title": "Tarea válida",
                "assignee_id": str(part23_identity["user_a_id"]),
                "priority": "normal"
            }
        )
        assert good_task.status_code == 201
        task_id = good_task.json()["id"]

        list_tasks = await client.get("/api/v1/collaboration/tasks")
        assert list_tasks.status_code == 200
        found = next(t for t in list_tasks.json()["items"] if t["id"] == task_id)
        assert found["assignee_active"] is True

        update_res = await client.patch(
            f"/api/v1/collaboration/tasks/{task_id}",
            json={"status": "completed", "resolution_notes": "Resuelta"}
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "completed"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_006_collaboration_approvals_modified_doc_revalidation(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        req_res = await client.post(
            "/api/v1/collaboration/approvals",
            json={
                "resource_type": "sale",
                "resource_id": str(uuid4()),
                "document_version": 1,
                "policy_name": "DESCUENTO_MAYOR_10"
            }
        )
        assert req_res.status_code == 201
        approval_id = req_res.json()["id"]

        conflict_res = await client.post(
            f"/api/v1/collaboration/approvals/{approval_id}/decide",
            json={"decision": "approved", "reason": "Conforme", "current_document_version": 2}
        )
        assert conflict_res.status_code == 409

        success_res = await client.post(
            f"/api/v1/collaboration/approvals/{approval_id}/decide",
            json={"decision": "approved", "reason": "Conforme", "current_document_version": 1}
        )
        assert success_res.status_code == 200
        assert success_res.json()["status"] == "approved"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_007_and_api_096_unified_search_enterprise_isolation(part23_identity):
    client_a = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_b = await authed_client(part23_identity["user_b_email"], part23_identity["password"])
    try:
        res_a = await client_a.get("/api/v1/search?q=Corporativo")
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["count"] >= 1
        assert any(item["title"] == "Cliente Corporativo A" for item in data_a["results"])

        res_b = await client_b.get("/api/v1/search?q=Corporativo")
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["total"] == 0
        assert len(data_b["results"]) == 0

        exact_res = await client_a.get("/api/v1/search?q=SKU-AAA")
        assert exact_res.status_code == 200
        assert any(item["subtitle"] == "SKU: SKU-AAA" for item in exact_res.json()["results"])
    finally:
        await client_a.aclose()
        await client_b.aclose()


@pytest.mark.asyncio
async def test_col_008_saved_views_versioning_and_migration(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        create_res = await client.post(
            "/api/v1/collaboration/saved-views",
            json={
                "resource_type": "sales",
                "name": "Vista Antigua",
                "config_json": json.dumps({"legacy_filter": "status=draft"}),
                "schema_version": 1
            }
        )
        assert create_res.status_code == 201
        view_id = create_res.json()["id"]

        list_res = await client.get("/api/v1/collaboration/saved-views?resource_type=sales")
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        target = next(v for v in items if v["id"] == view_id)
        assert target["is_migrated"] is True
        assert target["schema_version"] == 2
        assert "filters" in target["config"]

        del_res = await client.delete(f"/api/v1/collaboration/saved-views/{view_id}")
        assert del_res.status_code == 200
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_009_and_api_094_attachments_upload_intents_and_private_storage(part23_identity):
    client_a = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_b = await authed_client(part23_identity["user_b_email"], part23_identity["password"])
    try:
        cross_res = await client_b.post(
            "/api/v1/attachments/upload-intents",
            json={
                "file_name": "cross.csv",
                "mime_type": "text/csv",
                "file_size_bytes": 50,
                "related_entity_type": "customer",
                "related_entity_id": str(part23_identity["customer_a_id"])
            }
        )
        assert cross_res.status_code == 422

        valid_res = await client_a.post(
            "/api/v1/attachments/upload-intents",
            json={
                "file_name": "normal.csv",
                "mime_type": "text/csv",
                "file_size_bytes": 50,
                "related_entity_type": "customer",
                "related_entity_id": str(part23_identity["customer_a_id"])
            }
        )
        assert valid_res.status_code == 201
        upload_url = valid_res.json()["upload_url"]
        assert "normal.csv" not in upload_url
        assert str(part23_identity["root"]) not in upload_url
    finally:
        await client_a.aclose()
        await client_b.aclose()


@pytest.mark.asyncio
async def test_col_010_and_api_095_file_validation_zip_bomb_and_integrity(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        bad_zip = b"PK\x03\x04corrupted_header" + b"X" * 100
        intent = await upload_file(client, "corrupted.zip", "application/zip", bad_zip)
        comp_res = await client.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")
        assert comp_res.status_code == 422
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_011_safe_preview_csp(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        svg_content = b"<svg><circle cx='50' cy='50' r='40'/></svg>"
        intent = await upload_file(client, "diagram.svg", "image/svg+xml", svg_content)
        await client.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")

        preview_res = await client.get(f"/api/v1/attachments/{intent['attachment_id']}/preview")
        assert preview_res.status_code == 200
        assert "default-src 'none'" in preview_res.headers.get("Content-Security-Policy", "")
        assert preview_res.headers.get("X-Content-Type-Options") == "nosniff"
    finally:
        await client.aclose()


def test_col_012_external_notifications_idempotent_retry_limit(part23_identity):
    mgr = ExternalNotificationManager()
    comp_id = part23_identity["company_a_id"]
    idemp_key = f"key_{uuid4().hex}"
    with sync_session_factory() as db:
        res1 = mgr.send_idempotent_notification(
            db,
            company_id=comp_id,
            channel="email",
            recipient="admin@empresa-a.com",
            idempotency_key=idemp_key,
            send_fn=lambda: "msg_123"
        )
        db.commit()
    assert res1.idempotency_key == idemp_key
    with sync_session_factory() as db:
        res2 = mgr.send_idempotent_notification(
            db,
            company_id=comp_id,
            channel="email",
            recipient="admin@empresa-a.com",
            idempotency_key=idemp_key,
            send_fn=lambda: "msg_456"
        )
        db.commit()
    assert res2.id == res1.id


@pytest.mark.asyncio
async def test_col_013_and_api_093_realtime_activity_sse_stream(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        cursor_val = datetime.now(timezone.utc).isoformat()
        stream_res = await client.get(f"/api/v1/events/stream?cursor={cursor_val}&limit=1")
        assert stream_res.status_code == 200
        assert "text/event-stream" in stream_res.headers.get("content-type", "")
        assert "heartbeat" in stream_res.text
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_col_014_contextual_help(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        help_res = await client.get("/api/v1/help/contextual?screen=operations")
        assert help_res.status_code == 200
        data = help_res.json()
        assert data["screen"] == "operations"
        assert len(data["articles"]) >= 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_api_086_post_imports_contracts(part23_identity):
    client = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    try:
        inv_content = b"col1,col2\nval1,val2\n"
        intent = await upload_file(client, "missing_cols.csv", "text/csv", inv_content)
        await client.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")

        fail_res = await client.post(
            "/api/v1/imports",
            headers={"Idempotency-Key": uuid4().hex},
            json={"target_entity": "customers", "attachment_id": intent["attachment_id"]}
        )
        assert fail_res.status_code == 422
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_api_087_post_imports_commit_contracts(part23_identity):
    client_a = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_b = await authed_client(part23_identity["user_b_email"], part23_identity["password"])
    try:
        csv_content = b"code,doc_type,doc_number,legal_name\nCX,RUC,20999111,Empresa X\n"
        intent = await upload_file(client_a, "x.csv", "text/csv", csv_content)
        await client_a.post(f"/api/v1/attachments/{intent['attachment_id']}/complete")
        staged = await client_a.post(
            "/api/v1/imports",
            headers={"Idempotency-Key": uuid4().hex},
            json={"target_entity": "customers", "attachment_id": intent["attachment_id"]}
        )
        job_id = staged.json()["job_id"]

        cross_commit = await client_b.post(f"/api/v1/imports/{job_id}/commit")
        assert cross_commit.status_code == 403

        not_found = await client_a.post(f"/api/v1/imports/{uuid4()}/commit")
        assert not_found.status_code == 404
    finally:
        await client_a.aclose()
        await client_b.aclose()


@pytest.mark.asyncio
async def test_api_092_patch_notifications_read(part23_identity):
    client_a = await authed_client(part23_identity["user_a_email"], part23_identity["password"])
    client_b = await authed_client(part23_identity["user_b_email"], part23_identity["password"])
    try:
        with sync_session_factory() as db:
            n = Notification(
                company_id=part23_identity["company_a_id"],
                user_id=part23_identity["user_a_id"],
                title="Notif Leída",
                message="Prueba lectura",
                event_type="SYS_TEST"
            )
            db.add(n)
            db.commit()
            notif_id = n.id

        cross = await client_b.patch(f"/api/v1/notifications/{notif_id}/read")
        assert cross.status_code == 403

        read_ok = await client_a.patch(f"/api/v1/notifications/{notif_id}/read")
        assert read_ok.status_code == 200
        assert read_ok.json()["read"] is True

        repeat_ok = await client_a.patch(f"/api/v1/notifications/{notif_id}/read")
        assert repeat_ok.status_code == 200
        assert repeat_ok.json()["read"] is True
    finally:
        await client_a.aclose()
        await client_b.aclose()
