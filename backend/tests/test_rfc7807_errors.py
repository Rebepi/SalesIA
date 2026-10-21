from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from salesia.main import app
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import ProductModel, InventoryStockModel
from tests.support.auth_helpers import create_durable_identity, ensure_business_records


@pytest.mark.asyncio
async def test_rfc7807_domain_error_format():
    company_id = uuid4()
    user_id = uuid4()
    identity = create_durable_identity(user_id=user_id, company_id=company_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analytics/summary",
            json={"values": []},
            headers=identity["headers"]
        )
        assert response.status_code == 422
        data = response.json()
        assert data["type"] == "https://api.salesia.enterprise/errors/validation-error"
        assert data["title"] == "Error de Validación de Entrada"
        assert "trace_id" in data
        assert "trace" not in data.get("detail", "").lower()


@pytest.mark.asyncio
async def test_rfc7807_validation_error_format():
    company_id = uuid4()
    user_id = uuid4()
    identity = create_durable_identity(user_id=user_id, company_id=company_id, role="company_admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/analytics/bayes",
            json={"prior_a": 2.5, "likelihood_b_given_a": 0.5, "likelihood_b_given_not_a": 0.5},
            headers=identity["headers"]
        )
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "trace_id" in data
        assert len(data.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_sales_endpoint_draft_and_confirm_lifecycle():
    company_id = uuid4()
    user_id = uuid4()
    identity = create_durable_identity(user_id=user_id, company_id=company_id, role="company_admin")
    biz = ensure_business_records(company_id=company_id)
    branch_id = biz["branch_id"]
    warehouse_id = biz["warehouse_id"]
    customer_id = biz["customer_id"]

    prod_id = uuid4()
    with sync_session_factory() as session:
        prod = ProductModel(
            id=prod_id,
            company_id=company_id,
            sku=f"SKU-IPHONE-{uuid4().hex[:6]}",
            name="iPhone 15",
            category="GENERAL",
            unit_of_measure="NIU",
            unit_price=Decimal("999.000000"),
            unit_cost=Decimal("700.000000"),
            tax_rate=Decimal("0.1800"),
            is_active=True
        )
        session.add(prod)
        stock = InventoryStockModel(
            id=uuid4(),
            company_id=company_id,
            warehouse_id=warehouse_id,
            product_id=prod_id,
            physical_quantity=Decimal("10.000000"),
            reserved_quantity=Decimal("0.000000")
        )
        session.add(stock)
        session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_payload = {
            "branch_id": str(branch_id),
            "customer_id": str(customer_id),
            "warehouse_id": str(warehouse_id),
            "currency": "USD",
            "lines": [
                {
                    "product_id": str(prod_id),
                    "sku": "SKU-IPHONE-15",
                    "product_name": "iPhone 15",
                    "quantity": 1,
                    "unit_price": "999.00",
                    "tax_rate": "0.18"
                }
            ]
        }
        res_draft = await client.post(
            "/api/v1/sales/draft",
            json=draft_payload,
            headers={**identity["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert res_draft.status_code == 201
        draft_data = res_draft.json()
        sale_id = draft_data["sale_id"]
        assert draft_data["status"] == "draft"
        assert Decimal(draft_data["total_amount"]) == Decimal("1178.82")

        res_confirm = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**identity["headers"], "Idempotency-Key": uuid4().hex}
        )
        assert res_confirm.status_code == 200
        confirm_data = res_confirm.json()
        assert confirm_data["status"] == "confirmed"

        res_get = await client.get(f"/api/v1/sales/{sale_id}", headers=identity["headers"])
        assert res_get.status_code == 200
        assert res_get.json()["status"] == "confirmed"
