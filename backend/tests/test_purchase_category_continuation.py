from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import select
from test_supply_chain_integrity import supply, client_for
from salesia.modules.catalogo.infrastructure_models import CategoryModel
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import ProductModel


@pytest.mark.asyncio
async def test_purchase_multiline_totals_and_requisition_origin_are_atomic(supply):
    with sync_session_factory() as db:
        second = ProductModel(company_id=supply["company_id"], sku="P2", name="Segundo producto", category="General", unit_of_measure="NIU", unit_price=Decimal("30"), unit_cost=Decimal("8"), tax_rate=Decimal("0.18"))
        db.add(second)
        db.commit()
        second_id = str(second.id)
    client = await client_for(supply)
    try:
        supplier = (await client.post("/api/v1/suppliers", json={"tax_id": uuid4().hex, "legal_name": "Proveedor de conversión", "currency": "PEN"})).json()
        items = [{"product_id": str(supply["product_id"]), "quantity": "4", "unit_cost": "10"}, {"product_id": second_id, "quantity": "2", "unit_cost": "20"}]
        requisition_key = {"Idempotency-Key": uuid4().hex}
        requisition = await client.post("/api/v1/purchases/requisitions", headers=requisition_key, json={"warehouse_id": str(supply["source"]), "items": items, "justification": "Reposición aprobada", "suggested_supplier_id": supplier["id"]})
        assert requisition.status_code == 201, requisition.text
        source_id = requisition.json()["id"]
        repeated_requisition = await client.post("/api/v1/purchases/requisitions", headers=requisition_key, json={"warehouse_id": str(supply["source"]), "items": items, "justification": "Reposición aprobada", "suggested_supplier_id": supplier["id"]})
        assert repeated_requisition.json()["id"] == source_id
        payload = {"supplier_id": supplier["id"], "warehouse_id": str(supply["source"]), "currency": "PEN", "source_requisition_id": source_id, "source_version": 1, "items": [{**items[0], "discount_percentage": "10", "tax_rate": "0.18"}, {**items[1], "tax_rate": "0.18"}]}
        assert (await client.post("/api/v1/purchase-orders", json=payload, headers={"Idempotency-Key": uuid4().hex})).status_code == 409
        approved = await client.post(f"/api/v1/purchases/requisitions/{source_id}/approve")
        payload["source_version"] = approved.json()["version"]
        changed = {**payload, "items": [{**payload["items"][0], "quantity": "5"}, payload["items"][1]]}
        assert (await client.post("/api/v1/purchase-orders", json=changed, headers={"Idempotency-Key": uuid4().hex})).status_code == 422
        key = {"Idempotency-Key": uuid4().hex}
        order = await client.post("/api/v1/purchase-orders", json=payload, headers=key)
        assert order.status_code == 201, order.text
        result = order.json()
        assert result["parent_id"] == source_id
        assert Decimal(result["details"]["subtotal"]) == 76
        assert Decimal(result["details"]["tax_total"]) == Decimal("13.68")
        assert Decimal(result["details"]["total"]) == Decimal("89.68")
        assert Decimal(result["lines"][0]["unit_cost"]) == 9
        repeated = await client.post("/api/v1/purchase-orders", json=payload, headers=key)
        assert repeated.json()["id"] == result["id"]
        assert (await client.post("/api/v1/purchase-orders", json=payload, headers={"Idempotency-Key": uuid4().hex})).status_code == 409
        source = (await client.get("/api/v1/purchases/requisitions")).json()["items"][0]
        assert source["status"] == "converted"
        assert source["details"]["purchase_order_id"] == result["id"]
        assert (await client.post(f'/api/v1/purchase-orders/{result["id"]}/approve')).status_code == 200
        history = await client.get(f'/api/v1/suppliers/{supplier["id"]}/price-history', params={"product_id": str(supply["product_id"])})
        assert history.status_code == 200, history.text
        assert Decimal(history.json()["items"][0]["unit_cost"]) == 9
        assert history.json()["items"][0]["currency"] == "PEN"
        integrity = await client.get("/api/v1/audit/logs/verify")
        assert integrity.status_code == 200, integrity.text
        assert integrity.json()["is_valid"] is True, integrity.text
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_category_move_updates_subtree_depth_and_archive_undo(supply):
    client = await client_for(supply)
    try:
        async def create(name, parent=None):
            result = await client.post("/api/v1/categories", json={"name": name, "parent_id": parent})
            assert result.status_code == 201, result.text
            return result.json()["id"]
        first = await create("Primera raíz")
        child = await create("Hijo", first)
        leaf = await create("Hoja", child)
        second = await create("Segunda raíz")
        parent = await create("Nuevo padre", second)
        moved = await client.patch(f"/api/v1/categories/{first}", json={"parent_id": parent})
        assert moved.status_code == 200, moved.text
        with sync_session_factory() as db:
            levels = {str(row.id): row.level for row in db.scalars(select(CategoryModel).where(CategoryModel.company_id == supply["company_id"])).all()}
            assert levels[first] == 3 and levels[child] == 4 and levels[leaf] == 5
        assert (await client.patch(f"/api/v1/categories/{second}", json={"parent_id": leaf})).status_code == 409
        deepest = await create("Padre más profundo", parent)
        too_deep = await client.patch(f"/api/v1/categories/{first}", json={"parent_id": deepest})
        assert too_deep.status_code == 409
        archived = await client.post(f"/api/v1/categories/{first}/archive")
        assert set(archived.json()["archived_ids"]) == {first, child, leaf}
        invalid = await client.post(f"/api/v1/categories/{first}/restore", json={"category_ids": [first, second]})
        assert invalid.status_code == 409
        restored = await client.post(f"/api/v1/categories/{first}/restore", json={"category_ids": archived.json()["archived_ids"]})
        assert restored.status_code == 200, restored.text
        assert restored.json()["restored_categories"] == 3
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_replenishment_respects_warehouse_and_ignores_inactive_rules(supply):
    client = await client_for(supply)
    try:
        rule = await client.post("/api/v1/inventory/rules", json={"warehouse_id": str(supply["destination"]), "product_id": str(supply["product_id"]), "min_quantity": "5", "max_quantity": "20", "reorder_point": "7", "reorder_quantity": "12"})
        assert rule.status_code == 201, rule.text
        result = await client.get("/api/v1/purchases/replenishment-suggestions", params={"warehouse_id": str(supply["destination"])})
        item = result.json()["suggestions"][0]
        assert Decimal(item["current_available"]) == 0
        assert Decimal(item["suggested_quantity"]) == 12
        assert item["warehouse_id"] == str(supply["destination"])
        await client.post(f'/api/v1/inventory/rules/{rule.json()["id"]}/deactivate')
        result = await client.get("/api/v1/purchases/replenishment-suggestions", params={"warehouse_id": str(supply["destination"])})
        assert Decimal(result.json()["suggestions"][0]["suggested_quantity"]) == 0
    finally:
        await client.aclose()
