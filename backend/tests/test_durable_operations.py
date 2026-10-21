import secrets
from pathlib import Path
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.operaciones.infrastructure_models import Notification
from salesia.modules.operaciones.jobs import process_jobs
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import BackupSnapshotModel, CompanyModel, CustomerModel, JobModel, UserModel


@pytest.fixture
def operations_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "private_storage_path", str(tmp_path))
    monkeypatch.setattr(settings, "backup_encryption_key", secrets.token_urlsafe(48))
    password = secrets.token_urlsafe(24)
    process_jobs(limit=100)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Operaciones", trade_name="Operaciones")
        db.add(company)
        db.flush()
        user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        db.add(user)
        platform_password = secrets.token_urlsafe(24)
        platform_user = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(platform_password), role="platform_admin", is_active=True)
        db.add(platform_user)
        db.commit()
        return {"email": user.email, "password": password, "platform_email": platform_user.email, "platform_password": platform_password, "company_id": company.id, "user_id": user.id, "root": tmp_path}


async def operations_client(identity, platform=False):
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    email = identity["platform_email"] if platform else identity["email"]
    password = identity["platform_password"] if platform else identity["password"]
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return client


async def upload_csv(client, content):
    intent = await client.post("/api/v1/attachments/upload-intents", json={"file_name": "customers.csv", "mime_type": "text/csv", "file_size_bytes": len(content), "related_entity_type": "import"})
    assert intent.status_code == 201, intent.text
    data = intent.json()
    uploaded = await client.put(data["upload_url"], content=content, headers={"X-Upload-Token": data["upload_token"], "Content-Type": "text/csv"})
    assert uploaded.status_code == 200, uploaded.text
    completed = await client.post(f"/api/v1/attachments/{data['attachment_id']}/complete")
    assert completed.status_code == 200, completed.text
    return data["attachment_id"]


@pytest.mark.asyncio
async def test_attachment_requires_exact_content_and_completion(operations_identity):
    client = await operations_client(operations_identity)
    try:
        content = b"code,doc_type,doc_number,legal_name\nC1,RUC,100,Cliente Uno\n"
        intent = await client.post("/api/v1/attachments/upload-intents", json={"file_name": "customers.csv", "mime_type": "text/csv", "file_size_bytes": len(content), "related_entity_type": "import"})
        data = intent.json()
        assert (await client.post(f"/api/v1/attachments/{data['attachment_id']}/complete")).status_code == 409
        assert (await client.put(data["upload_url"], content=content[:-1], headers={"X-Upload-Token": data["upload_token"]})).status_code == 422
        assert (await client.put(data["upload_url"], content=content, headers={"X-Upload-Token": data["upload_token"]})).status_code == 200
        assert (await client.put(data["upload_url"], content=content, headers={"X-Upload-Token": data["upload_token"]})).status_code == 401
        assert (await client.post(f"/api/v1/attachments/{data['attachment_id']}/complete")).status_code == 200
        assert (operations_identity["root"] / "attachments" / f"{data['attachment_id']}.bin").read_bytes() == content
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_csv_import_is_durable_and_processed_once(operations_identity):
    client = await operations_client(operations_identity)
    try:
        content = b"code,doc_type,doc_number,legal_name,email\nC1,RUC,200,Cliente Importado,cliente@example.com\n"
        attachment_id = await upload_csv(client, content)
        key = uuid4().hex
        payload = {"target_entity": "customers", "attachment_id": attachment_id}
        staged = await client.post("/api/v1/imports", json=payload, headers={"Idempotency-Key": key})
        assert staged.status_code == 202, staged.text
        duplicate = await client.post("/api/v1/imports", json=payload, headers={"Idempotency-Key": key})
        assert duplicate.json()["job_id"] == staged.json()["job_id"]
        job_id = staged.json()["job_id"]
        assert (await client.post(f"/api/v1/imports/{job_id}/commit")).status_code == 202
        assert process_jobs(limit=1) == 1
        result = await client.get(f"/api/v1/jobs/{job_id}")
        assert result.json()["status"] == "completed"
        assert result.json()["result"]["processed_rows"] == 1
        with sync_session_factory() as db:
            assert db.scalar(select(CustomerModel.id).where(CustomerModel.company_id == operations_identity["company_id"], CustomerModel.doc_number == "200")) is not None
            assert len(db.scalars(select(Notification).where(Notification.user_id == operations_identity["user_id"])).all()) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_unknown_resources_fail_and_pending_job_can_cancel(operations_identity):
    client = await operations_client(operations_identity)
    try:
        unknown = uuid4()
        assert (await client.get(f"/api/v1/jobs/{unknown}")).status_code == 404
        assert (await client.post(f"/api/v1/attachments/{unknown}/complete")).status_code == 404
        content = b"code,doc_type,doc_number,legal_name\nC2,RUC,300,Cancelar\n"
        attachment_id = await upload_csv(client, content)
        staged = await client.post("/api/v1/imports", json={"target_entity": "customers", "attachment_id": attachment_id}, headers={"Idempotency-Key": uuid4().hex})
        job_id = staged.json()["job_id"]
        cancelled = await client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancelled.json()["status"] == "cancelled"
        assert process_jobs(limit=1) == 0
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_encrypted_backup_and_restore_verification(operations_identity):
    client = await operations_client(operations_identity, platform=True)
    try:
        queued = await client.post("/api/v1/operations/backup/trigger", headers={"Idempotency-Key": uuid4().hex})
        assert queued.status_code == 202, queued.text
        assert process_jobs(limit=1) == 1
        job = await client.get(f"/api/v1/jobs/{queued.json()['job_id']}")
        assert job.json()["status"] == "completed", job.text
        snapshot_id = job.json()["result"]["snapshot_id"]
        status = await client.get("/api/v1/operations/backup/status")
        snapshot = next(item for item in status.json()["items"] if item["snapshot_id"] == snapshot_id)
        assert Path(next((operations_identity["root"] / "backups").glob(f"{snapshot_id}*"))).is_file()
        verified = await client.post("/api/v1/operations/restore/verify", json={"snapshot_id": snapshot_id, "checksum": snapshot["checksum"]})
        assert verified.status_code == 200, verified.text
        assert verified.json()["integrity_check"] == "passed"
        failed = await client.post("/api/v1/operations/restore/verify", json={"snapshot_id": snapshot_id, "checksum": "0" * 64})
        assert failed.status_code == 409
        with sync_session_factory() as db:
            assert db.scalar(select(BackupSnapshotModel).where(BackupSnapshotModel.snapshot_id == snapshot_id)).encrypted is True
            assert db.scalar(select(JobModel).where(JobModel.id == UUID(queued.json()["job_id"]))).attempts == 1
    finally:
        await client.aclose()
