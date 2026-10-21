import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    WarehouseModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    PaymentModel,
    InventoryStockModel,
    UserModel,
    QuotationModel,
    OrderModel
)
from salesia.modules.operaciones.infrastructure_models import (
    SalesRepresentative,
    SalesTarget,
    CommissionSettlement,
    Notification
)
from salesia.modules.clientes.infrastructure.models import (
    CustomerProfileModel,
    CustomerOpportunityModel,
    CustomerActivityModel
)
from salesia.shared.infrastructure.transactions import RefundModel
from tests.support.auth_helpers import create_durable_identity, ensure_business_records

COMPANY_A = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000009")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000002")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000004")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000003")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000005")
USER_SUPERVISOR_A = UUID("00000000-0000-0000-0000-000000000006")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000008")


@pytest.fixture(autouse=True, scope="module")
def setup_part09_data():
    with sync_session_factory() as session:
        for cid, tax, name in [(COMPANY_A, "20999999991", "Empresa A P09"), (COMPANY_B, "20999999992", "Empresa B P09")]:
            comp = session.execute(select(CompanyModel).where(CompanyModel.id == cid)).scalar_one_or_none()
            if not comp:
                session.add(CompanyModel(
                    id=cid,
                    tax_id=tax,
                    legal_name=name,
                    trade_name=name,
                    base_currency="USD",
                    is_active=True
                ))
        session.flush()
        branch = session.execute(select(BranchModel).where(BranchModel.id == BRANCH_A)).scalar_one_or_none()
        if not branch:
            session.add(BranchModel(
                id=BRANCH_A,
                company_id=COMPANY_A,
                code="BR-P09-01",
                name="Sucursal Principal P09",
                timezone="America/Lima",
                is_active=True
            ))
        wh = session.execute(select(WarehouseModel).where(WarehouseModel.id == WAREHOUSE_A)).scalar_one_or_none()
        if not wh:
            session.add(WarehouseModel(
                id=WAREHOUSE_A,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                code="WH-P09-01",
                name="Almacen Central P09",
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
        email="admin_p09@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def approver_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        role="company_admin",
        email=f"approver_{uuid4().hex[:8]}@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def seller_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        user_id=USER_SELLER_A,
        role="salesperson",
        email="seller_p09@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def supervisor_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        user_id=USER_SUPERVISOR_A,
        role="manager",
        email="supervisor_p09@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def admin_b_headers():
    identity = create_durable_identity(
        company_id=COMPANY_B,
        user_id=USER_ADMIN_B,
        role="company_admin",
        email="admin_b_p09@salesia.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def test_setup():
    with sync_session_factory() as session:
        cust = CustomerModel(
            id=uuid4(),
            company_id=COMPANY_A,
            code=f"CLI-P09-{uuid4().hex[:6]}",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 1000000000:09d}",
            legal_name="Cliente Test P09",
            credit_limit=Decimal("50000"),
            current_balance=Decimal("0")
        )
        session.add(cust)
        session.flush()

        prod = session.scalar(select(ProductModel).where(ProductModel.company_id == COMPANY_A, ProductModel.sku == "PROD-P09-01"))
        if not prod:
            prod = ProductModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sku="PROD-P09-01",
                name="Producto P09",
                category="General",
                unit_of_measure="NIU",
                unit_price=Decimal("150.00"),
                unit_cost=Decimal("70.00"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(prod)
            session.flush()

        stock = session.scalar(select(InventoryStockModel).where(
            InventoryStockModel.company_id == COMPANY_A,
            InventoryStockModel.warehouse_id == WAREHOUSE_A,
            InventoryStockModel.product_id == prod.id
        ))
        if not stock:
            stock = InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A,
                product_id=prod.id,
                physical_quantity=Decimal("1000"),
                reserved_quantity=Decimal("0"),
                average_cost=Decimal("70.00")
            )
            session.add(stock)
            session.flush()
        else:
            stock.physical_quantity = Decimal("1000")
            stock.reserved_quantity = Decimal("0")
            session.flush()

        session.commit()
        return {
            "customer_id": cust.id,
            "product_id": prod.id,
            "branch_id": BRANCH_A,
            "warehouse_id": WAREHOUSE_A,
            "company_id": COMPANY_A
        }


@pytest.mark.asyncio
async def test_reproduced_bug_confirm_nonexistent_order_returns_404(admin_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/orders/{uuid4()}/confirm",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert res.status_code == 404
        assert res.json().get("detail") == "Pedido no encontrado."


@pytest.mark.asyncio
async def test_ven_001_employee_record_and_historical_attribution(admin_headers, supervisor_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        code_rep = f"REP-{uuid4().hex[:6]}"
        create_res = await client.post(
            "/api/v1/sales/reps",
            json={
                "code": code_rep,
                "full_name": "Vendedor Alfa",
                "branch_id": str(test_setup["branch_id"]),
                "team": "Equipo-Norte",
                "supervisor_id": str(USER_SUPERVISOR_A),
                "territory": "Lima Norte",
                "monthly_quota": "5000"
            },
            headers=admin_headers
        )
        assert create_res.status_code == 201, create_res.text
        data = create_res.json()
        assert data["code"] == code_rep
        assert data["full_name"] == "Vendedor Alfa"
        assert data["team"] == "Equipo-Norte"
        assert data["is_active"] is True
        rep_id = data["rep_id"]

        get_res = await client.get(f"/api/v1/sales/reps/{rep_id}", headers=admin_headers)
        assert get_res.status_code == 200
        assert get_res.json()["code"] == code_rep

        with sync_session_factory() as session:
            sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=101,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("300"),
                tax_amount=Decimal("54"),
                total_amount=Decimal("354"),
                paid_amount=Decimal("354"),
                confirmed_at=datetime.now(timezone.utc)
            )
            session.add(sale)
            session.commit()
            sale_id = sale.id

        deact_res = await client.patch(
            f"/api/v1/sales/reps/{rep_id}",
            json={"is_active": False},
            headers=admin_headers
        )
        assert deact_res.status_code == 200
        assert deact_res.json()["is_active"] is False

        with sync_session_factory() as session:
            persisted_sale = session.get(SaleModel, sale_id)
            assert persisted_sale.sales_rep_id == UUID(rep_id)


@pytest.mark.asyncio
async def test_ven_002_period_assignment_and_retroactive_isolation(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        code_rep = f"REP-{uuid4().hex[:6]}"
        create_res = await client.post(
            "/api/v1/sales/reps",
            json={
                "code": code_rep,
                "full_name": "Vendedor Beta",
                "branch_id": str(test_setup["branch_id"]),
                "team": "Equipo-Este",
                "territory": "Lima Este"
            },
            headers=admin_headers
        )
        rep_id = create_res.json()["rep_id"]

        with sync_session_factory() as session:
            sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=202,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("500"),
                tax_amount=Decimal("90"),
                total_amount=Decimal("590"),
                paid_amount=Decimal("590"),
                confirmed_at=datetime.now(timezone.utc)
            )
            session.add(sale)
            session.commit()
            sale_id = sale.id

        move_res = await client.patch(
            f"/api/v1/sales/reps/{rep_id}",
            json={"team": "Equipo-Oeste"},
            headers=admin_headers
        )
        assert move_res.status_code == 200
        assert move_res.json()["team"] == "Equipo-Oeste"

        with sync_session_factory() as session:
            old_sale = session.get(SaleModel, sale_id)
            assert old_sale.branch_id == test_setup["branch_id"]
            assert old_sale.sales_rep_id == UUID(rep_id)


@pytest.mark.asyncio
async def test_ven_003_sales_targets_definition_and_advance(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rep_res = await client.post(
            "/api/v1/sales/reps",
            json={
                "code": f"REP-{uuid4().hex[:6]}",
                "full_name": "Vendedor Gamma",
                "branch_id": str(test_setup["branch_id"])
            },
            headers=admin_headers
        )
        rep_id = rep_res.json()["rep_id"]
        period = "2026-10"

        for target_type, val in [("amount", "10000"), ("units", "50"), ("clients", "20")]:
            target_res = await client.post(
                "/api/v1/sales/targets",
                json={
                    "representative_id": rep_id,
                    "period": period,
                    "target_type": target_type,
                    "target_value": val,
                    "currency": "USD",
                    "scope": "individual"
                },
                headers=admin_headers
            )
            assert target_res.status_code == 201
            assert target_res.json()["target_type"] == target_type

        list_res = await client.get(
            f"/api/v1/sales/targets?period={period}&representative_id={rep_id}",
            headers=admin_headers
        )
        assert list_res.status_code == 200, list_res.text
        items = list_res.json()["items"]
        assert len(items) == 3
        for item in items:
            assert "advance_value" in item
            assert "attainment_percentage" in item
            assert item["currency"] == "USD"


@pytest.mark.asyncio
async def test_ven_004_fair_comparison_and_no_fake_zero(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rep_res = await client.post(
            "/api/v1/sales/reps",
            json={
                "code": f"REP-{uuid4().hex[:6]}",
                "full_name": "Vendedor Sin Meta",
                "branch_id": str(test_setup["branch_id"])
            },
            headers=admin_headers
        )
        rep_id = rep_res.json()["rep_id"]

        list_res = await client.get("/api/v1/sales/reps/list?period=2026-10", headers=admin_headers)
        assert list_res.status_code == 200
        data = list_res.json()
        all_reps = data.get("items", data)
        target_rep = next((r for r in all_reps if r["rep_id"] == rep_id), None)
        assert target_rep is not None
        assert target_rep["target_quota"] is None
        assert target_rep["quota_attainment_pct"] is None
        assert "total_sales" in target_rep
        assert "average_ticket" in target_rep
        assert "returns_amount" in target_rep
        assert "active_days" in target_rep


@pytest.mark.asyncio
async def test_ven_005_supervision_permissions_and_scope(admin_headers, supervisor_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        team_name = f"Team-{uuid4().hex[:4]}"
        rep_res = await client.post(
            "/api/v1/sales/reps",
            json={
                "code": f"REP-{uuid4().hex[:6]}",
                "full_name": "Vendedor Supervisado",
                "branch_id": str(test_setup["branch_id"]),
                "team": team_name,
                "supervisor_id": str(USER_SUPERVISOR_A)
            },
            headers=admin_headers
        )
        rep_id = rep_res.json()["rep_id"]

        sup_res = await client.get(f"/api/v1/sales/reps/list?team={team_name}", headers=supervisor_headers)
        assert sup_res.status_code == 200
        items_data = sup_res.json()
        items = items_data.get("items", items_data)
        assert any(r["rep_id"] == rep_id for r in items)

        await client.patch(
            f"/api/v1/sales/reps/{rep_id}",
            json={"team": "Otro-Team"},
            headers=admin_headers
        )
        sup_res2 = await client.get(f"/api/v1/sales/reps/list?team={team_name}", headers=supervisor_headers)
        items_data2 = sup_res2.json()
        items2 = items_data2.get("items", items_data2)
        assert not any(r["rep_id"] == rep_id for r in items2)


@pytest.mark.asyncio
async def test_ven_006_portfolio_reassignment_with_history_and_notification(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        u_seller = create_durable_identity(company_id=COMPANY_A, role="salesperson", email=f"sel_{uuid4().hex[:6]}@salesia.enterprise")
        u_sup = create_durable_identity(company_id=COMPANY_A, role="manager", email=f"sup_{uuid4().hex[:6]}@salesia.enterprise")
        r1 = await client.post(
            "/api/v1/sales/reps",
            json={"code": f"REP-{uuid4().hex[:6]}", "full_name": "Vendedor Origen", "user_id": str(u_seller["user_id"])},
            headers=admin_headers
        )
        assert r1.status_code == 201, r1.text
        rep1_id = r1.json()["rep_id"]

        r2 = await client.post(
            "/api/v1/sales/reps",
            json={"code": f"REP-{uuid4().hex[:6]}", "full_name": "Vendedor Destino", "user_id": str(u_sup["user_id"])},
            headers=admin_headers
        )
        assert r2.status_code == 201, r2.text
        rep2_id = r2.json()["rep_id"]

        with sync_session_factory() as session:
            prof = CustomerProfileModel(
                id=uuid4(),
                company_id=COMPANY_A,
                customer_id=test_setup["customer_id"],
                assigned_sales_rep_id=UUID(rep1_id),
                status="active"
            )
            session.add(prof)
            opp = CustomerOpportunityModel(
                id=uuid4(),
                company_id=COMPANY_A,
                customer_id=test_setup["customer_id"],
                title="Oportunidad Software",
                stage="qualified",
                estimated_amount=Decimal("1200"),
                currency="USD",
                assigned_to_id=u_seller["user_id"]
            )
            session.add(opp)
            act = CustomerActivityModel(
                id=uuid4(),
                company_id=COMPANY_A,
                customer_id=test_setup["customer_id"],
                activity_type="call",
                subject="Llamada de seguimiento",
                due_date=datetime.now(timezone.utc),
                status="pending",
                assigned_to_id=u_seller["user_id"]
            )
            session.add(act)
            session.commit()

        preview = await client.get(f"/api/v1/sales/reps/{rep1_id}/portfolio", headers=admin_headers)
        assert preview.status_code == 200
        pdata = preview.json()
        assert pdata["customers_count"] >= 1
        assert pdata["opportunities_count"] >= 1
        assert pdata["activities_count"] >= 1

        reassign = await client.post(
            f"/api/v1/sales/reps/{rep1_id}/reassign-portfolio",
            json={"target_rep_id": rep2_id, "reason": "Reestructuracion territorial"},
            headers=admin_headers
        )
        assert reassign.status_code == 200
        rdata = reassign.json()
        assert rdata["status"] == "reassigned"
        assert rdata["reassigned_customers"] >= 1

        with sync_session_factory() as session:
            updated_prof = session.scalar(select(CustomerProfileModel).where(CustomerProfileModel.customer_id == test_setup["customer_id"]))
            assert updated_prof.assigned_sales_rep_id == UUID(rep2_id)
            history = json.loads(updated_prof.assignment_history_json)
            assert len(history) > 0
            assert history[-1]["from_rep_id"] == rep1_id
            assert history[-1]["to_rep_id"] == rep2_id

            notif = session.scalar(select(Notification).where(Notification.company_id == COMPANY_A, Notification.user_id == u_sup["user_id"]))
            assert notif is not None


@pytest.mark.asyncio
async def test_ven_007_commissions_calculation_repeatable_and_deterministic(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/sales/reps",
            json={"code": f"REP-{uuid4().hex[:6]}", "full_name": "Vendedor Comisiones", "monthly_quota": "2000"},
            headers=admin_headers
        )
        rep_id = r.json()["rep_id"]
        period = "2026-07"

        with sync_session_factory() as session:
            s = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=701,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("2000"),
                tax_amount=Decimal("360"),
                total_amount=Decimal("2360"),
                paid_amount=Decimal("2360"),
                confirmed_at=datetime(2026, 7, 10, tzinfo=timezone.utc)
            )
            session.add(s)
            session.commit()

        calc1 = await client.post(
            "/api/v1/sales/commissions/calculate",
            json={"rep_id": rep_id, "period": period},
            headers=admin_headers
        )
        assert calc1.status_code == 200
        d1 = calc1.json()
        assert d1["gross_sales"] == "2360.000000"

        calc2 = await client.post(
            "/api/v1/sales/commissions/calculate",
            json={"rep_id": rep_id, "period": period},
            headers=admin_headers
        )
        assert calc2.status_code == 200
        d2 = calc2.json()
        assert d1["settlement_id"] == d2["settlement_id"]
        assert d1["commission_amount"] == d2["commission_amount"]


@pytest.mark.asyncio
async def test_ven_008_commissions_reversion_and_prior_adjustments(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/sales/reps",
            json={"code": f"REP-{uuid4().hex[:6]}", "full_name": "Vendedor Ajustes", "monthly_quota": "1000"},
            headers=admin_headers
        )
        rep_id = r.json()["rep_id"]

        with sync_session_factory() as session:
            s1 = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=801,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("1500"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("1500"),
                paid_amount=Decimal("1500"),
                confirmed_at=datetime(2026, 5, 5, tzinfo=timezone.utc)
            )
            session.add(s1)
            session.flush()
            p1 = PaymentModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=s1.id,
                amount=Decimal("1500"),
                currency="USD",
                payment_method="CASH",
                status="confirmed"
            )
            session.add(p1)
            session.commit()
            p1_id = p1.id

        c_p1 = await client.post(
            "/api/v1/sales/commissions/calculate",
            json={"rep_id": rep_id, "period": "2026-05"},
            headers=admin_headers
        )
        assert c_p1.status_code == 200
        settle1_id = c_p1.json()["settlement_id"]
        await client.post(f"/api/v1/sales/commissions/{settle1_id}/approve", headers=admin_headers)
        await client.post(f"/api/v1/sales/commissions/{settle1_id}/pay", headers=admin_headers)

        with sync_session_factory() as session:
            ref = RefundModel(
                id=uuid4(),
                company_id=COMPANY_A,
                payment_id=p1_id,
                amount=Decimal("300"),
                reason="Devolucion parcial",
                created_at=datetime(2026, 6, 15, tzinfo=timezone.utc)
            )
            session.add(ref)
            s2 = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=802,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("1200"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("1200"),
                paid_amount=Decimal("1200"),
                confirmed_at=datetime(2026, 6, 10, tzinfo=timezone.utc)
            )
            session.add(s2)
            session.commit()

        c_p2 = await client.post(
            "/api/v1/sales/commissions/calculate",
            json={"rep_id": rep_id, "period": "2026-06"},
            headers=admin_headers
        )
        assert c_p2.status_code == 200
        d_p2 = c_p2.json()
        assert Decimal(d_p2["prior_adjustments"]) == Decimal("300")
        assert Decimal(d_p2["net_sales"]) == Decimal("900")

        with sync_session_factory() as session:
            old_settle = session.get(CommissionSettlement, UUID(settle1_id))
            assert old_settle.status == "paid"
            assert old_settle.gross_sales == Decimal("1500")


@pytest.mark.asyncio
async def test_ven_009_approval_and_closing_separation_of_duties(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sep_seller = create_durable_identity(
            company_id=COMPANY_A,
            role="salesperson",
            email=f"sep_seller_{uuid4().hex[:6]}@salesia.enterprise"
        )
        r = await client.post(
            "/api/v1/sales/reps",
            json={"code": f"REP-{uuid4().hex[:6]}", "full_name": "Vendedor Separado", "user_id": str(sep_seller["user_id"]), "monthly_quota": "1000"},
            headers=admin_headers
        )
        assert r.status_code == 201, r.text
        rep_id = r.json()["rep_id"]

        with sync_session_factory() as session:
            s = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=test_setup["branch_id"],
                customer_id=test_setup["customer_id"],
                sales_rep_id=UUID(rep_id),
                series=uuid4().hex[:4],
                number=901,
                status="confirmed",
                currency="USD",
                subtotal_amount=Decimal("1000"),
                tax_amount=Decimal("0"),
                total_amount=Decimal("1000"),
                paid_amount=Decimal("1000"),
                confirmed_at=datetime(2026, 8, 10, tzinfo=timezone.utc)
            )
            session.add(s)
            session.commit()

        calc = await client.post(
            "/api/v1/sales/commissions/calculate",
            json={"rep_id": rep_id, "period": "2026-08"},
            headers=admin_headers
        )
        settle_id = calc.json()["settlement_id"]

        seller_appr = await client.post(f"/api/v1/sales/commissions/{settle_id}/approve", headers=sep_seller["headers"])
        assert seller_appr.status_code in (403, 409)

        admin_appr = await client.post(f"/api/v1/sales/commissions/{settle_id}/approve", headers=admin_headers)
        assert admin_appr.status_code == 200
        assert admin_appr.json()["status"] == "approved"

        dup_appr = await client.post(f"/api/v1/sales/commissions/{settle_id}/approve", headers=admin_headers)
        assert dup_appr.status_code == 409

        pay = await client.post(f"/api/v1/sales/commissions/{settle_id}/pay", headers=admin_headers)
        assert pay.status_code == 200
        assert pay.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_ord_001_quotation_editor_and_incomplete_draft(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        draft_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "is_draft": True,
                "lines": []
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert draft_res.status_code == 201
        assert draft_res.json()["status"] == "draft"
        assert Decimal(draft_res.json()["total_amount"]) == Decimal("0")

        full_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "delivery_terms": "Entrega en obra 48h",
                "notes": "Cotizacion formal con descuento",
                "is_draft": False,
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "2", "discount_pct": "5"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert full_res.status_code == 201
        data = full_res.json()
        assert data["status"] == "pending"
        assert data["delivery_terms"] == "Entrega en obra 48h"
        assert len(data["lines"]) == 1


@pytest.mark.asyncio
async def test_ord_002_quotation_versioning_immutability(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        v1_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        v1_id = v1_res.json()["quotation_id"]
        assert v1_res.json()["version"] == 1

        v2_res = await client.post(
            f"/api/v1/quotations/{v1_id}/versions",
            json={
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "3", "discount_pct": "10"}],
                "delivery_terms": "Despacho express"
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert v2_res.status_code == 201
        v2_data = v2_res.json()
        assert v2_data["version"] == 2
        assert v2_data["quotation_number"] == v1_res.json()["quotation_number"]

        v1_fetch = await client.get(f"/api/v1/quotations/{v1_id}", headers=admin_headers)
        assert v1_fetch.json()["status"] == "superseded"
        assert v1_fetch.json()["version"] == 1
        assert len(v1_fetch.json()["lines"]) == 1
        assert v1_fetch.json()["lines"][0]["quantity"] == "1.000000"


@pytest.mark.asyncio
async def test_ord_003_quotation_acceptance(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        q_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "2", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        qid = q_res.json()["quotation_id"]

        acc_res = await client.post(
            f"/api/v1/quotations/{qid}/accept",
            json={"conditions": "Aprobado por compras cliente"},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert acc_res.status_code == 200
        assert acc_res.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_ord_004_quotation_conversion_idempotent(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        q_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        qid = q_res.json()["quotation_id"]
        await client.post(f"/api/v1/quotations/{qid}/accept", headers={**admin_headers, "Idempotency-Key": uuid4().hex})

        conv_key = uuid4().hex
        conv1 = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_headers, "Idempotency-Key": conv_key}
        )
        assert conv1.status_code == 201
        order_id_1 = conv1.json()["order_id"]

        conv2 = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_headers, "Idempotency-Key": conv_key}
        )
        assert conv2.status_code in (200, 201)
        assert conv2.json()["order_id"] == order_id_1


@pytest.mark.asyncio
async def test_ord_005_quotation_pricing_expiration(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        q_res = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "valid_until": past_date,
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        qid = q_res.json()["quotation_id"]

        with sync_session_factory() as session:
            q_row = session.get(QuotationModel, UUID(qid))
            q_row.status = "accepted"
            session.commit()

        reject_conv = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}&honor_expired_price=false",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert reject_conv.status_code == 409

        allow_conv = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}&honor_expired_price=true",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert allow_conv.status_code == 201


@pytest.mark.asyncio
async def test_ord_006_order_stock_reservation_concurrency(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with sync_session_factory() as session:
            prod_single = ProductModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sku=f"SKU-SINGLE-{uuid4().hex[:4]}",
                name="Producto Unitario",
                category="General",
                unit_of_measure="NIU",
                unit_price=Decimal("100"),
                unit_cost=Decimal("50"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(prod_single)
            session.flush()
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=test_setup["warehouse_id"],
                product_id=prod_single.id,
                physical_quantity=Decimal("1"),
                reserved_quantity=Decimal("0"),
                average_cost=Decimal("50")
            ))
            session.commit()
            single_pid = prod_single.id

        o1 = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(single_pid), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        o1_id = o1.json()["order_id"]

        o2 = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(single_pid), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        o2_id = o2.json()["order_id"]

        c1 = await client.post(f"/api/v1/orders/{o1_id}/confirm", headers={**admin_headers, "Idempotency-Key": uuid4().hex})
        assert c1.status_code == 200
        assert c1.json()["stock_reserved"] is True

        c2 = await client.post(
            f"/api/v1/orders/{o2_id}/confirm",
            json={"allow_backorder": False},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert c2.status_code == 409


@pytest.mark.asyncio
async def test_ord_007_reservation_release_and_renewal_no_double_liberation(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "2", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]
        await client.post(f"/api/v1/orders/{oid}/confirm", headers={**admin_headers, "Idempotency-Key": uuid4().hex})

        renew = await client.post(f"/api/v1/orders/{oid}/renew-reservation?extension_days=14", headers=admin_headers)
        assert renew.status_code == 200
        assert renew.json()["reservation_expires_at"] is not None

        rel_key = uuid4().hex
        rel1 = await client.post(f"/api/v1/orders/{oid}/release-reservation", headers={**admin_headers, "Idempotency-Key": rel_key})
        assert rel1.status_code == 200
        assert rel1.json()["stock_reserved"] is False

        rel2 = await client.post(f"/api/v1/orders/{oid}/release-reservation", headers={**admin_headers, "Idempotency-Key": uuid4().hex})
        assert rel2.status_code == 409


@pytest.mark.asyncio
async def test_ord_008_partial_order_fulfillment_bounds(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "5", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]
        await client.post(f"/api/v1/orders/{oid}/confirm", headers={**admin_headers, "Idempotency-Key": uuid4().hex})

        f1 = await client.post(
            f"/api/v1/orders/{oid}/fulfill-partial",
            json={"fulfilled_items": [{"product_id": str(test_setup["product_id"]), "quantity": "3"}]},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert f1.status_code == 200
        assert f1.json()["status"] == "partially_fulfilled"

        f_overflow = await client.post(
            f"/api/v1/orders/{oid}/fulfill-partial",
            json={"fulfilled_items": [{"product_id": str(test_setup["product_id"]), "quantity": "3"}]},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert f_overflow.status_code == 409

        f2 = await client.post(
            f"/api/v1/orders/{oid}/fulfill-partial",
            json={"fulfilled_items": [{"product_id": str(test_setup["product_id"]), "quantity": "2"}]},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert f2.status_code == 200
        assert f2.json()["status"] == "fulfilled"


@pytest.mark.asyncio
async def test_ord_009_backorder_handling_and_availability(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with sync_session_factory() as session:
            p_zero = ProductModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sku=f"SKU-BO-{uuid4().hex[:4]}",
                name="Producto Agotado",
                category="General",
                unit_of_measure="NIU",
                unit_price=Decimal("80"),
                unit_cost=Decimal("40"),
                tax_rate=Decimal("0.18"),
                is_active=True
            )
            session.add(p_zero)
            session.flush()
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=test_setup["warehouse_id"],
                product_id=p_zero.id,
                physical_quantity=Decimal("0"),
                reserved_quantity=Decimal("0"),
                average_cost=Decimal("40")
            ))
            session.commit()
            bo_pid = p_zero.id

        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(bo_pid), "quantity": "10", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]

        c_bo = await client.post(
            f"/api/v1/orders/{oid}/confirm",
            json={"allow_backorder": True},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert c_bo.status_code == 200
        data = c_bo.json()
        assert data["status"] == "backorder"
        assert data["lines"][0]["is_backorder"] is True
        assert Decimal(data["lines"][0]["backorder_quantity"]) == Decimal("10")
        assert data["lines"][0]["estimated_delivery_date"] is not None


@pytest.mark.asyncio
async def test_ord_010_order_approval_invalidated_on_line_edit(admin_headers, approver_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "20"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]
        assert o.json()["status"] == "pending_approval"

        appr = await client.post(f"/api/v1/orders/{oid}/approve", headers={**approver_headers, "Idempotency-Key": uuid4().hex})
        assert appr.status_code == 200
        assert appr.json()["status"] == "draft"

        edit = await client.put(
            f"/api/v1/orders/{oid}/lines",
            json={"lines": [{"product_id": str(test_setup["product_id"]), "quantity": "2", "discount_pct": "25"}]},
            headers=admin_headers
        )
        assert edit.status_code == 200
        assert edit.json()["status"] == "pending_approval"
        assert edit.json()["requires_approval"] is True


@pytest.mark.asyncio
async def test_ord_011_partial_order_cancellation(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "4", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]
        await client.post(f"/api/v1/orders/{oid}/confirm", headers={**admin_headers, "Idempotency-Key": uuid4().hex})

        await client.post(
            f"/api/v1/orders/{oid}/fulfill-partial",
            json={"fulfilled_items": [{"product_id": str(test_setup["product_id"]), "quantity": "2"}]},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )

        cancel_res = await client.post(
            f"/api/v1/orders/{oid}/cancel",
            json={
                "reason": "Cliente redujo pedido",
                "cancelled_items": [{"product_id": str(test_setup["product_id"]), "quantity": "2"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cancel_res.status_code == 200
        data = cancel_res.json()
        assert data["lines"][0]["fulfilled_quantity"] == "2.000000"
        assert data["lines"][0]["cancelled_quantity"] == "2.000000"
        assert data["lines"][0]["reserved_quantity"] == "0.000000"


@pytest.mark.asyncio
async def test_ord_012_order_tracking_timeline_and_relations(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        q = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        qid = q.json()["quotation_id"]
        await client.post(f"/api/v1/quotations/{qid}/accept", headers={**admin_headers, "Idempotency-Key": uuid4().hex})
        conv = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = conv.json()["order_id"]

        track = await client.get(f"/api/v1/orders/{oid}/tracking", headers=admin_headers)
        assert track.status_code == 200
        tdata = track.json()
        assert tdata["order_id"] == oid
        assert tdata["linked_quotation"]["id"] == qid
        assert len(tdata["timeline"]) >= 1
        assert "next_step" in tdata


@pytest.mark.asyncio
async def test_ord_013_order_attachments_po_and_conditions_snapshot(admin_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "customer_po_number": "PO-GLOBAL-9999",
                "delivery_terms": "Incoterm CIF Callao",
                "attachments": [{"filename": "orden_compra.pdf", "url": "https://storage/oc.pdf"}],
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert o.status_code == 201
        oid = o.json()["order_id"]
        assert o.json()["customer_po_number"] == "PO-GLOBAL-9999"
        assert o.json()["delivery_terms"] == "Incoterm CIF Callao"
        assert len(o.json()["attachments"]) == 1

        c = await client.post(f"/api/v1/orders/{oid}/confirm", headers={**admin_headers, "Idempotency-Key": uuid4().hex})
        assert c.status_code == 200, c.text
        assert c.json()["customer_po_number"] == "PO-GLOBAL-9999"


@pytest.mark.asyncio
async def test_api_029_quotations_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ok = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "2", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert ok.status_code == 201

        inv = await client.post(
            "/api/v1/quotations",
            json={"customer_id": str(uuid4()), "lines": []},
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert inv.status_code == 422

        cross = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_b_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code in (422, 403)


@pytest.mark.asyncio
async def test_api_030_quotation_convert_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        q = await client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "currency": "USD",
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        qid = q.json()["quotation_id"]
        await client.post(f"/api/v1/quotations/{qid}/accept", headers={**admin_headers, "Idempotency-Key": uuid4().hex})

        cross = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_b_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code == 403

        nf = await client.post(
            f"/api/v1/quotations/{uuid4()}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert nf.status_code == 404

        ok = await client.post(
            f"/api/v1/quotations/{qid}/convert?warehouse_id={test_setup['warehouse_id']}",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert ok.status_code == 201


@pytest.mark.asyncio
async def test_api_031_orders_list_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        l_a = await client.get("/api/v1/orders?limit=10&offset=0", headers=admin_headers)
        assert l_a.status_code == 200
        assert isinstance(l_a.json(), list)

        l_b = await client.get("/api/v1/orders?limit=10&offset=0", headers=admin_b_headers)
        assert l_b.status_code == 200
        assert isinstance(l_b.json(), list)
        a_ids = {item["order_id"] for item in l_a.json()}
        b_ids = {item["order_id"] for item in l_b.json()}
        assert a_ids.isdisjoint(b_ids)


@pytest.mark.asyncio
async def test_api_032_orders_create_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ok = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert ok.status_code == 201

        inv = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": []
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert inv.status_code == 422

        cross = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_b_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code in (422, 403)


@pytest.mark.asyncio
async def test_api_033_orders_confirm_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]

        cross = await client.post(
            f"/api/v1/orders/{oid}/confirm",
            headers={**admin_b_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code == 403

        nf = await client.post(
            f"/api/v1/orders/{uuid4()}/confirm",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert nf.status_code == 404

        ok = await client.post(
            f"/api/v1/orders/{oid}/confirm",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert ok.status_code == 200


@pytest.mark.asyncio
async def test_api_034_orders_cancel_contract(admin_headers, admin_b_headers, test_setup):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        o = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": str(test_setup["customer_id"]),
                "branch_id": str(test_setup["branch_id"]),
                "warehouse_id": str(test_setup["warehouse_id"]),
                "lines": [{"product_id": str(test_setup["product_id"]), "quantity": "1", "discount_pct": "0"}]
            },
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        oid = o.json()["order_id"]

        cross = await client.post(
            f"/api/v1/orders/{oid}/cancel",
            headers={**admin_b_headers, "Idempotency-Key": uuid4().hex}
        )
        assert cross.status_code == 403

        nf = await client.post(
            f"/api/v1/orders/{uuid4()}/cancel",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert nf.status_code == 404

        ok = await client.post(
            f"/api/v1/orders/{oid}/cancel",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex}
        )
        assert ok.status_code == 200
