import secrets
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from salesia.main import app
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, CustomerModel, SaleModel, UserModel


@pytest.mark.asyncio
async def test_commission_uses_persisted_sales_and_approves_once():
    password = secrets.token_urlsafe(24)
    with sync_session_factory() as db:
        company = CompanyModel(tax_id=uuid4().hex, legal_name="Comisiones", trade_name="Comisiones")
        db.add(company)
        db.flush()
        branch = BranchModel(company_id=company.id, code=uuid4().hex[:8], name="Principal")
        customer = CustomerModel(company_id=company.id, code=uuid4().hex[:8], doc_type="RUC", doc_number=uuid4().hex, legal_name="Cliente")
        admin = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="company_admin", is_active=True)
        seller = UserModel(company_id=company.id, email=f"{uuid4().hex}@example.com", hashed_password=hash_password(password), role="salesperson", is_active=True)
        db.add_all([branch, customer, admin, seller])
        db.commit()
        data = {"company": company.id, "branch": branch.id, "customer": customer.id, "admin": admin.email, "seller": seller.id}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json={"email": data["admin"], "password": password})
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        rep = await client.post("/api/v1/sales/reps", json={"user_id": str(data["seller"]), "full_name": "Vendedor Real", "territory": "Lima", "monthly_quota": "1000"})
        assert rep.status_code == 201, rep.text
        rep_id = rep.json()["rep_id"]
        with sync_session_factory() as db:
            db.add(SaleModel(company_id=data["company"], branch_id=data["branch"], customer_id=data["customer"], sales_rep_id=UUID(rep_id), series=uuid4().hex[:8], number=1, status="confirmed", currency="USD", subtotal_amount=Decimal("100"), tax_amount=Decimal("0"), total_amount=Decimal("100"), paid_amount=Decimal("0"), confirmed_at=datetime.now(timezone.utc)))
            db.commit()
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        payload = {"rep_id": rep_id, "period": period, "gross_sales": "999999", "returns_amount": "999", "target_quota": "1"}
        calculated = await client.post("/api/v1/sales/commissions/calculate", json=payload)
        assert calculated.status_code == 200, calculated.text
        assert calculated.json()["gross_sales"] == "100.000000"
        assert calculated.json()["target_quota"] == "1000.000000"
        repeated = await client.post("/api/v1/sales/commissions/calculate", json=payload)
        assert repeated.json()["settlement_id"] == calculated.json()["settlement_id"]
        settlement_id = calculated.json()["settlement_id"]
        assert (await client.post(f"/api/v1/sales/commissions/{settlement_id}/approve")).status_code == 200
        assert (await client.post(f"/api/v1/sales/commissions/{settlement_id}/approve")).status_code == 409
