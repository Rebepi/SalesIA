import os
import hashlib
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from salesia.main import app
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import BackupSnapshotModel, JobModel
from salesia.modules.operaciones.presentation.router import safe_path
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def auth_admin_token():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="platform_admin",
        email="admin_ops_f15@salesia.enterprise",
        password="valid_password"
    )
    return identity["access_token"]


@pytest.mark.asyncio
async def test_health_and_orchestration_probes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_root_health = await client.get("/api/v1/health")
        assert res_root_health.status_code == 200
        assert res_root_health.json()["status"] == "ok"

        res_live = await client.get("/api/v1/health/live")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "ok"

        res_ready = await client.get("/api/v1/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"
        assert res_ready.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_system_status_and_metrics_endpoints(auth_admin_token):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {auth_admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_status = await client.get("/api/v1/operations/system-status", headers=headers)
        assert res_status.status_code == 200
        body_status = res_status.json()
        assert body_status["status"] in ["healthy", "degraded", "maintenance"]
        assert "environment" in body_status
        assert "pending_jobs" in body_status

        res_metrics = await client.get("/api/v1/operations/metrics", headers=headers)
        assert res_metrics.status_code == 200
        body_metrics = res_metrics.json()
        assert "slo_targets" in body_metrics
        assert body_metrics["slo_targets"]["availability_target"] == 0.999
        assert body_metrics["slo_targets"]["rpo_minutes"] == 15.0
        assert body_metrics["slo_targets"]["rto_minutes"] == 120.0
        assert "jobs" in body_metrics


@pytest.mark.asyncio
async def test_feature_flags_lifecycle(auth_admin_token):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {auth_admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_flags = await client.get("/api/v1/operations/feature-flags", headers=headers)
        assert res_flags.status_code == 200
        flags = res_flags.json()["flags"]
        assert "ai_insights_engine" in flags

        toggle_payload = {"flag_key": "mfa_mandatory_enforcement", "enabled": True}
        res_toggle = await client.post("/api/v1/operations/feature-flags/toggle", json=toggle_payload, headers=headers)
        assert res_toggle.status_code == 200
        assert res_toggle.json()["enabled"] is True

        res_invalid = await client.post(
            "/api/v1/operations/feature-flags/toggle",
            json={"flag_key": "unknown_flag_xyz", "enabled": True},
            headers=headers
        )
        assert res_invalid.status_code == 400


@pytest.mark.asyncio
async def test_maintenance_and_degraded_modes(auth_admin_token):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {auth_admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        maint_payload = {"active": True, "reason": "Ventana programada", "estimated_end": "2026-10-10T04:00:00Z"}
        res_maint = await client.post("/api/v1/operations/maintenance/set", json=maint_payload, headers=headers)
        assert res_maint.status_code == 200
        assert res_maint.json()["active"] is True

        res_status = await client.get("/api/v1/operations/system-status", headers=headers)
        assert res_status.json()["status"] == "maintenance"

        await client.post(
            "/api/v1/operations/maintenance/set",
            json={"active": False},
            headers=headers
        )

        res_degraded = await client.post(
            "/api/v1/operations/degraded-mode/toggle",
            json={"active": True, "reason": "Alta carga comercial"},
            headers=headers
        )
        assert res_degraded.status_code == 200
        assert res_degraded.json()["active"] is True

        await client.post(
            "/api/v1/operations/degraded-mode/toggle",
            json={"active": False},
            headers=headers
        )


@pytest.mark.asyncio
async def test_business_invariants_monitoring(auth_admin_token):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {auth_admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/operations/business-invariants", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["invariants_checked"] >= 3
        assert data["negative_stock_count"] == 0
        assert data["discrepant_sales_count"] == 0
        assert data["status"] == "clean"


@pytest.mark.asyncio
async def test_disaster_recovery_backup_and_restore(auth_admin_token):
    settings.backup_encryption_key = "super-secret-backup-encryption-key-for-salesia-tests"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "Authorization": f"Bearer {auth_admin_token}",
            "Idempotency-Key": "bkup-" + uuid4().hex[:8]
        }
        res_backup = await client.post("/api/v1/operations/backup/trigger", headers=headers)
        assert res_backup.status_code == 202
        backup_data = res_backup.json()
        assert backup_data["job_type"] == "backup"
        assert backup_data["status"] == "pending"
        assert "job_id" in backup_data

        with sync_session_factory() as s:
            job = s.get(JobModel, UUID(backup_data["job_id"]))
            if job:
                job.status = "completed"
            s.commit()

        res_status = await client.get("/api/v1/operations/backup/status", headers=headers)
        assert res_status.status_code == 200
        assert "items" in res_status.json()

        key = hashlib.sha256(settings.backup_encryption_key.encode()).digest()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        clear_content = b"SQLite format 3\x00" + b"demo_backup_data"
        snapshot_id = "snap-test-" + uuid4().hex[:8]
        encrypted_data = aesgcm.encrypt(nonce, clear_content, snapshot_id.encode())
        checksum = hashlib.sha256(encrypted_data).hexdigest()
        file_path = safe_path("backups", f"{snapshot_id}.enc")
        file_path.write_bytes(encrypted_data)

        with sync_session_factory() as s:
            s.add(
                BackupSnapshotModel(
                    company_id=TEST_COMPANY_ID,
                    snapshot_id=snapshot_id,
                    status="completed",
                    encrypted=True,
                    checksum=checksum,
                    size_bytes=len(encrypted_data),
                    artifact_path=str(file_path),
                    nonce=nonce.hex(),
                    source_revision=settings.source_revision
                )
            )
            s.commit()

        restore_payload = {
            "snapshot_id": snapshot_id,
            "checksum": checksum
        }
        res_restore = await client.post("/api/v1/operations/restore/verify", json=restore_payload, headers=headers)
        assert res_restore.status_code == 200
        restore_result = res_restore.json()
        assert restore_result["integrity_check"] == "passed"
        assert restore_result["encrypted"] is True
