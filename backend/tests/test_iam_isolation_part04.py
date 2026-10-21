from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory, sync_engine, Base
Base.metadata.create_all(sync_engine)
from salesia.shared.infrastructure.models import (
    CompanyModel,
    UserModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    InventoryStockModel,
    PaymentModel,
    OrderModel,
    JobModel
)
from salesia.modules.seguridad.infrastructure.models import (
    AuthSession,
    CustomRole,
    SupportGrant
)
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.seguridad.infrastructure.sessions import token_pair, fingerprint, utcnow
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative


def create_test_identity(db, company_id=None, role="company_admin", permissions=None, email=None):
    if company_id is None:
        comp = CompanyModel(
            id=uuid4(),
            tax_id=uuid4().hex[:11],
            legal_name="Empresa Test " + uuid4().hex[:6],
            trade_name="Test Trade",
            base_currency="USD",
            is_active=True
        )
        db.add(comp)
        db.flush()
        company_id = comp.id
    else:
        comp = db.get(CompanyModel, company_id)

    u_email = email or f"user_{uuid4().hex[:8]}@test.enterprise"
    pwd = "SuperSecretSecurePassword2026!"
    user = UserModel(
        id=uuid4(),
        company_id=company_id,
        email=u_email,
        hashed_password=hash_password(pwd),
        role=role,
        is_active=True
    )
    db.add(user)
    db.flush()

    if permissions is not None and role.startswith("custom_"):
        import json
        crole = CustomRole(
            company_id=company_id,
            role_key=role,
            title="Custom Test Role",
            description="Role for tests",
            permissions_json=json.dumps(permissions)
        )
        db.add(crole)
        db.flush()

    now = utcnow()
    session = AuthSession(
        user_id=user.id,
        company_id=company_id,
        refresh_hash=fingerprint(secrets.token_urlsafe(48)),
        created_at=now,
        expires_at=now + timedelta(days=7),
        user_agent="pytest-runner",
        ip_address="127.0.0.1"
    )
    db.add(session)
    db.flush()

    pair = token_pair(db, user, session)
    session.refresh_hash = fingerprint(pair["refresh_token"])
    db.commit()

    return {
        "company_id": company_id,
        "user_id": user.id,
        "email": u_email,
        "password": pwd,
        "token": pair["access_token"],
        "headers": {"Authorization": f"Bearer {pair['access_token']}"}
    }


def seed_company_fixtures(db, company_id):
    branch = BranchModel(
        id=uuid4(),
        company_id=company_id,
        code="BR-" + uuid4().hex[:4],
        name="Sucursal Principal",
        timezone="America/Lima",
        is_active=True
    )
    db.add(branch)
    db.flush()

    wh = WarehouseModel(
        id=uuid4(),
        company_id=company_id,
        branch_id=branch.id,
        code="WH-" + uuid4().hex[:4],
        name="Almacen Central",
        is_active=True
    )
    db.add(wh)
    db.flush()

    cust = CustomerModel(
        id=uuid4(),
        company_id=company_id,
        code="CLI-" + uuid4().hex[:4],
        doc_type="RUC",
        doc_number="20" + uuid4().hex[:9],
        legal_name="Cliente Corp " + uuid4().hex[:4],
        credit_limit=Decimal("50000.00"),
        current_balance=Decimal("0.00"),
        is_active=True
    )
    db.add(cust)
    db.flush()

    prod = ProductModel(
        id=uuid4(),
        company_id=company_id,
        sku="SKU-" + uuid4().hex[:6],
        name="Laptop Test " + uuid4().hex[:4],
        category="Computo",
        unit_of_measure="NIU",
        unit_price=Decimal("1000.00"),
        unit_cost=Decimal("600.00"),
        tax_rate=Decimal("0.18"),
        is_active=True
    )
    db.add(prod)
    db.flush()

    stock = InventoryStockModel(
        id=uuid4(),
        company_id=company_id,
        warehouse_id=wh.id,
        product_id=prod.id,
        physical_quantity=Decimal("100.00"),
        reserved_quantity=Decimal("0.00")
    )
    db.add(stock)
    db.commit()

    return {
        "branch_id": branch.id,
        "warehouse_id": wh.id,
        "customer_id": cust.id,
        "product_id": prod.id,
        "sku": prod.sku
    }


@pytest.mark.asyncio
async def test_reproduced_failure_01_create_sale_without_session_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sales/draft",
            headers={"Idempotency-Key": uuid4().hex},
            json={
                "company_id": str(uuid4()),
                "branch_id": str(uuid4()),
                "customer_id": str(uuid4()),
                "warehouse_id": str(uuid4()),
                "currency": "USD",
                "lines": [
                    {
                        "sku": "SKU-ANON",
                        "product_name": "Producto Anonimo",
                        "quantity": 1,
                        "unit_price": "100.00"
                    }
                ]
            }
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_reproduced_failure_02_read_sale_from_another_company_returns_403():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_a["company_id"])
        id_b = create_test_identity(db, role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/sales/draft",
            headers={**id_a["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(fix_a["product_id"]),
                        "sku": fix_a["sku"],
                        "product_name": "Producto A",
                        "quantity": 2,
                        "unit_price": "1000.00"
                    }
                ]
            }
        )
        assert create_res.status_code == 201
        sale_a_id = create_res.json()["sale_id"]

        read_res = await client.get(
            f"/api/v1/sales/{sale_a_id}",
            headers=id_b["headers"]
        )
        assert read_res.status_code == 403


@pytest.mark.asyncio
async def test_fal005_cross_company_mutations_and_resources_all_return_403():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_a["company_id"])
        id_b = create_test_identity(db, role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/sales/draft",
            headers={**id_a["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(fix_a["product_id"]),
                        "sku": fix_a["sku"],
                        "product_name": "Producto A",
                        "quantity": 1,
                        "unit_price": "1000.00"
                    }
                ]
            }
        )
        assert create_res.status_code == 201
        sale_a_id = create_res.json()["sale_id"]

        conf_cross = await client.post(
            f"/api/v1/sales/{sale_a_id}/confirm",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert conf_cross.status_code == 403

        annul_cross = await client.post(
            f"/api/v1/sales/{sale_a_id}/annul",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex},
            json={"reason": "Intento anulacion indebida"}
        )
        assert annul_cross.status_code == 403

        clone_cross = await client.post(
            f"/api/v1/sales/{sale_a_id}/clone",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert clone_cross.status_code == 403

        patch_cross = await client.patch(
            f"/api/v1/sales/{sale_a_id}",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "version": 1,
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(fix_a["product_id"]),
                        "sku": fix_a["sku"],
                        "product_name": "Producto A",
                        "quantity": 1,
                        "unit_price": "1000.00"
                    }
                ]
            }
        )
        assert patch_cross.status_code == 403

        with sync_session_factory() as db:
            pay = PaymentModel(
                id=uuid4(),
                company_id=id_a["company_id"],
                sale_id=UUID(sale_a_id),
                payment_method="CASH",
                amount=Decimal("100.00"),
                currency="USD",
                status="confirmed"
            )
            db.add(pay)
            job = JobModel(
                id=uuid4(),
                company_id=id_a["company_id"],
                requested_by=id_a["user_id"],
                job_type="export",
                status="pending",
                progress=0
            )
            db.add(job)
            db.commit()
            pay_id = pay.id
            job_id = job.id

        ref_cross = await client.post(
            "/api/v1/refunds",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex},
            json={"payment_id": str(pay_id), "reason": "Reembolso indebido"}
        )
        assert ref_cross.status_code == 403

        job_get_cross = await client.get(
            f"/api/v1/jobs/{job_id}",
            headers=id_b["headers"]
        )
        assert job_get_cross.status_code == 403

        job_cancel_cross = await client.post(
            f"/api/v1/jobs/{job_id}/cancel",
            headers=id_b["headers"]
        )
        assert job_cancel_cross.status_code == 403

        nonexistent_uuid = uuid4()
        not_found_sale = await client.get(
            f"/api/v1/sales/{nonexistent_uuid}",
            headers=id_a["headers"]
        )
        assert not_found_sale.status_code == 404

        not_found_job = await client.get(
            f"/api/v1/jobs/{nonexistent_uuid}",
            headers=id_a["headers"]
        )
        assert not_found_job.status_code == 404


@pytest.mark.asyncio
async def test_reg_04_anonymous_mutations_401_no_permission_403_other_company_403():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_a["company_id"])
        id_analyst = create_test_identity(db, company_id=id_a["company_id"], role="analyst")
        id_b = create_test_identity(db, role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        anon_sale = await client.post(
            "/api/v1/sales/draft",
            headers={"Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "lines": [{"sku": fix_a["sku"], "product_name": "P", "quantity": 1, "unit_price": "10"}]
            }
        )
        assert anon_sale.status_code == 401

        analyst_sale = await client.post(
            "/api/v1/sales/draft",
            headers={**id_analyst["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "lines": [{"sku": fix_a["sku"], "product_name": "P", "quantity": 1, "unit_price": "10"}]
            }
        )
        assert analyst_sale.status_code == 403

        cross_company_sale = await client.post(
            "/api/v1/sales/draft",
            headers={**id_b["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "company_id": str(id_a["company_id"]),
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "lines": [{"sku": fix_a["sku"], "product_name": "P", "quantity": 1, "unit_price": "10"}]
            }
        )
        assert cross_company_sale.status_code in (403, 422)


@pytest.mark.asyncio
async def test_iam_001_granular_permissions_catalog():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_a["company_id"])
        id_reader = create_test_identity(
            db,
            company_id=id_a["company_id"],
            role="custom_reader_" + uuid4().hex[:6],
            permissions=["sales:read"]
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/sales/draft",
            headers={**id_a["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix_a["branch_id"]),
                "customer_id": str(fix_a["customer_id"]),
                "warehouse_id": str(fix_a["warehouse_id"]),
                "currency": "USD",
                "lines": [
                    {
                        "product_id": str(fix_a["product_id"]),
                        "sku": fix_a["sku"],
                        "product_name": "P",
                        "quantity": 1,
                        "unit_price": "100.00"
                    }
                ]
            }
        )
        assert create_res.status_code == 201
        sale_id = create_res.json()["sale_id"]

        read_res = await client.get(
            f"/api/v1/sales/{sale_id}",
            headers=id_reader["headers"]
        )
        assert read_res.status_code == 200

        cancel_res = await client.post(
            f"/api/v1/sales/{sale_id}/annul",
            headers={**id_reader["headers"], "Idempotency-Key": uuid4().hex},
            json={"reason": "Cancelacion no autorizada"}
        )
        assert cancel_res.status_code == 403

        export_res = await client.get(
            "/api/v1/sales/export",
            headers=id_reader["headers"]
        )
        assert export_res.status_code == 403


@pytest.mark.asyncio
async def test_iam_002_deny_by_default_server_side():
    with sync_session_factory() as db:
        id_empty = create_test_identity(
            db,
            role="custom_empty_" + uuid4().hex[:6],
            permissions=[]
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ["/api/v1/customers", "/api/v1/products", "/api/v1/sales", "/api/v1/users", "/api/v1/operations/metrics"]:
            res = await client.get(path, headers=id_empty["headers"])
            assert res.status_code == 403


@pytest.mark.asyncio
async def test_iam_003_membership_scope_and_tampered_headers():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        id_b = create_test_identity(db, role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tampered_headers = {
            **id_a["headers"],
            "X-Company-ID": str(id_b["company_id"])
        }
        res = await client.get("/api/v1/customers", headers=tampered_headers)
        assert res.status_code == 200
        me = await client.get("/api/v1/auth/me", headers=tampered_headers)
        assert me.status_code == 200
        assert me.json()["company_id"] == str(id_a["company_id"])


@pytest.mark.asyncio
async def test_iam_004_field_level_permissions_masking():
    with sync_session_factory() as db:
        id_a = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_a["company_id"])
        id_nocost = create_test_identity(
            db,
            company_id=id_a["company_id"],
            role="custom_nocost_" + uuid4().hex[:6],
            permissions=["products:read"]
        )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        admin_prod = await client.get(
            f"/api/v1/products/{fix_a['product_id']}",
            headers=id_a["headers"]
        )
        assert admin_prod.status_code == 200
        admin_data = admin_prod.json()
        assert "unit_cost" in admin_data and admin_data["unit_cost"] is not None

        nocost_prod = await client.get(
            f"/api/v1/products/{fix_a['product_id']}",
            headers=id_nocost["headers"]
        )
        assert nocost_prod.status_code == 200
        nocost_data = nocost_prod.json()
        assert "unit_cost" not in nocost_data or nocost_data["unit_cost"] is None
        assert "margin_amount" not in nocost_data or nocost_data["margin_amount"] is None


@pytest.mark.asyncio
async def test_iam_005_record_level_permissions_salesperson_isolation():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        fix = seed_company_fixtures(db, id_admin["company_id"])
        id_rep1 = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")
        id_rep2 = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")

        rep1 = SalesRepresentative(
            company_id=id_admin["company_id"],
            user_id=id_rep1["user_id"],
            full_name="Vendedor Uno",
            territory="Norte",
            monthly_quota=Decimal("10000.00"),
            is_active=True
        )
        rep2 = SalesRepresentative(
            company_id=id_admin["company_id"],
            user_id=id_rep2["user_id"],
            full_name="Vendedor Dos",
            territory="Sur",
            monthly_quota=Decimal("10000.00"),
            is_active=True
        )
        db.add_all([rep1, rep2])
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sale1_res = await client.post(
            "/api/v1/sales/draft",
            headers={**id_rep1["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(fix["branch_id"]),
                "customer_id": str(fix["customer_id"]),
                "warehouse_id": str(fix["warehouse_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(fix["product_id"]), "sku": fix["sku"], "product_name": "P", "quantity": 1, "unit_price": "100.00"}]
            }
        )
        assert sale1_res.status_code == 201
        sale1_id = sale1_res.json()["sale_id"]

        rep2_view = await client.get(
            f"/api/v1/sales/{sale1_id}",
            headers=id_rep2["headers"]
        )
        assert rep2_view.status_code == 403

        rep2_list = await client.get(
            "/api/v1/sales",
            headers=id_rep2["headers"]
        )
        assert rep2_list.status_code == 200
        assert not any(s["sale_id"] == sale1_id for s in rep2_list.json()["items"])


@pytest.mark.asyncio
async def test_iam_006_segregation_of_duties_requester_cannot_approve():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        fix = seed_company_fixtures(db, id_admin["company_id"])
        id_creator = create_test_identity(db, company_id=id_admin["company_id"], role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        order_res = await client.post(
            "/api/v1/orders",
            headers={**id_creator["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(fix["customer_id"]),
                "branch_id": str(fix["branch_id"]),
                "warehouse_id": str(fix["warehouse_id"]),
                "lines": [
                    {
                        "product_id": str(fix["product_id"]),
                        "sku": fix["sku"],
                        "name": "P",
                        "quantity": 1,
                        "unit_price": "100.00",
                        "discount_pct": "20.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert order_res.status_code == 201
        order_id = order_res.json()["order_id"]
        assert order_res.json()["status"] == "pending_approval"

        self_approve = await client.post(
            f"/api/v1/orders/{order_id}/approve",
            headers={**id_creator["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert self_approve.status_code == 403

        other_approve = await client.post(
            f"/api/v1/orders/{order_id}/approve",
            headers={**id_admin["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert other_approve.status_code == 200
        assert other_approve.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_iam_007_economic_limits_cumulative_splits_cannot_evade():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        fix = seed_company_fixtures(db, id_admin["company_id"])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        order1 = await client.post(
            "/api/v1/orders",
            headers={**id_admin["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(fix["customer_id"]),
                "branch_id": str(fix["branch_id"]),
                "warehouse_id": str(fix["warehouse_id"]),
                "lines": [
                    {
                        "product_id": str(fix["product_id"]),
                        "sku": fix["sku"],
                        "name": "P",
                        "quantity": 12,
                        "unit_price": "1000.00",
                        "discount_pct": "5.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert order1.status_code == 201

        order2 = await client.post(
            "/api/v1/orders",
            headers={**id_admin["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "customer_id": str(fix["customer_id"]),
                "branch_id": str(fix["branch_id"]),
                "warehouse_id": str(fix["warehouse_id"]),
                "lines": [
                    {
                        "product_id": str(fix["product_id"]),
                        "sku": fix["sku"],
                        "name": "P",
                        "quantity": 15,
                        "unit_price": "1000.00",
                        "discount_pct": "5.00",
                        "tax_rate": "0.18"
                    }
                ]
            }
        )
        assert order2.status_code == 201
        assert order2.json()["requires_approval"] is True


@pytest.mark.asyncio
async def test_iam_008_immediate_role_changes_and_job_cancellation():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_victim = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")
        job = JobModel(
            id=uuid4(),
            company_id=id_admin["company_id"],
            requested_by=id_victim["user_id"],
            job_type="export",
            status="running",
            progress=50
        )
        db.add(job)
        db.commit()
        job_id = job.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        active_me = await client.get("/api/v1/auth/me", headers=id_victim["headers"])
        assert active_me.status_code == 200

        deact_res = await client.patch(
            f"/api/v1/memberships/{id_victim['user_id']}",
            headers=id_admin["headers"],
            json={"is_active": False}
        )
        assert deact_res.status_code == 200

        revoked_me = await client.get("/api/v1/auth/me", headers=id_victim["headers"])
        assert revoked_me.status_code == 401

        with sync_session_factory() as db:
            cancelled_job = db.get(JobModel, job_id)
            assert cancelled_job.status == "cancelled"


@pytest.mark.asyncio
async def test_iam_009_role_templates_cloning_and_comparison_no_privilege_escalation():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_seller = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        roles_res = await client.get("/api/v1/roles", headers=id_admin["headers"])
        assert roles_res.status_code == 200
        roles_data = roles_res.json()
        assert len(roles_data["roles"]) >= 5
        assert all("is_custom" in role for role in roles_data["roles"])
        assert all(role["is_custom"] is False for role in roles_data["roles"])

        comp_res = await client.get(
            "/api/v1/roles/compare?source=salesperson&target=manager",
            headers=id_admin["headers"]
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert "added_permissions" in comp_data

        unique_key = "cloned_rep_" + uuid4().hex[:6]
        clone_res = await client.post(
            "/api/v1/roles/salesperson/clone",
            headers=id_admin["headers"],
            json={
                "role_key": unique_key,
                "title": "Vendedor Especial",
                "description": "Vendedor clonado con permiso extra",
                "additional_permissions": ["customers:write"]
            }
        )
        assert clone_res.status_code == 201
        assert clone_res.json()["role"] == unique_key

        updated_roles_res = await client.get("/api/v1/roles", headers=id_admin["headers"])
        assert updated_roles_res.status_code == 200
        cloned_role = next(role for role in updated_roles_res.json()["roles"] if role["role"] == unique_key)
        assert cloned_role["is_custom"] is True

        escalate_res = await client.post(
            "/api/v1/roles",
            headers=id_admin["headers"],
            json={
                "role_key": "escalated_role_" + uuid4().hex[:6],
                "title": "Escalated",
                "permissions": ["platform:manage"]
            }
        )
        assert escalate_res.status_code == 403


@pytest.mark.asyncio
async def test_iam_010_last_admin_protection_and_transfer():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_member = create_test_identity(db, company_id=id_admin["company_id"], role="cashier")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        demote_fail = await client.patch(
            f"/api/v1/memberships/{id_admin['user_id']}",
            headers=id_admin["headers"],
            json={"role": "cashier"}
        )
        assert demote_fail.status_code == 409

        transfer_res = await client.post(
            f"/api/v1/memberships/{id_member['user_id']}/transfer-admin",
            headers=id_admin["headers"]
        )
        assert transfer_res.status_code == 200
        assert transfer_res.json()["new_admin_id"] == str(id_member["user_id"])

        with sync_session_factory() as db:
            u_old = db.get(UserModel, id_admin["user_id"])
            u_new = db.get(UserModel, id_member["user_id"])
            assert u_new.role == "company_admin"
            assert u_old.role != "company_admin"


@pytest.mark.asyncio
async def test_iam_011_temporary_support_sessions_lifecycle():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        grant_res = await client.post(
            "/api/v1/auth/support/grants",
            headers=id_admin["headers"],
            json={
                "reason": "Auditoria de soporte tecnico ticket 90210",
                "scope": "diagnostics",
                "duration_minutes": 60
            }
        )
        assert grant_res.status_code == 201
        grant_data = grant_res.json()
        assert "token" in grant_data
        assert grant_data["scope"] == "diagnostics"
        grant_id = grant_data["grant_id"]

        support_headers = {"Authorization": f"Bearer {grant_data['token']}"}
        me_support = await client.get("/api/v1/auth/me", headers=support_headers)
        assert me_support.status_code == 200
        assert me_support.json().get("is_support_session") is True

        list_grants = await client.get("/api/v1/auth/support/grants", headers=id_admin["headers"])
        assert list_grants.status_code == 200
        assert any(g["grant_id"] == grant_id for g in list_grants.json()["items"])

        revoke_res = await client.post(
            f"/api/v1/auth/support/grants/{grant_id}/revoke",
            headers=id_admin["headers"]
        )
        assert revoke_res.status_code == 200

        expired_access = await client.get("/api/v1/auth/me", headers=support_headers)
        assert expired_access.status_code == 401


@pytest.mark.asyncio
async def test_iam_012_test_matrix_roles_states_cross_company():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_sales = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")
        id_cashier = create_test_identity(db, company_id=id_admin["company_id"], role="cashier")
        id_warehouse = create_test_identity(db, company_id=id_admin["company_id"], role="warehouse")
        id_b = create_test_identity(db, role="company_admin")
        fix_a = seed_company_fixtures(db, id_admin["company_id"])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.post(
            "/api/v1/inventory/adjustments",
            headers={**id_warehouse["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "warehouse_id": str(fix_a["warehouse_id"]),
                "product_id": str(fix_a["product_id"]),
                "quantity_delta": 5,
                "unit_cost": "600.00",
                "reason": "Lote inicial"
            }
        )
        assert res1.status_code in (200, 201)

        res2 = await client.post(
            "/api/v1/inventory/adjustments",
            headers={**id_cashier["headers"], "Idempotency-Key": uuid4().hex},
            json={
                "warehouse_id": str(fix_a["warehouse_id"]),
                "product_id": str(fix_a["product_id"]),
                "quantity_delta": 5,
                "unit_cost": "600.00",
                "reason": "Lote no permitido"
            }
        )
        assert res2.status_code == 403


@pytest.mark.asyncio
async def test_api_008_post_memberships_invitations():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_sales = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")
        id_b = create_test_identity(db, role="company_admin")
        fix_b = seed_company_fixtures(db, id_b["company_id"])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ok_invite = await client.post(
            "/api/v1/memberships/invitations",
            headers=id_admin["headers"],
            json={"email": f"new_{uuid4().hex[:6]}@empresa.com", "role": "salesperson"}
        )
        assert ok_invite.status_code == 201
        assert ok_invite.json()["status"] == "pending"

        inv_role = await client.post(
            "/api/v1/memberships/invitations",
            headers=id_admin["headers"],
            json={"email": f"bad_{uuid4().hex[:6]}@empresa.com", "role": "non_existent_role_xyz"}
        )
        assert inv_role.status_code == 422

        unauth = await client.post(
            "/api/v1/memberships/invitations",
            headers=id_sales["headers"],
            json={"email": f"sales_{uuid4().hex[:6]}@empresa.com", "role": "salesperson"}
        )
        assert unauth.status_code == 403

        cross_branch = await client.post(
            "/api/v1/memberships/invitations",
            headers=id_admin["headers"],
            json={
                "email": f"cross_{uuid4().hex[:6]}@empresa.com",
                "role": "salesperson",
                "branch_id": str(fix_b["branch_id"])
            }
        )
        assert cross_branch.status_code in (403, 422)


@pytest.mark.asyncio
async def test_api_009_get_users():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_sales = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_ok = await client.get("/api/v1/users?page=1&page_size=10", headers=id_admin["headers"])
        assert list_ok.status_code == 200
        data = list_ok.json()
        users = data["items"] if isinstance(data, dict) and "items" in data else data
        assert len(users) >= 2

        unauth = await client.get("/api/v1/users", headers=id_sales["headers"])
        assert unauth.status_code == 403

        bad_page = await client.get("/api/v1/users?page=0", headers=id_admin["headers"])
        assert bad_page.status_code == 422


@pytest.mark.asyncio
async def test_api_010_patch_memberships_id():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_sales = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")
        id_b = create_test_identity(db, role="company_admin")
        id_sales_b = create_test_identity(db, company_id=id_b["company_id"], role="salesperson")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        patch_ok = await client.patch(
            f"/api/v1/memberships/{id_sales['user_id']}",
            headers=id_admin["headers"],
            json={"role": "manager"}
        )
        assert patch_ok.status_code == 200
        assert patch_ok.json()["role"] == "manager"

        patch_bad_role = await client.patch(
            f"/api/v1/memberships/{id_sales['user_id']}",
            headers=id_admin["headers"],
            json={"role": "invalid_unknown_role"}
        )
        assert patch_bad_role.status_code == 422

        patch_cross = await client.patch(
            f"/api/v1/memberships/{id_sales_b['user_id']}",
            headers=id_admin["headers"],
            json={"role": "manager"}
        )
        assert patch_cross.status_code == 403

        patch_last_admin = await client.patch(
            f"/api/v1/memberships/{id_admin['user_id']}",
            headers=id_admin["headers"],
            json={"is_active": False}
        )
        assert patch_last_admin.status_code == 409


@pytest.mark.asyncio
async def test_api_011_get_roles():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_b = create_test_identity(db, role="company_admin")
        crole_b = CustomRole(
            company_id=id_b["company_id"],
            role_key="b_secret_role_" + uuid4().hex[:6],
            title="B Secret Role",
            description="Role of Company B",
            permissions_json='["sales:read"]'
        )
        db.add(crole_b)
        db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/roles", headers=id_admin["headers"])
        assert res.status_code == 200
        data = res.json()
        assert "roles" in data
        assert not any(r["role"] == crole_b.role_key for r in data["roles"])


@pytest.mark.asyncio
async def test_api_012_post_roles():
    with sync_session_factory() as db:
        id_admin = create_test_identity(db, role="company_admin")
        id_sales = create_test_identity(db, company_id=id_admin["company_id"], role="salesperson")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        key = "valid_role_" + uuid4().hex[:6]
        res_ok = await client.post(
            "/api/v1/roles",
            headers=id_admin["headers"],
            json={
                "role_key": key,
                "title": "Nuevo Rol Valido",
                "description": "Descripcion de prueba",
                "permissions": ["sales:read", "customers:read"]
            }
        )
        assert res_ok.status_code == 201
        assert res_ok.json()["role"] == key

        escalate = await client.post(
            "/api/v1/roles",
            headers=id_admin["headers"],
            json={
                "role_key": "escalate_" + uuid4().hex[:6],
                "title": "Escalar Permisos",
                "permissions": ["platform:manage"]
            }
        )
        assert escalate.status_code == 403

        dup = await client.post(
            "/api/v1/roles",
            headers=id_admin["headers"],
            json={
                "role_key": key,
                "title": "Duplicado",
                "permissions": ["sales:read"]
            }
        )
        assert dup.status_code == 409

        duplicate_title = await client.post(
            "/api/v1/roles",
            headers=id_admin["headers"],
            json={
                "role_key": "duplicate_title_" + uuid4().hex[:6],
                "title": "  nuevo rol valido  ",
                "permissions": ["sales:read"]
            }
        )
        assert duplicate_title.status_code == 409

        unauth = await client.post(
            "/api/v1/roles",
            headers=id_sales["headers"],
            json={
                "role_key": "unauth_" + uuid4().hex[:6],
                "title": "Sin Permiso",
                "permissions": ["sales:read"]
            }
        )
        assert unauth.status_code == 403
