import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlsplit, parse_qs
from uuid import UUID, uuid4
import pytest
from sqlalchemy import select
from test_supply_chain_integrity import supply, client_for
from salesia.modules.analitica.schedules import next_schedule_time
from salesia.modules.analitica.schedule_worker import process_report_schedules
from salesia.modules.inventario.infrastructure_models import LocationStock, WarehouseLocation
from salesia.modules.operaciones.import_files import read_import_file
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import CustomerModel, InventoryStockModel, ProductModel, QuotationModel, WarehouseModel
from salesia.shared.infrastructure.models import SaleModel, UserModel, JobModel, CashSessionModel
from salesia.modules.operaciones.infrastructure_models import CollaborationTask
from salesia.modules.operaciones.jobs import execute_report_job
from salesia.modules.operaciones.jobs import execute_import


def test_import_detects_encoding_separator_mapping_and_quoted_values(tmp_path):
    path = tmp_path / "productos.csv"
    path.write_bytes('Codigo;Descripcion;Precio\r\nA1;"Madera; castaño";10\r\n'.encode("cp1252"))
    rows, columns, detected = read_import_file(path, column_mapping={"sku": "Codigo", "name": "Descripcion", "unit_price": "Precio"})
    assert detected["encoding"] == "cp1252"
    assert detected["delimiter"] == ";"
    assert rows == [{"sku": "A1", "name": "Madera; castaño", "unit_price": "10"}]
    assert columns == ["sku", "name", "unit_price"]
    corrected, _, _ = read_import_file(path, column_mapping={"sku": "Codigo"}, corrections={"1": {"sku": "A2"}})
    assert corrected[0]["sku"] == "A2"


def test_import_rejects_ambiguous_headers_and_mapping(tmp_path):
    path = tmp_path / "archivo.csv"
    path.write_text("sku,sku\nA,B\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_import_file(path)
    path.write_text("sku,name\nA,B\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_import_file(path, column_mapping={"sku": "name"})


def test_visual_schedule_uses_lima_time_and_start_date():
    config = {"frequency": "weekly", "hour": 8, "minute": 30, "weekday": 1, "day": 1, "start_date": "2026-10-14"}
    result = next_schedule_time(config, "America/Lima", datetime(2026, 10, 14, 12, tzinfo=timezone.utc))
    assert result == datetime(2026, 10, 19, 13, 30, tzinfo=timezone.utc)
    config.update(frequency="monthly", day=28)
    assert next_schedule_time(config, "America/Lima", datetime(2026, 10, 29, tzinfo=timezone.utc)) == datetime(2026, 11, 28, 13, 30, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_count_requires_recorded_quantities_and_checks_version(supply):
    client = await client_for(supply)
    try:
        created = await client.post("/api/v1/inventory/counts", json={"warehouse_id": str(supply["source"]), "product_ids": [str(supply["product_id"])]})
        assert created.status_code == 201, created.text
        count_id = created.json()["id"]
        listed = (await client.get("/api/v1/inventory/counts")).json()["items"][0]
        assert listed["lines"][0]["counted_at"] is None
        assert listed["lines"][0]["snapshot_system_quantity"] is None
        submitted = await client.put(f"/api/v1/inventory/counts/{count_id}/entries", json={"items": [{"product_id": str(supply["product_id"]), "quantity": "9"}], "submit": True, "version": 1})
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["status"] == "pending_approval"
        second = await client.put(f"/api/v1/inventory/counts/{count_id}/entries", json={"items": [{"product_id": str(supply["product_id"]), "quantity": "0"}], "version": 1})
        assert second.status_code == 409
        listed = (await client.get("/api/v1/inventory/counts")).json()["items"][0]
        assert Decimal(listed["lines"][0]["discrepancy_quantity"]) == -1
        approved = await client.post(f"/api/v1/inventory/counts/{count_id}/approve", headers={"Idempotency-Key": uuid4().hex})
        assert approved.status_code == 403
        with sync_session_factory() as db:
            assert db.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.warehouse_id == supply["source"])) == 10
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_location_dependencies_and_stock_rule_lifecycle(supply):
    client = await client_for(supply)
    try:
        payload = {"warehouse_id": str(supply["source"]), "code": "P-01", "aisle": "A", "rack": "1", "shelf": "1", "bin": "1", "capacity_units": "20"}
        location = await client.post("/api/v1/inventory/locations", json=payload)
        assert location.status_code == 201
        location_id = UUID(location.json()["id"])
        with sync_session_factory() as db:
            db.add(LocationStock(company_id=supply["company_id"], warehouse_id=supply["source"], location_id=location_id, product_id=supply["product_id"], quantity=Decimal("2")))
            db.commit()
        update = {key: value for key, value in payload.items() if key != "warehouse_id"} | {"is_active": False}
        assert (await client.put(f"/api/v1/inventory/locations/{location_id}", json=update)).status_code == 409
        rule = await client.post("/api/v1/inventory/rules", json={"warehouse_id": str(supply["source"]), "product_id": str(supply["product_id"]), "min_quantity": "4", "max_quantity": "20", "reorder_point": "6", "reorder_quantity": "10"})
        assert rule.status_code == 201, rule.text
        rule_id = rule.json()["id"]
        rows = (await client.get("/api/v1/inventory/rules")).json()["items"]
        assert Decimal(rows[0]["reorder_point"]) == 6
        assert (await client.post(f"/api/v1/inventory/rules/{rule_id}/deactivate")).json()["is_active"] is False
        assert (await client.get("/api/v1/inventory/rules")).json()["items"][0]["is_active"] is False
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_quotation_recipient_portal_and_internal_preview_are_distinct(supply):
    with sync_session_factory() as db:
        warehouse = db.get(WarehouseModel, supply["source"])
        branch_id = warehouse.branch_id
        customer = CustomerModel(company_id=supply["company_id"], code="PORTAL", doc_type="DNI", doc_number="12345678", legal_name="Cliente de portal", current_balance=Decimal("0"), credit_limit=Decimal("1000"))
        db.add(customer)
        db.commit()
        customer_id = customer.id
    client = await client_for(supply)
    try:
        created = await client.post("/api/v1/quotations", json={"customer_id": str(customer_id), "branch_id": str(branch_id), "currency": "USD", "valid_until": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "lines": [{"product_id": str(supply["product_id"]), "quantity": "1"}]}, headers={"Idempotency-Key": uuid4().hex})
        assert created.status_code == 201, created.text
        quotation_id = created.json()["quotation_id"]
        preview = await client.get(f"/api/v1/quotations/{quotation_id}/preview")
        assert preview.json()["opened_at"] is None
        sent = await client.post(f"/api/v1/quotations/{quotation_id}/send", json={"channel": "WHATSAPP", "recipient": "51999999999"})
        assert sent.status_code == 200, sent.text
        token = parse_qs(urlsplit(sent.json()["url"]).fragment)["quotation-token"][0]
        headers = {"Authorization": f"Bearer {token}"}
        opened = await client.get(f"/api/v1/quotation-portal/{quotation_id}", headers=headers)
        assert opened.status_code == 200, opened.text
        assert "customer_id" not in opened.json()
        assert "communication_log" not in opened.json()
        assert (await client.get(f"/api/v1/quotations/{quotation_id}")).json()["opened_at"] is not None
        assert (await client.get(f"/api/v1/quotation-portal/{uuid4()}", headers=headers)).status_code == 401
        assert (await client.get(f"/api/v1/quotation-portal/{quotation_id}")).status_code == 401
        rejected = await client.post(f"/api/v1/quotation-portal/{quotation_id}/accept", headers=headers, json={"accepted_by": "Cliente", "conditions_accepted": False})
        assert rejected.status_code == 422
        accepted = await client.post(f"/api/v1/quotation-portal/{quotation_id}/accept", headers=headers, json={"accepted_by": "Cliente", "conditions_accepted": True})
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["status"] == "accepted"
        repeated = await client.post(f"/api/v1/quotation-portal/{quotation_id}/accept", headers=headers, json={"accepted_by": "Cliente", "conditions_accepted": True})
        assert repeated.json()["accepted_at"] == accepted.json()["accepted_at"]
        pdf = await client.get(f"/api/v1/quotation-portal/{quotation_id}/pdf", headers=headers)
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_visual_report_schedule_runs_once_and_advances(supply):
    client = await client_for(supply)
    try:
        schedule = await client.post("/api/v1/report-schedules", json={"report_type": "REP_SALES_DETAIL", "format": "csv", "recipients": ["gerencia@salesia.enterprise"], "timezone": "America/Lima", "schedule": {"frequency": "daily", "hour": 8, "minute": 0, "weekday": 1, "day": 1, "start_date": "2026-01-01"}})
        assert schedule.status_code == 201, schedule.text
        schedule_id = UUID(schedule.json()["schedule_id"])
        current = datetime.now(timezone.utc)
        with sync_session_factory() as db:
            row = db.get(AnalyticsArtifact, schedule_id)
            data = json.loads(row.data_json)
            data["next_run_at"] = (current - timedelta(minutes=1)).isoformat()
            row.data_json = json.dumps(data)
            db.commit()
        process_report_schedules(at=current)
        process_report_schedules(at=current)
        with sync_session_factory() as db:
            row = db.get(AnalyticsArtifact, schedule_id)
            data = json.loads(row.data_json)
            assert data["runs_count"] == 1
            assert datetime.fromisoformat(data["next_run_at"]) > current
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_async_report_queue_cancellation_retry_and_worker(supply):
    client = await client_for(supply)
    try:
        queued = await client.post("/api/v1/report-runs", json={"report_type": "REP_SALES_DETAIL", "format": "csv", "async_execution": True})
        assert queued.status_code == 202 and queued.json()["status"] == "queued", queued.text
        run_id = UUID(queued.json()["run_id"])
        cancelled = await client.post(f"/api/v1/report-runs/{run_id}/cancel")
        assert cancelled.status_code == 200
        assert (await client.get(f"/api/v1/report-runs/{run_id}/download")).status_code != 200
        retried = await client.post(f"/api/v1/report-runs/{run_id}/retry")
        assert retried.status_code == 200 and retried.json()["status"] == "queued"
        with sync_session_factory() as db:
            job = db.get(JobModel, run_id)
            assert job.status == "pending" and job.cancel_requested is False
            execute_report_job(db, job)
            job.status = "completed"
            db.commit()
        response = await client.get(f"/api/v1/report-runs/{run_id}")
        assert response.json()["status"] == "completed"
        assert (await client.get(f"/api/v1/report-runs/{run_id}/download")).status_code == 200
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_custom_roles_show_impact_reject_escalation_and_preserve_admin(supply):
    client = await client_for(supply)
    try:
        key = f"custom_{uuid4().hex[:8]}"
        created = await client.post("/api/v1/roles", json={"role_key": key, "title": f"Supervisión {uuid4().hex[:6]}", "permissions": ["sales:read"]})
        assert created.status_code == 201, created.text
        with sync_session_factory() as db:
            user = UserModel(company_id=supply["company_id"], email=f"{uuid4().hex}@example.com", hashed_password="", role=key, is_active=False)
            db.add(user)
            db.commit()
            user_id = user.id
        impact = await client.get(f"/api/v1/roles/{key}/impact")
        assert impact.json()["affected_users"] == 1
        changed = await client.patch(f"/api/v1/roles/{key}", json={"title": "Supervisión comercial", "permissions": ["sales:read"], "affected_users": 0})
        assert changed.status_code == 409
        escalated = await client.patch(f"/api/v1/roles/{key}", json={"title": "Supervisión comercial", "permissions": ["platform:manage"], "affected_users": 1})
        assert escalated.status_code == 403
        changed = await client.patch(f"/api/v1/roles/{key}", json={"title": "Supervisión comercial", "permissions": ["sales:read"], "affected_users": 1})
        assert changed.status_code == 200, changed.text
        deleted = await client.delete(f"/api/v1/roles/{key}?affected_users=1")
        assert deleted.status_code == 422
        deleted = await client.delete(f"/api/v1/roles/{key}?affected_users=1&replacement_role=salesperson")
        assert deleted.status_code == 200, deleted.text
        security = await client.get(f"/api/v1/users/{user_id}/security")
        assert security.status_code == 200 and security.json()["credentials_configured"] is False
        last_admin = await client.patch(f"/api/v1/memberships/{supply['user_id']}", json={"is_active": False})
        assert last_admin.status_code == 409
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_collection_promises_create_tasks_and_remain_idempotent(supply):
    with sync_session_factory() as db:
        warehouse = db.get(WarehouseModel, supply["source"])
        customer = CustomerModel(company_id=supply["company_id"], code="DEBT", doc_type="DNI", doc_number="87654321", legal_name="Cliente deudor", current_balance=Decimal("100"), credit_limit=Decimal("500"))
        db.add(customer)
        db.flush()
        sale = SaleModel(company_id=supply["company_id"], branch_id=warehouse.branch_id, warehouse_id=warehouse.id, customer_id=customer.id, series="F001", number=1, status="confirmed", currency="PEN", subtotal_amount=Decimal("100"), total_amount=Decimal("100"), paid_amount=Decimal("0"))
        db.add(sale)
        db.commit()
        sale_id = sale.id
    client = await client_for(supply)
    try:
        payload = {"kind": "promise", "notes": "Cliente pagará en su próxima visita", "promised_amount": "40", "next_action_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}
        headers = {"Idempotency-Key": uuid4().hex}
        first = await client.post(f"/api/v1/receivables/{sale_id}/activities", json=payload, headers=headers)
        assert first.status_code == 201, first.text
        repeated = await client.post(f"/api/v1/receivables/{sale_id}/activities", json=payload, headers=headers)
        assert repeated.json()["id"] == first.json()["id"]
        second = await client.post(f"/api/v1/receivables/{sale_id}/activities", json={"kind": "contact", "notes": "Contacto adicional"}, headers={"Idempotency-Key": uuid4().hex})
        assert second.status_code == 201, second.text
        context = await client.get(f"/api/v1/receivables/{sale_id}/context")
        assert context.json()["currency"] == "PEN"
        assert len(context.json()["activities"]) == 2
        with sync_session_factory() as db:
            tasks = db.scalars(select(CollaborationTask).where(CollaborationTask.company_id == supply["company_id"], CollaborationTask.resource_id == sale_id)).all()
            assert len(tasks) == 1 and tasks[0].assignee_id == supply["user_id"]
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_cash_count_validates_denomination_total(supply):
    with sync_session_factory() as db:
        warehouse = db.get(WarehouseModel, supply["source"])
        cash = CashSessionModel(company_id=supply["company_id"], branch_id=warehouse.branch_id, user_id=supply["user_id"], terminal_code="CAJA-01", expected_cash=Decimal("100"), initial_cash=Decimal("100"), status="open")
        db.add(cash)
        db.commit()
        cash_id = cash.id
    client = await client_for(supply)
    try:
        bad = await client.post(f"/api/v1/cash-sessions/{cash_id}/blind-count", json={"counted_cash": "99", "denominations": {"50": 2}})
        assert bad.status_code == 422
        good = await client.post(f"/api/v1/cash-sessions/{cash_id}/blind-count", json={"counted_cash": "100", "denominations": {"50": 2}, "non_cash_totals": {"CARD": "20"}})
        assert good.status_code == 200 and good.json()["requires_approval"] is False
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_import_mapping_corrections_and_superseded_simulation(supply):
    client = await client_for(supply)
    try:
        content = "Codigo;Tipo;Documento;Cliente\r\nC-01;DNI;12345678;\r\n".encode("utf-8")
        intent = await client.post("/api/v1/attachments/upload-intents", json={"file_name": "clientes.csv", "mime_type": "text/csv", "file_size_bytes": len(content), "related_entity_type": "import"})
        assert intent.status_code == 201, intent.text
        upload = intent.json()
        uploaded = await client.put(upload["upload_url"], content=content, headers={"X-Upload-Token": upload["upload_token"], "Content-Type": "text/csv"})
        assert uploaded.status_code == 200, uploaded.text
        assert (await client.post(f"/api/v1/attachments/{upload['attachment_id']}/complete")).status_code == 200
        base = {"target_entity": "customers", "attachment_id": upload["attachment_id"]}
        inspected = await client.post("/api/v1/imports/inspect", json=base)
        assert inspected.json()["delimiter"] == ";"
        mapping = {"code": "Codigo", "doc_type": "Tipo", "doc_number": "Documento", "legal_name": "Cliente"}
        staged = await client.post("/api/v1/imports", json={**base, "column_mapping": mapping}, headers={"Idempotency-Key": uuid4().hex})
        assert staged.status_code == 202 and staged.json()["result"]["invalid_rows"] == 1, staged.text
        original_id = staged.json()["job_id"]
        corrected = await client.post("/api/v1/imports", json={**base, "column_mapping": mapping, "source_import_id": original_id, "corrections": {"1": {"legal_name": "Cliente corregido"}}}, headers={"Idempotency-Key": uuid4().hex})
        assert corrected.status_code == 202 and corrected.json()["result"]["valid_rows"] == 1, corrected.text
        assert (await client.post(f"/api/v1/imports/{original_id}/commit")).status_code == 409
        corrected_id = UUID(corrected.json()["job_id"])
        assert (await client.post(f"/api/v1/imports/{corrected_id}/commit")).status_code == 202
        with sync_session_factory() as db:
            job = db.get(JobModel, corrected_id)
            result = execute_import(db, job)
            assert result["processed_rows"] == 1
            job.status = "completed"
            db.commit()
            customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == supply["company_id"], CustomerModel.code == "C-01"))
            assert customer.legal_name == "Cliente corregido"
        history = await client.get("/api/v1/imports")
        assert any(row["job_id"] == str(corrected_id) for row in history.json()["items"])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_insight_bulk_actions_create_linked_tasks_without_duplicates(supply):
    insight_id = uuid4()
    with sync_session_factory() as db:
        db.add(AnalyticsArtifact(id=insight_id, company_id=supply["company_id"], kind="insight", artifact_key=uuid4().hex, version=1, status="pending", data_json=json.dumps({"id": str(insight_id), "title": "Revisar reposición de producto", "status": "pending", "severity": "high", "entity_type": "Product", "entity_id": str(supply["product_id"])}), created_by=supply["user_id"]))
        db.commit()
    client = await client_for(supply)
    try:
        payload = {"ids": [str(insight_id)], "action": "task", "assignee_id": str(supply["user_id"]), "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "priority": "high"}
        first = await client.post("/api/v1/insights/bulk-actions", json=payload)
        assert first.status_code == 200, first.text
        second = await client.post("/api/v1/insights/bulk-actions", json=payload)
        assert second.json()["task_ids"] == first.json()["task_ids"]
        with sync_session_factory() as db:
            tasks = db.scalars(select(CollaborationTask).where(CollaborationTask.company_id == supply["company_id"], CollaborationTask.title == "Revisar reposición de producto")).all()
            assert len(tasks) == 1 and tasks[0].resource_id == supply["product_id"]
            assert tasks[0].resource_type == "product"
        snoozed = await client.post("/api/v1/insights/bulk-actions", json={"ids": [str(insight_id)], "action": "snooze", "snoozed_until": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()})
        assert snoozed.status_code == 200
        invalid = await client.post("/api/v1/insights/bulk-actions", json={"ids": [str(insight_id), str(uuid4())], "action": "resolve"})
        assert invalid.status_code == 404
        with sync_session_factory() as db:
            assert db.get(AnalyticsArtifact, insight_id).status == "in_review"
    finally:
        await client.aclose()
