from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from salesia.main import app
from salesia.shared.infrastructure.database import sync_engine, sync_session_factory, Base
from datetime import datetime, timezone
from salesia.shared.infrastructure.models import (
    CompanyModel,
    BranchModel,
    CustomerModel,
    ProductModel,
    SaleModel,
    SaleLineModel,
    UserModel,
    PaymentModel
)
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.shared.infrastructure.transactions import RefundModel
from salesia.modules.seguridad.infrastructure.security import create_access_token, hash_password
from tests.support.auth_helpers import create_durable_identity

TEST_COMPANY_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        comp = session.execute(
            select(CompanyModel).where(CompanyModel.id == TEST_COMPANY_ID)
        ).scalar_one_or_none()
        if not comp:
            comp = CompanyModel(
                id=TEST_COMPANY_ID,
                tax_id="20999999999",
                legal_name="EMPRESA COMERCIAL MATRIZ S.A.C.",
                trade_name="SALESIA CORP",
                base_currency="USD",
                is_active=True
            )
            session.add(comp)

        branch = session.execute(
            select(BranchModel).where(BranchModel.id == TEST_BRANCH_ID)
        ).scalar_one_or_none()
        if not branch:
            branch = BranchModel(
                id=TEST_BRANCH_ID,
                company_id=TEST_COMPANY_ID,
                code="SUC-01",
                name="Sucursal Principal Lima",
                timezone="America/Lima",
                is_active=True
            )
            session.add(branch)
        session.commit()
    yield


@pytest.fixture
def auth_headers():
    identity = create_durable_identity(
        company_id=TEST_COMPANY_ID,
        user_id=TEST_USER_ID,
        role="company_admin",
        email="gerente@salesia.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_crm_customer_lifecycle_and_merge(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        doc_num = f"20{uuid4().int % 1000000000:09d}"
        create_res = await client.post(
            "/api/v1/customers",
            headers=auth_headers,
            json={
                "code": f"CLI-{doc_num[:6]}",
                "doc_type": "RUC",
                "doc_number": doc_num,
                "legal_name": "DISTRIBUIDORA NORTE S.A.C.",
                "credit_limit": 25000.00
            }
        )
        assert create_res.status_code == 201
        customer_id = create_res.json()["id"]

        dup_res = await client.post(
            "/api/v1/customers",
            headers=auth_headers,
            json={
                "code": "CLI-OTRO",
                "doc_type": "RUC",
                "doc_number": doc_num,
                "legal_name": "OTRO NOMBRE S.A.C.",
                "credit_limit": 10000.00
            }
        )
        assert dup_res.status_code == 409

        get_res = await client.get(f"/api/v1/customers/{customer_id}", headers=auth_headers)
        assert get_res.status_code == 200
        assert get_res.json()["doc_number"] == doc_num

        archive_res = await client.post(f"/api/v1/customers/{customer_id}/archive", headers=auth_headers)
        assert archive_res.status_code == 200
        assert archive_res.json()["is_active"] is False

        restore_res = await client.post(f"/api/v1/customers/{customer_id}/restore", headers=auth_headers)
        assert restore_res.status_code == 200
        assert restore_res.json()["is_active"] is True

        dup2_num = f"20{uuid4().int % 1000000000:09d}"
        c2_res = await client.post(
            "/api/v1/customers",
            headers=auth_headers,
            json={
                "code": f"CLI-{dup2_num[:6]}",
                "doc_type": "RUC",
                "doc_number": dup2_num,
                "legal_name": "DISTRIBUIDORA SECUNDARIA S.A.C.",
                "credit_limit": 15000.00
            }
        )
        c2_id = c2_res.json()["id"]

        merge_res = await client.post(
            "/api/v1/customers/merge",
            headers=auth_headers,
            json={
                "primary_customer_id": customer_id,
                "duplicate_customer_id": c2_id
            }
        )
        assert merge_res.status_code == 200
        assert merge_res.json()["status"] == "completed"

        statement_res = await client.get(f"/api/v1/customers/{customer_id}/statement", headers=auth_headers)
        assert statement_res.status_code == 200
        assert "invoices_count" in statement_res.json()


@pytest.mark.asyncio
async def test_catalog_sku_uniqueness_and_pricing_engine(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_sku = f"SKU-{uuid4().hex[:8].upper()}"
        prod_res = await client.post(
            "/api/v1/products",
            headers=auth_headers,
            json={
                "sku": unique_sku,
                "name": "Servidor Rack 1U Xeon",
                "category": "Infraestructura",
                "unit_of_measure": "NIU",
                "unit_price": 2400.00,
                "unit_cost": 1600.00,
                "tax_rate": 0.18
            }
        )
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        dup_sku_res = await client.post(
            "/api/v1/products",
            headers=auth_headers,
            json={
                "sku": unique_sku,
                "name": "Duplicado",
                "category": "Infraestructura",
                "unit_price": 2500.00,
                "unit_cost": 1700.00
            }
        )
        assert dup_sku_res.status_code == 409

        preview_single = await client.post(
            "/api/v1/prices/preview",
            headers=auth_headers,
            json={"product_id": prod_id, "quantity": 1}
        )
        assert preview_single.status_code == 200
        assert preview_single.json()["discount_percentage"] == "0.00"
        assert preview_single.json()["final_unit_price"] == "2400.000000"

        preview_vol_10 = await client.post(
            "/api/v1/prices/preview",
            headers=auth_headers,
            json={"product_id": prod_id, "quantity": 10}
        )
        assert preview_vol_10.status_code == 200
        assert Decimal(preview_vol_10.json()["discount_percentage"]) == Decimal("5.00")
        assert preview_vol_10.json()["final_unit_price"] == "2280.000000"

        preview_vol_50 = await client.post(
            "/api/v1/prices/preview",
            headers=auth_headers,
            json={"product_id": prod_id, "quantity": 50}
        )
        assert preview_vol_50.status_code == 200
        assert Decimal(preview_vol_50.json()["discount_percentage"]) == Decimal("10.00")
        assert preview_vol_50.json()["final_unit_price"] == "2160.000000"


@pytest.mark.asyncio
async def test_commercial_snapshot_immutability(auth_headers):
    sku = f"SKU-{uuid4().hex[:8].upper()}"
    with sync_session_factory() as session:
        product = ProductModel(
            id=uuid4(),
            company_id=TEST_COMPANY_ID,
            sku=sku,
            name="Impresora Termica Fiscal",
            category="Punto de Venta",
            unit_of_measure="NIU",
            unit_price=Decimal("450.000000"),
            unit_cost=Decimal("280.000000"),
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(product)

        customer = CustomerModel(
            id=uuid4(),
            company_id=TEST_COMPANY_ID,
            code=f"CLI-{uuid4().hex[:6]}",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 1000000000:09d}",
            legal_name="RETAIL PRUEBA S.A.",
            credit_limit=Decimal("50000.000000"),
            current_balance=Decimal("0.000000"),
            is_active=True
        )
        session.add(customer)

        sale = SaleModel(
            id=uuid4(),
            company_id=TEST_COMPANY_ID,
            branch_id=TEST_BRANCH_ID,
            customer_id=customer.id,
            series="F001",
            number=uuid4().int % 100000,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("450.000000"),
            tax_amount=Decimal("81.000000"),
            total_amount=Decimal("531.000000"),
            paid_amount=Decimal("0.000000")
        )
        session.add(sale)

        line = SaleLineModel(
            id=uuid4(),
            company_id=TEST_COMPANY_ID,
            sale_id=sale.id,
            product_id=product.id,
            line_number=1,
            sku_snapshot=product.sku,
            name_snapshot=product.name,
            unit_of_measure_snapshot=product.unit_of_measure,
            quantity=Decimal("1.000000"),
            unit_price_snapshot=Decimal("450.000000"),
            unit_cost_snapshot=Decimal("280.000000"),
            discount_amount=Decimal("0.000000"),
            tax_rate_snapshot=Decimal("0.1800"),
            subtotal_amount=Decimal("450.000000"),
            tax_amount=Decimal("81.000000"),
            total_amount=Decimal("531.000000")
        )
        session.add(line)
        session.commit()

        product.name = "Impresora Modificada 2027"
        product.unit_price = Decimal("890.000000")
        product.is_active = False
        session.commit()

        persisted_line = session.execute(
            select(SaleLineModel).where(SaleLineModel.id == line.id)
        ).scalar_one()

        assert persisted_line.name_snapshot == "Impresora Termica Fiscal"
        assert persisted_line.unit_price_snapshot == Decimal("450.000000")
        assert persisted_line.total_amount == Decimal("531.000000")


@pytest.mark.asyncio
async def test_sales_reps_and_commission_tiers(auth_headers):
    cust_id = uuid4()
    u1_id, u2_id, u3_id = uuid4(), uuid4(), uuid4()
    rep1_id, rep2_id, rep3_id = uuid4(), uuid4(), uuid4()
    s1_id, s2_id, s3_id = uuid4(), uuid4(), uuid4()
    pay3_id = uuid4()
    ref3_id = uuid4()

    with sync_session_factory() as session:
        cust = CustomerModel(
            id=cust_id,
            company_id=TEST_COMPANY_ID,
            code=f"CUST-{uuid4().hex[:6]}",
            doc_type="RUC",
            doc_number=f"20{uuid4().int % 1000000000:09d}",
            legal_name="Comisiones Test SAC",
            is_active=True
        )
        session.add(cust)

        for u_id, name in [
            (u1_id, "Vendedor Under"),
            (u2_id, "Vendedor Tier1"),
            (u3_id, "Vendedor Over")
        ]:
            user = UserModel(
                id=u_id,
                company_id=TEST_COMPANY_ID,
                email=f"rep_{uuid4().hex[:6]}@salesia.enterprise",
                hashed_password=hash_password("Pass123!"),
                role="salesperson",
                is_active=True
            )
            session.add(user)
        session.flush()

        for u_id, r_id, name in [
            (u1_id, rep1_id, "Vendedor Under"),
            (u2_id, rep2_id, "Vendedor Tier1"),
            (u3_id, rep3_id, "Vendedor Over")
        ]:
            rep = SalesRepresentative(
                id=r_id,
                company_id=TEST_COMPANY_ID,
                user_id=u_id,
                full_name=name,
                territory="Lima",
                monthly_quota=Decimal("50000.000000"),
                is_active=True
            )
            session.add(rep)
        session.flush()

        session.add(SaleModel(
            id=s1_id,
            company_id=TEST_COMPANY_ID,
            branch_id=TEST_BRANCH_ID,
            customer_id=cust_id,
            sales_rep_id=rep1_id,
            series=f"V{uuid4().hex[:3]}",
            number=1,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("35000.000000"),
            tax_amount=Decimal("0.000000"),
            total_amount=Decimal("35000.000000"),
            paid_amount=Decimal("35000.000000"),
            confirmed_at=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        ))
        session.add(SaleModel(
            id=s2_id,
            company_id=TEST_COMPANY_ID,
            branch_id=TEST_BRANCH_ID,
            customer_id=cust_id,
            sales_rep_id=rep2_id,
            series=f"V{uuid4().hex[:3]}",
            number=2,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("45000.000000"),
            tax_amount=Decimal("0.000000"),
            total_amount=Decimal("45000.000000"),
            paid_amount=Decimal("45000.000000"),
            confirmed_at=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        ))
        session.add(SaleModel(
            id=s3_id,
            company_id=TEST_COMPANY_ID,
            branch_id=TEST_BRANCH_ID,
            customer_id=cust_id,
            sales_rep_id=rep3_id,
            series=f"V{uuid4().hex[:3]}",
            number=3,
            status="confirmed",
            currency="USD",
            subtotal_amount=Decimal("65000.000000"),
            tax_amount=Decimal("0.000000"),
            total_amount=Decimal("65000.000000"),
            paid_amount=Decimal("65000.000000"),
            confirmed_at=datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        ))
        session.flush()

        session.add(PaymentModel(
            id=pay3_id,
            company_id=TEST_COMPANY_ID,
            sale_id=s3_id,
            payment_method="TRANSFER",
            amount=Decimal("65000.000000"),
            currency="USD",
            status="confirmed",
            reference_code=f"TX-{uuid4().hex[:8]}"
        ))
        session.flush()

        session.add(RefundModel(
            id=ref3_id,
            company_id=TEST_COMPANY_ID,
            payment_id=pay3_id,
            amount=Decimal("5000.000000"),
            reason="Devolucion parcial",
            created_at=datetime(2026, 10, 11, 10, 0, tzinfo=timezone.utc)
        ))
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reps_res = await client.get("/api/v1/sales/reps/list", headers=auth_headers)
        assert reps_res.status_code == 200
        assert "items" in reps_res.json()

        calc_under = await client.post(
            "/api/v1/sales/commissions/calculate",
            headers=auth_headers,
            json={
                "rep_id": str(rep1_id),
                "period": "2026-10",
                "gross_sales": "35000.00",
                "returns_amount": "0.00",
                "target_quota": "50000.00"
            }
        )
        assert calc_under.status_code == 200
        assert calc_under.json()["attainment_percentage"] == "70.00"
        assert calc_under.json()["commission_amount"] == "0.000000"

        calc_tier1 = await client.post(
            "/api/v1/sales/commissions/calculate",
            headers=auth_headers,
            json={
                "rep_id": str(rep2_id),
                "period": "2026-10",
                "gross_sales": "45000.00",
                "returns_amount": "0.00",
                "target_quota": "50000.00"
            }
        )
        assert calc_tier1.status_code == 200
        assert calc_tier1.json()["attainment_percentage"] == "90.00"
        assert calc_tier1.json()["commission_amount"] == "1125.000000"

        calc_over = await client.post(
            "/api/v1/sales/commissions/calculate",
            headers=auth_headers,
            json={
                "rep_id": str(rep3_id),
                "period": "2026-10",
                "gross_sales": "65000.00",
                "returns_amount": "5000.00",
                "target_quota": "50000.00"
            }
        )
        assert calc_over.status_code == 200
        assert Decimal(calc_over.json()["net_sales"]) == Decimal("60000.00")
        assert calc_over.json()["attainment_percentage"] == "120.00"
        assert calc_over.json()["commission_amount"] == "4200.000000"
        settlement_id = calc_over.json()["settlement_id"]

        approve_res = await client.post(
            f"/api/v1/sales/commissions/{settlement_id}/approve",
            headers=auth_headers
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "approved"
