import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, sync_engine, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    PaymentModel,
    KardexMovementModel
)
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000201")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000209")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000202")
BRANCH_B = UUID("00000000-0000-0000-0000-000000000292")
CUSTOMER_A = UUID("00000000-0000-0000-0000-000000000214")
CUSTOMER_B = UUID("00000000-0000-0000-0000-000000000295")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000203")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000208")
USER_ANALYST_A = UUID("00000000-0000-0000-0000-000000000205")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000207")
PRODUCT_1 = UUID("00000000-0000-0000-0000-000000000221")
PRODUCT_2 = UUID("00000000-0000-0000-0000-000000000222")


@pytest.fixture(autouse=True, scope="module")
def setup_part16_data():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999000201", "Empresa A P16"), (COMPANY_B, "20999000209", "Empresa B P16")]:
            comp = session.scalar(select(CompanyModel).where(CompanyModel.id == cid))
            if not comp:
                session.add(CompanyModel(id=cid, tax_id=tax, legal_name=name, trade_name=name, base_currency="USD", is_active=True))
        session.flush()
        for bid, cid, code in [(BRANCH_A, COMPANY_A, "SUC-A"), (BRANCH_B, COMPANY_B, "SUC-B")]:
            br = session.scalar(select(BranchModel).where(BranchModel.id == bid))
            if not br:
                session.add(BranchModel(id=bid, company_id=cid, code=code, name=f"Sucursal {code}", timezone="America/Lima", is_active=True))
        for cust_id, cid, doc in [(CUSTOMER_A, COMPANY_A, "10000001"), (CUSTOMER_B, COMPANY_B, "10000002")]:
            cust = session.scalar(select(CustomerModel).where(CustomerModel.id == cust_id))
            if not cust:
                session.add(CustomerModel(id=cust_id, company_id=cid, code=f"CLI-{doc}", doc_type="DNI", doc_number=doc, legal_name=f"Cliente {doc}", credit_limit=Decimal("5000.00"), current_balance=Decimal("0.00"), is_active=True))
        p1 = session.scalar(select(ProductModel).where(ProductModel.id == PRODUCT_1))
        if not p1:
            session.add(ProductModel(id=PRODUCT_1, company_id=COMPANY_A, sku="PROD-001", name="Monitor 27", category="Tecnologia", unit_of_measure="NIU", unit_price=Decimal("200.000000"), unit_cost=Decimal("120.000000"), tax_rate=Decimal("0.180000"), is_active=True))
        p2 = session.scalar(select(ProductModel).where(ProductModel.id == PRODUCT_2))
        if not p2:
            session.add(ProductModel(id=PRODUCT_2, company_id=COMPANY_A, sku="PROD-002", name="Cable HDMI", category="Cables", unit_of_measure="NIU", unit_price=Decimal("15.000000"), unit_cost=Decimal("5.000000"), tax_rate=Decimal("0.180000"), is_active=True))
        session.commit()
    yield


@pytest.fixture
def auth_admin_a():
    with sync_session_factory() as session:
        return create_durable_identity(session, company_id=COMPANY_A, user_id=USER_ADMIN_A, role="company_admin", email="admin_a_p16@salesia.enterprise")


@pytest.fixture
def auth_admin_b():
    with sync_session_factory() as session:
        return create_durable_identity(session, company_id=COMPANY_B, user_id=USER_ADMIN_B, role="company_admin", email="admin_b_p16@salesia.enterprise")


@pytest.fixture
def auth_analyst_a():
    with sync_session_factory() as session:
        return create_durable_identity(session, company_id=COMPANY_A, user_id=USER_ANALYST_A, role="analyst", email="analyst_a_p16@salesia.enterprise")


@pytest.fixture
def auth_seller_a():
    with sync_session_factory() as session:
        return create_durable_identity(session, company_id=COMPANY_A, user_id=USER_SELLER_A, role="salesperson", email="seller_a_p16@salesia.enterprise")


@pytest.mark.asyncio
async def test_api_068_post_datasets_validation_persistence_and_cross_tenant(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={"name": ""})
        assert invalid_res.status_code == 422

        valid_payload = {
            "name": "Dataset Ventas Tickets Q4",
            "description": "Universo operacional de ventas confirmadas",
            "grain": "ticket",
            "source_entity": "sales",
            "variable_scale": "quantitative_continuous",
            "filters": {
                "branch_id": str(BRANCH_A),
                "currency": "USD",
                "statuses": ["confirmed", "paid"],
                "returns_handling": "net_of_returns"
            },
            "variables": [
                {"name": "total_amount", "scale": "quantitative_continuous", "unit": "USD", "data_type": "decimal"},
                {"name": "paid_amount", "scale": "quantitative_continuous", "unit": "USD", "data_type": "decimal"}
            ]
        }
        create_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json=valid_payload)
        assert create_res.status_code == 201
        data = create_res.json()
        dataset_id = data["id"]
        assert data["name"] == valid_payload["name"]
        assert data["grain"] == "ticket"
        assert data["current_version"] == 1
        assert data["filters"]["currency"] == "USD"

        cross_res = await client.get(f"/api/v1/datasets/{dataset_id}/versions/1", headers=auth_admin_b["headers"])
        assert cross_res.status_code in (404, 403)


@pytest.mark.asyncio
async def test_dset_001_grain_definition_and_payment_join_does_not_multiply_sale_total(auth_admin_a):
    transport = ASGITransport(app=app)
    sale_id = uuid4()
    with sync_session_factory() as session:
        sale = SaleModel(
            id=sale_id,
            company_id=COMPANY_A,
            branch_id=BRANCH_A,
            customer_id=CUSTOMER_A,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("100.000000"),
            tax_amount=Decimal("18.000000"),
            total_amount=Decimal("118.000000"),
            paid_amount=Decimal("118.000000"),
            created_at=datetime.now(timezone.utc)
        )
        session.add(sale)
        session.flush()

        p1 = PaymentModel(
            id=uuid4(),
            company_id=COMPANY_A,
            sale_id=sale_id,
            payment_method="cash",
            amount=Decimal("50.000000"),
            status="confirmed",
            created_at=datetime.now(timezone.utc)
        )
        p2 = PaymentModel(
            id=uuid4(),
            company_id=COMPANY_A,
            sale_id=sale_id,
            payment_method="card",
            amount=Decimal("68.000000"),
            status="confirmed",
            created_at=datetime.now(timezone.utc)
        )
        session.add_all([p1, p2])
        session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Grano Ticket y Pagos",
            "grain": "ticket",
            "source_entity": "sales",
            "filters": {"currency": "USD", "statuses": ["confirmed"]}
        })
        assert dataset_res.status_code == 201
        dataset_id = dataset_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert ver_res.status_code == 201
        ver_data = ver_res.json()
        version_num = ver_data["version"]

        loaded_res = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{version_num}", headers=auth_admin_a["headers"])
        assert loaded_res.status_code == 200
        details = loaded_res.json()
        target_rows = [r for r in details.get("preview_sample", []) if r.get("sale_id") == str(sale_id)]
        assert len(target_rows) == 1
        assert Decimal(str(target_rows[0]["total_amount"])) == Decimal("118.000000")
        assert Decimal(str(target_rows[0]["paid_amount"])) == Decimal("118.000000")


@pytest.mark.asyncio
async def test_dset_002_dset_007_operational_source_and_annulled_sale_exclusion_explanation(auth_admin_a):
    transport = ASGITransport(app=app)
    sale_annulled_id = uuid4()
    with sync_session_factory() as session:
        annulled_sale = SaleModel(
            id=sale_annulled_id,
            company_id=COMPANY_A,
            branch_id=BRANCH_A,
            customer_id=CUSTOMER_A,
            series="F001",
            number=int(uuid4().int % 900000 + 100000),
            status="cancelled",
            currency="USD",
            subtotal_amount=Decimal("300.000000"),
            tax_amount=Decimal("54.000000"),
            total_amount=Decimal("354.000000"),
            paid_amount=Decimal("0.000000"),
            created_at=datetime.now(timezone.utc)
        )
        session.add(annulled_sale)
        session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Explicabilidad Anuladas",
            "grain": "ticket",
            "source_entity": "sales"
        })
        dataset_id = dataset_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert ver_res.status_code == 201
        v_data = ver_res.json()

        quality = v_data["quality_report"]
        assert "total_received" in quality
        assert "total_used" in quality
        assert "total_excluded" in quality
        assert quality["total_excluded"] >= 1
        assert "excluded_by_reason" in quality
        assert quality["excluded_by_reason"].get("annulled_status", 0) >= 1 or quality["excluded_by_reason"].get("cancelled_status", 0) >= 1
        sample_ids = [r.get("sale_id") for r in v_data.get("preview_sample", [])]
        assert str(sale_annulled_id) not in sample_ids


@pytest.mark.asyncio
async def test_dset_003_dset_004_snapshot_reproducibility_and_filter_context(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        filters_original = {
            "branch_id": str(BRANCH_A),
            "currency": "USD",
            "statuses": ["confirmed", "paid"],
            "period": "30d",
            "returns_handling": "net_of_returns"
        }
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Snapshot Reproducible",
            "grain": "ticket",
            "filters": filters_original
        })
        dataset_id = dataset_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert ver_res.status_code == 201
        ver_info = ver_res.json()
        version_num = ver_info["version"]
        initial_hash = ver_info["data_hash"]
        initial_count = ver_info["row_count"]

        analysis_create = await client.post("/api/v1/analyses", headers=auth_admin_a["headers"], json={
            "name": "Analisis Descriptivo Ventas Snapshot",
            "dataset_id": dataset_id,
            "dataset_version": version_num,
            "variable_name": "total_amount",
            "analysis_type": "summary"
        })
        assert analysis_create.status_code == 201
        analysis_id = analysis_create.json()["id"]
        initial_mean = analysis_create.json()["result"]["mean"]

        with sync_session_factory() as session:
            new_sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=CUSTOMER_A,
                series="F001",
                number=int(uuid4().int % 900000 + 100000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("9999.000000"),
                tax_amount=Decimal("1799.820000"),
                total_amount=Decimal("11798.820000"),
                paid_amount=Decimal("11798.820000"),
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_sale)
            session.commit()

        ver_recheck = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{version_num}", headers=auth_admin_a["headers"])
        assert ver_recheck.status_code == 200
        assert ver_recheck.json()["data_hash"] == initial_hash
        assert ver_recheck.json()["row_count"] == initial_count

        analysis_get = await client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_admin_a["headers"])
        assert analysis_get.status_code == 200
        reopened = analysis_get.json()
        assert reopened["context"]["currency"] == "USD"
        assert reopened["context"]["returns_handling"] == "net_of_returns"
        assert reopened["result"]["mean"] == initial_mean

        repeat_res = await client.post(f"/api/v1/analyses/{analysis_id}/repeat", headers=auth_admin_a["headers"], json={})
        assert repeat_res.status_code == 200
        repeated = repeat_res.json()
        assert repeated["original_analysis_id"] == str(analysis_id)
        assert repeated["result"]["mean"] == initial_mean
        assert repeated["result"]["count"] == initial_count


@pytest.mark.asyncio
async def test_dset_005_dset_006_consistent_snapshot_and_large_volume_storage(auth_admin_a, tmp_path, monkeypatch):
    from salesia.shared.infrastructure.config import settings
    monkeypatch.setattr(settings, "private_storage_path", str(tmp_path))
    transport = ASGITransport(app=app)

    with sync_session_factory() as session:
        for i in range(15):
            sid = uuid4()
            sale = SaleModel(
                id=sid,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=CUSTOMER_A,
                series="F002",
                number=int(uuid4().int % 900000 + 100000),
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("100.00"),
                tax_amount=Decimal("18.00"),
                total_amount=Decimal("118.00"),
                paid_amount=Decimal("118.00"),
                created_at=datetime.now(timezone.utc)
            )
            line = SaleLineModel(
                id=uuid4(),
                sale_id=sid,
                company_id=COMPANY_A,
                product_id=PRODUCT_1,
                line_number=i + 1,
                sku_snapshot="PROD-001",
                name_snapshot="Monitor 27",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("1.000000"),
                unit_price_snapshot=Decimal("100.000000"),
                unit_cost_snapshot=Decimal("60.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.180000"),
                subtotal_amount=Decimal("100.000000"),
                tax_amount=Decimal("18.000000"),
                total_amount=Decimal("118.000000")
            )
            session.add(sale)
            session.flush()
            session.add(line)
        session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Lineas Consistente",
            "grain": "lines",
            "source_entity": "sales"
        })
        dataset_id = dataset_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert ver_res.status_code == 201
        v_data = ver_res.json()
        assert v_data["row_count"] >= 15
        assert v_data["storage_type"] in ("inline", "private_file")
        assert len(v_data["preview_sample"]) <= 10
        for row in v_data["preview_sample"]:
            assert "line_id" in row
            assert "sale_id" in row
            assert "sku_snapshot" in row


@pytest.mark.asyncio
async def test_dset_008_dset_009_null_handling_and_duplicate_differentiation(auth_admin_a):
    transport = ASGITransport(app=app)
    sale_1 = uuid4()
    sale_2 = uuid4()
    with sync_session_factory() as session:
        s1 = SaleModel(
            id=sale_1,
            company_id=COMPANY_A,
            branch_id=BRANCH_A,
            customer_id=CUSTOMER_A,
            series="F003",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("250.000000"),
            tax_amount=Decimal("45.000000"),
            total_amount=Decimal("295.000000"),
            paid_amount=Decimal("295.000000"),
            created_at=datetime.now(timezone.utc)
        )
        s2 = SaleModel(
            id=sale_2,
            company_id=COMPANY_A,
            branch_id=BRANCH_A,
            customer_id=CUSTOMER_A,
            series="F003",
            number=int(uuid4().int % 900000 + 100000),
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("250.000000"),
            tax_amount=Decimal("45.000000"),
            total_amount=Decimal("295.000000"),
            paid_amount=Decimal("295.000000"),
            created_at=datetime.now(timezone.utc)
        )
        session.add_all([s1, s2])
        session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Deduplicacion y Nulos",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert ver_res.status_code == 201
        v_data = ver_res.json()
        matching = [r for r in v_data.get("preview_sample", []) if r.get("sale_id") in (str(sale_1), str(sale_2))]
        assert len(matching) == 2
        assert matching[0]["sale_id"] != matching[1]["sale_id"]
        assert matching[0]["total_amount"] == matching[1]["total_amount"]


@pytest.mark.asyncio
async def test_dset_010_dset_011_types_units_and_transformations_pipeline(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Tipos y Transformaciones",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        ver_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        ver_num = ver_res.json()["version"]

        analysis_res = await client.post("/api/v1/analyses", headers=auth_admin_a["headers"], json={
            "name": "Analisis Con Winsorizacion",
            "dataset_id": dataset_id,
            "dataset_version": ver_num,
            "variable_name": "total_amount",
            "analysis_type": "summary",
            "parameters": {
                "transformations": ["winsorization_95"]
            }
        })
        assert analysis_res.status_code == 201
        res = analysis_res.json()
        assert "raw_metrics" in res["result"]
        assert "transformed_metrics" in res["result"]
        assert "winsorization_95" in res["transformations_applied"]


@pytest.mark.asyncio
async def test_dset_012_dset_013_late_data_and_incremental_projection(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Datos Tardios",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        ver_1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        v1_hash = ver_1.json()["data_hash"]
        v1_ver = ver_1.json()["version"]

        ver_2 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={
            "watermark": datetime.now(timezone.utc).isoformat()
        })
        assert ver_2.status_code == 201
        assert ver_2.json()["version"] == v1_ver + 1

        v1_check = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{v1_ver}", headers=auth_admin_a["headers"])
        assert v1_check.status_code == 200
        assert v1_check.json()["data_hash"] == v1_hash


@pytest.mark.asyncio
async def test_dset_014_reconstruction_rebuild_validation_before_publish(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Reconstruccion",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        v1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        assert v1.status_code == 201

        rebuild_res = await client.post(f"/api/v1/datasets/{dataset_id}/rebuild", headers=auth_admin_a["headers"], json={})
        assert rebuild_res.status_code == 200
        rebuild_data = rebuild_res.json()
        assert rebuild_data["status"] == "published"
        assert "comparison_validation" in rebuild_data
        assert rebuild_data["comparison_validation"]["passed"] is True
        assert rebuild_data["new_version"] >= 2


@pytest.mark.asyncio
async def test_dset_015_permissions_mask_costs_and_sensitive_fields(auth_admin_a, auth_analyst_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Permisos y Mascaras",
            "grain": "lines"
        })
        dataset_id = dataset_res.json()["id"]
        v1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        v1_num = v1.json()["version"]

        admin_view = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{v1_num}", headers=auth_admin_a["headers"])
        assert admin_view.status_code == 200
        admin_sample = admin_view.json()["preview_sample"]
        if admin_sample:
            assert "unit_cost" in admin_sample[0]

        analyst_view = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{v1_num}", headers=auth_analyst_a["headers"])
        assert analyst_view.status_code == 200
        analyst_sample = analyst_view.json()["preview_sample"]
        if analyst_sample:
            assert analyst_sample[0].get("unit_cost") in (None, "***", "REDACTED")


@pytest.mark.asyncio
async def test_dset_016_preview_sample_and_scope_labeling(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Muestra Etiquetada",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        v1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        v1_num = v1.json()["version"]

        loaded = await client.get(f"/api/v1/datasets/{dataset_id}/versions/{v1_num}", headers=auth_admin_a["headers"])
        assert loaded.status_code == 200
        data = loaded.json()
        assert "scope_type" in data
        assert data["scope_type"] in ("sample", "population", "aggregate")
        assert "sample_size" in data
        assert "total_population" in data
        assert "sampling_method" in data


@pytest.mark.asyncio
async def test_dset_017_dset_018_version_history_dependent_analyses_and_retention(auth_admin_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Historial y Retencion",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        v1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        v1_num = v1.json()["version"]

        await client.post("/api/v1/analyses", headers=auth_admin_a["headers"], json={
            "name": "Analisis Dependiente",
            "dataset_id": dataset_id,
            "dataset_version": v1_num,
            "variable_name": "total_amount"
        })

        history_res = await client.get(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"])
        assert history_res.status_code == 200
        items = history_res.json()["items"]
        assert len(items) >= 1
        target_v = next(i for i in items if i["version"] == v1_num)
        assert target_v["dependent_analyses_count"] >= 1
        assert "created_by" in target_v
        assert "data_hash" in target_v

        del_fail = await client.delete(f"/api/v1/datasets/{dataset_id}/versions/{v1_num}", headers=auth_admin_a["headers"])
        assert del_fail.status_code == 409

        expire_res = await client.post(f"/api/v1/datasets/{dataset_id}/versions/{v1_num}/expire", headers=auth_admin_a["headers"], json={
            "retention_reason": "politica_retencion_90_dias"
        })
        assert expire_res.status_code == 200
        expired_data = expire_res.json()
        assert expired_data["status"] == "expired"
        assert expired_data["data_available"] is False
        assert "data_hash" in expired_data


@pytest.mark.asyncio
async def test_dset_019_quality_visible_panel_and_reg16_empty_dataset(auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        empty_res = await client.post("/api/v1/datasets", headers=auth_admin_b["headers"], json={
            "name": "Dataset Vacio Empresa B",
            "grain": "ticket"
        })
        assert empty_res.status_code == 201
        empty_id = empty_res.json()["id"]

        ver_res = await client.post(f"/api/v1/datasets/{empty_id}/versions", headers=auth_admin_b["headers"], json={})
        assert ver_res.status_code == 201
        v_data = ver_res.json()
        assert v_data["row_count"] == 0

        quality = v_data["quality_report"]
        assert quality["total_received"] == 0
        assert quality["total_used"] == 0
        assert quality["completeness_pct"] == 100.0 or quality["completeness_pct"] == 0.0

        analysis_res = await client.post("/api/v1/analyses", headers=auth_admin_b["headers"], json={
            "name": "Analisis Sobre Dataset Vacio",
            "dataset_id": empty_id,
            "dataset_version": v_data["version"],
            "variable_name": "total_amount",
            "analysis_type": "summary"
        })
        assert analysis_res.status_code in (200, 201)
        a_data = analysis_res.json()
        res = a_data["result"]
        assert res["count"] == 0
        assert res["mean"] is None
        assert res["median"] is None
        assert res["minimum"] is None
        assert res["maximum"] is None
        assert a_data["status"] == "completed"


@pytest.mark.asyncio
async def test_api_077_api_078_api_079_analyses_listing_details_and_repeat_traceability(auth_admin_a, auth_admin_b):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dataset_res = await client.post("/api/v1/datasets", headers=auth_admin_a["headers"], json={
            "name": "Dataset Analisis Listado",
            "grain": "ticket"
        })
        dataset_id = dataset_res.json()["id"]
        v1 = await client.post(f"/api/v1/datasets/{dataset_id}/versions", headers=auth_admin_a["headers"], json={})
        v1_num = v1.json()["version"]

        a1 = await client.post("/api/v1/analyses", headers=auth_admin_a["headers"], json={
            "name": "Analisis A1",
            "dataset_id": dataset_id,
            "dataset_version": v1_num,
            "variable_name": "total_amount"
        })
        assert a1.status_code == 201
        a1_id = a1.json()["id"]

        list_res = await client.get(f"/api/v1/analyses?dataset_id={dataset_id}&limit=10", headers=auth_admin_a["headers"])
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert len(items) >= 1
        assert any(i["id"] == str(a1_id) for i in items)

        cross_res = await client.get(f"/api/v1/analyses/{a1_id}", headers=auth_admin_b["headers"])
        assert cross_res.status_code in (404, 403)

        get_res = await client.get(f"/api/v1/analyses/{a1_id}", headers=auth_admin_a["headers"])
        assert get_res.status_code == 200
        detail = get_res.json()
        assert detail["id"] == str(a1_id)
        assert "algorithm_version" in detail
        assert "explanation" in detail
        assert "causalidad" not in detail["explanation"].lower() or "no implica causalidad" in detail["explanation"].lower()

        repeat_res = await client.post(f"/api/v1/analyses/{a1_id}/repeat", headers=auth_admin_a["headers"], json={})
        assert repeat_res.status_code == 200
        rep = repeat_res.json()
        assert rep["id"] != str(a1_id)
        assert rep["original_analysis_id"] == str(a1_id)
        assert rep["parent_id"] == str(a1_id)
        assert rep["result"]["mean"] == detail["result"]["mean"]
