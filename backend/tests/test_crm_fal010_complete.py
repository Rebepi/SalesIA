from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    UserModel,
    QuotationModel,
    OrderModel,
    AuditLogModel
)
from salesia.modules.clientes.infrastructure.models import (
    CustomerProfileModel,
    CustomerContactModel,
    CustomerAddressModel,
    CustomerNoteModel,
    CustomerOpportunityModel,
    CustomerActivityModel,
    CustomerLoyaltyLedgerModel,
    CustomerSegmentModel
)
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000009")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000002")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000004")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000003")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000005")
USER_PORTAL_A = UUID("00000000-0000-0000-0000-000000000007")


@pytest.fixture(autouse=True, scope="module")
def setup_crm_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax in [(COMPANY_A, "20111111111"), (COMPANY_B, "20222222222")]:
            comp = session.execute(select(CompanyModel).where(CompanyModel.id == cid)).scalar_one_or_none()
            if not comp:
                session.add(CompanyModel(
                    id=cid,
                    tax_id=tax,
                    legal_name=f"EMPRESA TEST {tax}",
                    trade_name=f"TRADE {tax}",
                    base_currency="USD",
                    is_active=True
                ))
        branch = session.execute(select(BranchModel).where(BranchModel.id == BRANCH_A)).scalar_one_or_none()
        if not branch:
            session.add(BranchModel(
                id=BRANCH_A,
                company_id=COMPANY_A,
                code="SUC-MAIN",
                name="Sucursal Matriz",
                timezone="America/Lima",
                is_active=True
            ))
        wh = session.execute(select(WarehouseModel).where(WarehouseModel.id == WAREHOUSE_A)).scalar_one_or_none()
        if not wh:
            session.add(WarehouseModel(
                id=WAREHOUSE_A,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                code="ALM-MAIN",
                name="Almacen Principal",
                is_active=True
            ))
        session.commit()
    yield


@pytest.fixture
def admin_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        user_id=USER_ADMIN_A,
        role="company_admin",
        email="admin@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def seller_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        user_id=USER_SELLER_A,
        role="salesperson",
        email="seller@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def company_b_headers():
    identity = create_durable_identity(
        company_id=COMPANY_B,
        user_id=uuid4(),
        role="company_admin",
        email="admin_b@tenant_b.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_crm_001_customer_create_and_update(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_ruc = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={
                "code": "CLI-INV-1",
                "doc_type": "RUC",
                "doc_number": "123",
                "legal_name": "EMPRESA RUC CORTO"
            }
        )
        assert invalid_ruc.status_code == 422
        assert invalid_ruc.json()["detail"]["field"] == "doc_number"

        invalid_email = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={
                "code": "CLI-INV-2",
                "doc_type": "DNI",
                "doc_number": "12345678",
                "legal_name": "PERSONA EMAIL INVALIDO",
                "email": "correo_sin_arroba"
            }
        )
        assert invalid_email.status_code == 422
        assert invalid_email.json()["detail"]["field"] == "email"

        valid_dni = f"4{uuid4().int % 10000000:07d}"
        create_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={
                "code": f"CLI-{valid_dni}",
                "doc_type": "DNI",
                "doc_number": valid_dni,
                "legal_name": "JUAN PEREZ INTERNACIONAL",
                "email": "juan.perez@empresa.com",
                "phone": "+34 612 34 56 78",
                "credit_limit": 12000.00
            }
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["doc_number"] == valid_dni
        assert data["phone"] == "+34 612 34 56 78"
        customer_id = data["id"]

        update_res = await client.patch(
            f"/api/v1/customers/{customer_id}",
            headers=admin_headers,
            json={
                "legal_name": "JUAN PEREZ MODIFICADO",
                "phone": "+1 (555) 019-2834"
            }
        )
        assert update_res.status_code == 200
        assert update_res.json()["legal_name"] == "JUAN PEREZ MODIFICADO"


@pytest.mark.asyncio
async def test_crm_002_duplicate_detection_and_similarity(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ruc_num = f"20{uuid4().int % 1000000000:09d}"
        await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={
                "code": f"CLI-{ruc_num[:6]}",
                "doc_type": "RUC",
                "doc_number": ruc_num,
                "legal_name": "ACME INDUSTRIAL CORPORACION S.A.C.",
                "email": "ventas@acme-corp.com"
            }
        )

        check_exact = await client.post(
            "/api/v1/customers/duplicates/check",
            headers=admin_headers,
            json={
                "doc_type": "RUC",
                "doc_number": ruc_num
            }
        )
        assert check_exact.status_code == 200
        assert check_exact.json()["is_exact_duplicate"] is True

        check_soft = await client.post(
            "/api/v1/customers/duplicates/check",
            headers=admin_headers,
            json={
                "doc_type": "RUC",
                "doc_number": f"20{uuid4().int % 1000000000:09d}",
                "legal_name": "ACME INDUSTRIAL S.A.C.",
                "email": "ventas@acme-corp.com"
            }
        )
        assert check_soft.status_code == 200
        assert check_soft.json()["is_exact_duplicate"] is False
        assert len(check_soft.json()["potential_matches"]) > 0

        diff_doc = f"20{uuid4().int % 1000000000:09d}"
        allow_creation = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={
                "code": f"CLI-{diff_doc[:6]}",
                "doc_type": "RUC",
                "doc_number": diff_doc,
                "legal_name": "ACME INDUSTRIAL PERU S.A.C."
            }
        )
        assert allow_creation.status_code == 201


@pytest.mark.asyncio
async def test_crm_003_controlled_merge_workflow(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        d1 = f"20{uuid4().int % 1000000000:09d}"
        d2 = f"20{uuid4().int % 1000000000:09d}"
        res1 = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{d1[:6]}", "doc_type": "RUC", "doc_number": d1, "legal_name": "CLIENTE MAESTRO SAC", "credit_limit": 50000.0}
        )
        res2 = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{d2[:6]}", "doc_type": "RUC", "doc_number": d2, "legal_name": "CLIENTE DUPLICADO SAC", "credit_limit": 20000.0}
        )
        c1_id = res1.json()["id"]
        c2_id = res2.json()["id"]

        with sync_session_factory() as session:
            c2_obj = session.scalar(select(CustomerModel).where(CustomerModel.id == UUID(c2_id)))
            c2_obj.current_balance = Decimal("7500.000000")
            session.commit()

        self_merge = await client.post(
            "/api/v1/customers/merge",
            headers=admin_headers,
            json={"primary_customer_id": c1_id, "duplicate_customer_id": c1_id}
        )
        assert self_merge.status_code == 409

        preview_res = await client.post(
            "/api/v1/customers/merge/preview",
            headers=admin_headers,
            json={"primary_customer_id": c1_id, "duplicate_customer_id": c2_id}
        )
        assert preview_res.status_code == 200
        assert Decimal(preview_res.json()["impact"]["balance_transfer"]) == Decimal("7500.000000")

        merge_exec = await client.post(
            "/api/v1/customers/merge",
            headers=admin_headers,
            json={"primary_customer_id": c1_id, "duplicate_customer_id": c2_id}
        )
        assert merge_exec.status_code == 200
        assert merge_exec.json()["status"] == "completed"
        assert Decimal(merge_exec.json()["primary_current_balance"]) == Decimal("7500.000000")

        c2_get = await client.get(f"/api/v1/customers/{c2_id}", headers=admin_headers)
        assert c2_get.status_code == 200
        assert c2_get.json()["is_active"] is False


@pytest.mark.asyncio
async def test_crm_004_contacts_and_addresses(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "CONTACTOS Y SEDES SAC"}
        )
        cid = c_res.json()["id"]

        contact_res = await client.post(
            f"/api/v1/customers/{cid}/contacts",
            headers=admin_headers,
            json={
                "name": "Maria Lopez",
                "role": "Jefa de Finanzas",
                "email": "mlopez@empresa.com",
                "phone": "+51 987 654 321",
                "is_primary": True,
                "preferences": {"canal": "whatsapp"}
            }
        )
        assert contact_res.status_code == 201
        contact_id = contact_res.json()["id"]

        addr_res = await client.post(
            f"/api/v1/customers/{cid}/addresses",
            headers=admin_headers,
            json={
                "address_type": "fiscal",
                "street": "Av. Los Negocios 123",
                "city": "Lima",
                "country": "PE",
                "is_primary": True
            }
        )
        assert addr_res.status_code == 201
        addr_id = addr_res.json()["id"]

        contacts_list = await client.get(f"/api/v1/customers/{cid}/contacts", headers=admin_headers)
        assert len(contacts_list.json()) == 1

        del_addr = await client.delete(f"/api/v1/customers/{cid}/addresses/{addr_id}", headers=admin_headers)
        assert del_addr.status_code == 200

        del_contact = await client.delete(f"/api/v1/customers/{cid}/contacts/{contact_id}", headers=admin_headers)
        assert del_contact.status_code == 200


@pytest.mark.asyncio
async def test_crm_005_history_and_reconciliation(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "HISTORIAL RECONCIL S.A."}
        )
        cid = UUID(c_res.json()["id"])

        with sync_session_factory() as session:
            s1 = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=cid,
                series="F001",
                number=uuid4().int % 100000,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("1000.00"),
                tax_amount=Decimal("180.00"),
                total_amount=Decimal("1180.00"),
                paid_amount=Decimal("500.00")
            )
            session.add(s1)
            session.commit()

        hist_res = await client.get(f"/api/v1/customers/{cid}/history", headers=admin_headers)
        assert hist_res.status_code == 200
        data = hist_res.json()
        assert Decimal(data["total_billed"]) == Decimal("1180.00")
        assert Decimal(data["total_paid"]) == Decimal("500.00")
        assert Decimal(data["reconciled_balance"]) == Decimal("680.00")


@pytest.mark.asyncio
async def test_crm_006_commercial_terms_and_credit_check(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "CREDITO VALIDACION SAC", "credit_limit": 5000.00}
        )
        cid = c_res.json()["id"]

        terms_update = await client.patch(
            f"/api/v1/customers/{cid}/commercial-terms",
            headers=admin_headers,
            json={
                "price_list_id": "LISTA_MAYORISTA",
                "payment_terms_days": 45,
                "preferred_currency": "PEN",
                "credit_limit": 10000.00,
                "is_credit_blocked": False
            }
        )
        assert terms_update.status_code == 200
        assert terms_update.json()["payment_terms_days"] == 45

        check_ok = await client.post(
            f"/api/v1/customers/{cid}/credit-check",
            headers=admin_headers,
            json={"amount": 4000.00}
        )
        assert check_ok.status_code == 200
        assert check_ok.json()["allowed"] is True

        check_over = await client.post(
            f"/api/v1/customers/{cid}/credit-check",
            headers=admin_headers,
            json={"amount": 15000.00}
        )
        assert check_over.status_code == 200
        assert check_over.json()["allowed"] is False
        assert check_over.json()["requires_approval"] is True


@pytest.mark.asyncio
async def test_crm_007_assignment_and_reassignment(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "ASIGNACION TEST SAC"}
        )
        cid = c_res.json()["id"]

        rep_id = uuid4()
        assign_res = await client.post(
            f"/api/v1/customers/{cid}/assignment",
            headers=admin_headers,
            json={
                "assigned_sales_rep_id": str(rep_id),
                "sales_team": "Equipo Corporativo",
                "reason": "Asignacion de cartera inicial"
            }
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["assigned_sales_rep_id"] == str(rep_id)

        history_res = await client.get(f"/api/v1/customers/{cid}/assignment", headers=admin_headers)
        assert len(history_res.json()["history"]) == 1


@pytest.mark.asyncio
async def test_crm_008_segmentation_rules(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "SEGMENTACION VIP SAC"}
        )
        cid = UUID(c_res.json()["id"])

        seg_res = await client.post(
            "/api/v1/customers/segments",
            headers=admin_headers,
            json={
                "name": "Clientes VIP Alto Volumen",
                "description": "Mas de 2 compras y 2000 USD",
                "min_frequency": 2,
                "min_spend": 2000.0,
                "max_recency_days": 180
            }
        )
        assert seg_res.status_code == 201

        with sync_session_factory() as session:
            for _ in range(3):
                session.add(SaleModel(
                    id=uuid4(),
                    company_id=COMPANY_A,
                    branch_id=BRANCH_A,
                    customer_id=cid,
                    series="F001",
                    number=uuid4().int % 100000,
                    status="confirmed",
                    currency="USD",
                    subtotal_amount=Decimal("1000.00"),
                    tax_amount=Decimal("180.00"),
                    total_amount=Decimal("1180.00"),
                    paid_amount=Decimal("1180.00")
                ))
            session.commit()

        eval_res = await client.get(f"/api/v1/customers/{cid}/segments", headers=admin_headers)
        assert eval_res.status_code == 200
        data = eval_res.json()
        assert len(data["matched_segments"]) >= 1
        assert data["actual_metrics"]["frequency"] >= 3


@pytest.mark.asyncio
async def test_crm_009_notes_privacy_and_sanitization(admin_headers, seller_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "NOTAS PRIVACIDAD SAC"}
        )
        cid = c_res.json()["id"]

        note_com = await client.post(
            f"/api/v1/customers/{cid}/notes",
            headers=admin_headers,
            json={"category": "comercial", "content": "Nota comercial visible para el equipo"}
        )
        assert note_com.status_code == 201

        note_int = await client.post(
            f"/api/v1/customers/{cid}/notes",
            headers=admin_headers,
            json={"category": "interno", "content": "Comentario confidencial sobre riesgo"}
        )
        assert note_int.status_code == 201

        seller_list = await client.get(f"/api/v1/customers/{cid}/notes", headers=seller_headers)
        assert seller_list.status_code == 200
        seller_categories = [n["category"] for n in seller_list.json()]
        assert "comercial" in seller_categories
        assert "interno" not in seller_categories

        admin_list = await client.get(f"/api/v1/customers/{cid}/notes", headers=admin_headers)
        admin_categories = [n["category"] for n in admin_list.json()]
        assert "interno" in admin_categories


@pytest.mark.asyncio
async def test_crm_010_status_blocking_sales(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "CLIENTE BLOQUEABLE SAC"}
        )
        cid = UUID(c_res.json()["id"])

        block_res = await client.patch(
            f"/api/v1/customers/{cid}/status",
            headers=admin_headers,
            json={"status": "blocked", "reason": "Morosidad prolongada"}
        )
        assert block_res.status_code == 200
        assert block_res.json()["status"] == "blocked"

        prod_sku = f"SKU-{uuid4().hex[:6].upper()}"
        p_res = await client.post(
            "/api/v1/products",
            headers=admin_headers,
            json={
                "sku": prod_sku,
                "name": "Producto Bloqueo",
                "category": "General",
                "unit_price": 500.0,
                "unit_cost": 300.0,
                "tax_rate": 0.18
            }
        )
        pid = UUID(p_res.json()["id"])

        sale_id = uuid4()
        with sync_session_factory() as session:
            s = SaleModel(
                id=sale_id,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=cid,
                warehouse_id=WAREHOUSE_A,
                series="F001",
                number=uuid4().int % 100000,
                status="draft",
                currency="USD",
                subtotal_amount=Decimal("500.00"),
                tax_amount=Decimal("90.00"),
                total_amount=Decimal("590.00"),
                paid_amount=Decimal("0.00")
            )
            session.add(s)
            session.add(SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale_id,
                product_id=pid,
                line_number=1,
                sku_snapshot=prod_sku,
                name_snapshot="Producto Bloqueo",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("1.000000"),
                unit_price_snapshot=Decimal("500.000000"),
                unit_cost_snapshot=Decimal("300.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("500.000000"),
                tax_amount=Decimal("90.000000"),
                total_amount=Decimal("590.000000")
            ))
            session.commit()

        headers_idempotent = {**admin_headers, "Idempotency-Key": str(uuid4())}
        confirm_blocked = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers=headers_idempotent,
            json={"allow_blocked_exception": False}
        )
        assert confirm_blocked.status_code == 409


@pytest.mark.asyncio
async def test_crm_011_import_idempotency(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        batch_key = f"BATCH-{uuid4().hex[:8]}"
        doc1 = f"20{uuid4().int % 1000000000:09d}"
        payload = {
            "import_batch_key": batch_key,
            "dry_run": False,
            "rows": [
                {"code": f"IMP-{doc1[:6]}", "doc_type": "RUC", "doc_number": doc1, "legal_name": "IMPORTADO S.A.C.", "credit_limit": 8000.0}
            ]
        }
        res1 = await client.post("/api/v1/customers/import", headers=admin_headers, json=payload)
        assert res1.status_code == 200
        assert res1.json()["created_count"] == 1

        res2 = await client.post("/api/v1/customers/import", headers=admin_headers, json=payload)
        assert res2.status_code == 200
        assert res2.json()["created_count"] == 1


@pytest.mark.asyncio
async def test_crm_012_export_permissions(admin_headers, seller_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        seller_exp = await client.post(
            "/api/v1/customers/export",
            headers=seller_headers,
            json={"format": "json", "reason": "Reporte diario de visitas", "include_sensitive": True}
        )
        assert seller_exp.status_code == 200
        first_row = seller_exp.json()["data"][0]
        assert first_row["credit_limit"] is None

        admin_exp = await client.post(
            "/api/v1/customers/export",
            headers=admin_headers,
            json={"format": "json", "reason": "Auditoria de saldos", "include_sensitive": True}
        )
        assert admin_exp.status_code == 200


@pytest.mark.asyncio
async def test_crm_013_profile_quality(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "CALIDAD TEST SAC"}
        )
        cid = c_res.json()["id"]

        qual_res = await client.get(f"/api/v1/customers/{cid}/quality", headers=admin_headers)
        assert qual_res.status_code == 200
        data = qual_res.json()
        assert "score_percentage" in data
        assert data["blocking_purchases"] is False


@pytest.mark.asyncio
async def test_crm_014_opportunities_and_quote_conversion(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "OPORTUNIDAD TEST SAC"}
        )
        cid = c_res.json()["id"]

        opp_res = await client.post(
            f"/api/v1/customers/{cid}/opportunities",
            headers=admin_headers,
            json={
                "title": "Renovacion de Servidores Cloud",
                "stage": "qualified",
                "estimated_amount": 15000.0,
                "probability": 70.0
            }
        )
        assert opp_res.status_code == 201
        opp_id = opp_res.json()["id"]

        quote_conv = await client.post(f"/api/v1/crm/opportunities/{opp_id}/convert-to-quote", headers=admin_headers)
        assert quote_conv.status_code == 200
        assert quote_conv.json()["already_converted"] is False

        quote_dup = await client.post(f"/api/v1/crm/opportunities/{opp_id}/convert-to-quote", headers=admin_headers)
        assert quote_dup.status_code == 200
        assert quote_dup.json()["already_converted"] is True


@pytest.mark.asyncio
async def test_crm_015_activities_scheduling(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "ACTIVIDADES TEST SAC"}
        )
        cid = c_res.json()["id"]

        due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        act_res = await client.post(
            f"/api/v1/customers/{cid}/activities",
            headers=admin_headers,
            json={
                "activity_type": "meeting",
                "subject": "Reunion de demostracion Enterprise",
                "due_date": due,
                "reminder_minutes": 30
            }
        )
        assert act_res.status_code == 201
        act_id = act_res.json()["id"]

        cal_res = await client.get("/api/v1/crm/activities?view_mode=calendar", headers=admin_headers)
        assert cal_res.status_code == 200
        assert "events_by_date" in cal_res.json()

        complete_res = await client.patch(
            f"/api/v1/crm/activities/{act_id}",
            headers=admin_headers,
            json={"status": "completed", "outcome": "Cliente satisfecho con la demo"}
        )
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_crm_016_loyalty_ledger_and_reversal(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "PUNTOS FIDELIDAD SAC"}
        )
        cid = c_res.json()["id"]

        accrue_res = await client.post(
            f"/api/v1/customers/{cid}/loyalty/accrue",
            headers=admin_headers,
            json={"points": 1200, "reference_type": "sale", "reference_id": "V-001"}
        )
        assert accrue_res.status_code == 201
        assert accrue_res.json()["new_balance"] == 1200

        rev1 = await client.post(
            f"/api/v1/customers/{cid}/loyalty/reverse",
            headers=admin_headers,
            json={"points": 500, "reference_id": "REF-001"}
        )
        assert rev1.status_code == 200
        assert rev1.json()["new_balance"] == 700

        rev2_idempotent = await client.post(
            f"/api/v1/customers/{cid}/loyalty/reverse",
            headers=admin_headers,
            json={"points": 500, "reference_id": "REF-001"}
        )
        assert rev2_idempotent.status_code == 200
        assert rev2_idempotent.json()["status"] == "already_reversed"
        assert rev2_idempotent.json()["new_balance"] == 700


@pytest.mark.asyncio
async def test_crm_017_customer_portal_isolation(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc = f"20{uuid4().int % 1000000000:09d}"
        portal_email = f"portal_{uuid4().hex[:6]}@cliente.com"
        c_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"C-{doc[:6]}", "doc_type": "RUC", "doc_number": doc, "legal_name": "PORTAL CLIENTE SAC", "email": portal_email}
        )
        cid = UUID(c_res.json()["id"])

        with sync_session_factory() as session:
            session.add(SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=cid,
                series="F001",
                number=uuid4().int % 100000,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("800.00"),
                tax_amount=Decimal("144.00"),
                total_amount=Decimal("944.00"),
                paid_amount=Decimal("944.00")
            ))
            session.commit()

        portal_identity = create_durable_identity(
            company_id=COMPANY_A,
            user_id=USER_PORTAL_A,
            role="customer_portal",
            email=portal_email
        )
        portal_headers = portal_identity["headers"]

        my_profile = await client.get("/api/v1/customer-portal/me", headers=portal_headers)
        assert my_profile.status_code == 200
        assert my_profile.json()["legal_name"] == "PORTAL CLIENTE SAC"

        my_invoices = await client.get("/api/v1/customer-portal/invoices", headers=portal_headers)
        assert my_invoices.status_code == 200
        assert len(my_invoices.json()) == 1


@pytest.mark.asyncio
async def test_api_017_to_023_contracts_and_isolation(admin_headers, company_b_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc_a = f"20{uuid4().int % 1000000000:09d}"
        ca_res = await client.post(
            "/api/v1/customers",
            headers=admin_headers,
            json={"code": f"CA-{doc_a[:6]}", "doc_type": "RUC", "doc_number": doc_a, "legal_name": "TENANT A CUSTOMER SAC"}
        )
        assert ca_res.status_code == 201
        ca_id = ca_res.json()["id"]

        list_b = await client.get("/api/v1/customers", headers=company_b_headers)
        assert list_b.status_code == 200
        b_ids = [c["id"] for c in list_b.json()["items"]]
        assert ca_id not in b_ids

        get_cross = await client.get(f"/api/v1/customers/{ca_id}", headers=company_b_headers)
        assert get_cross.status_code == 404

        patch_res = await client.patch(
            f"/api/v1/customers/{ca_id}",
            headers=admin_headers,
            json={"legal_name": "TENANT A ACTUALIZADO", "version": 1}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["version"] == 2

        patch_conflict = await client.patch(
            f"/api/v1/customers/{ca_id}",
            headers=admin_headers,
            json={"legal_name": "CONFLICTO CONCURRENTE", "version": 1}
        )
        assert patch_conflict.status_code == 409

        arch_res = await client.post(f"/api/v1/customers/{ca_id}/archive", headers=admin_headers)
        assert arch_res.status_code == 200
        assert arch_res.json()["is_active"] is False

        rest_res = await client.post(f"/api/v1/customers/{ca_id}/restore", headers=admin_headers)
        assert rest_res.status_code == 200
        assert rest_res.json()["is_active"] is True
