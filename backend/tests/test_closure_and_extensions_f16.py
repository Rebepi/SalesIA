import pytest
from httpx import AsyncClient, ASGITransport
from salesia.main import app
from salesia.shared.infrastructure.models import (
    CompanyModel,
    SaleModel,
    InventoryStockModel,
    CustomerModel,
    ProductModel
)


@pytest.mark.asyncio
async def test_openapi_documentation_generation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/openapi.json")
        assert res.status_code == 200
        data = res.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert "/api/v1/health" in data["paths"]
        assert "/api/v1/auth/login" in data["paths"]
        assert "/api/v1/sales/draft" in data["paths"]
        assert "/api/v1/inventory" in data["paths"]
        assert "/api/v1/analytics/summary" in data["paths"]
        assert "/api/v1/operations/system-status" in data["paths"]
        assert "/api/v1/audit/logs" in data["paths"]


@pytest.mark.asyncio
async def test_system_root_metadata():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert data["docs"] == "/docs"
        assert data["api_prefix"] == "/api/v1"


def test_data_dictionary_schema_invariants():
    assert CompanyModel.__tablename__ == "companies"
    assert SaleModel.__tablename__ == "sales"
    assert InventoryStockModel.__tablename__ == "inventory_stocks"
    assert CustomerModel.__tablename__ == "customers"
    assert ProductModel.__tablename__ == "products"

    assert hasattr(SaleModel, "total_amount")
    assert hasattr(SaleModel, "paid_amount")
    assert hasattr(SaleModel, "status")
    assert hasattr(InventoryStockModel, "physical_quantity")
    assert hasattr(InventoryStockModel, "reserved_quantity")
