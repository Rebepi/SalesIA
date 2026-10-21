import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from sqlalchemy import func, select
from test_supply_chain_integrity import supply, client_for
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.infrastructure_models import InventoryLot, InventoryQuarantine, InventorySerial, SupplyDocument
from salesia.modules.operaciones.infrastructure_models import UploadGrant
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, UserModel


async def order_for(client, supply, lines):
    supplier = await client.post("/api/v1/suppliers", json={"tax_id": uuid4().hex, "legal_name": "Proveedor de recepción"})
    result = await client.post("/api/v1/purchase-orders", headers={"Idempotency-Key": uuid4().hex}, json={"supplier_id": supplier.json()["id"], "warehouse_id": str(supply["source"]), "items": lines})
    assert result.status_code == 201, result.text
    return result.json()


def tracked_product(supply, tracking):
    with sync_session_factory() as db:
        prod = ProductModel(company_id=supply["company_id"], sku=tracking, name=f"Artículo {tracking}", category="General", unit_of_measure="NIU", unit_price=Decimal("50"), unit_cost=Decimal("3"), tax_rate=Decimal("0.18"))
        db.add(prod)
        db.flush()
        db.add(ProductProfileModel(company_id=supply["company_id"], product_id=prod.id, tracking_mode=tracking))
        db.commit()
        return str(prod.id)


@pytest.mark.asyncio
async def test_multiline_receipt_records_lots_quality_and_releases_serials_at_purchase_cost(supply, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "private_storage_path", str(tmp_path))
    lot_product = tracked_product(supply, "LOT")
    serial_product = tracked_product(supply, "SERIAL")
    client = await client_for(supply)
    try:
        lines = [{"product_id": lot_product, "quantity": "5", "unit_cost": "9"}, {"product_id": serial_product, "quantity": "2", "unit_cost": "25"}, {"product_id": str(supply["product_id"]), "quantity": "4", "unit_cost": "6"}]
        order = await order_for(client, supply, lines)
        context = (await client.get(f'/api/v1/purchase-orders/{order["id"]}/receiving-context')).json()
        assert {item["tracking_mode"] for item in context["lines"]} == {"LOT", "SERIAL", "NONE"}
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jNZYAAAAASUVORK5CYII=")
        intent = await client.post("/api/v1/attachments/upload-intents", json={"file_name": "evidencia.png", "mime_type": "image/png", "file_size_bytes": len(png), "related_entity_type": "purchase_order", "related_entity_id": order["id"]})
        assert intent.status_code == 201, intent.text
        upload = intent.json()
        assert (await client.put(upload["upload_url"], content=png, headers={"X-Upload-Token": upload["upload_token"], "Content-Type": "image/png"})).status_code == 200
        assert (await client.post(f'/api/v1/attachments/{upload["attachment_id"]}/complete')).status_code == 200
        payload = {"purchase_order_id": order["id"], "warehouse_id": str(supply["source"]), "order_version": context["version"], "attachment_ids": [upload["attachment_id"]], "notes": "Guía 123", "items": [{**lines[0], "quantity": "2", "inspection_status": "accepted", "lots": [{"lot_code": "LOTE-1", "quantity": "2", "manufacture_date": "2026-01-01", "expiration_date": "2099-01-01"}]}, {**lines[1], "inspection_status": "quarantine", "inspection_notes": "Verificar funcionamiento", "serial_numbers": ["SER-A", "SER-B"]}, {**lines[2], "quantity": "1", "inspection_status": "rejected", "inspection_notes": "Daño en embalaje"}]}
        key = {"Idempotency-Key": uuid4().hex}
        result = await client.post("/api/v1/goods-receipts", headers=key, json=payload)
        assert result.status_code == 201, result.text
        receipt = result.json()
        assert receipt["status"] == "mixed"
        assert receipt["details"]["attachments"][0]["file_name"] == "evidencia.png"
        assert (await client.post("/api/v1/goods-receipts", headers=key, json=payload)).json()["id"] == receipt["id"]
        with sync_session_factory() as db:
            assert db.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == UUID(lot_product))) == 2
            assert db.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == supply["product_id"])) == 10
            assert {row.status for row in db.scalars(select(InventorySerial).where(InventorySerial.company_id == supply["company_id"])).all()} == {"IN_QUARANTINE"}
            quarantine = db.scalar(select(InventoryQuarantine).where(InventoryQuarantine.company_id == supply["company_id"]))
            quarantine_id = str(quarantine.id)
            grant = db.get(UploadGrant, UUID(upload["attachment_id"]))
            grant.expires_at = datetime.now(timezone.utc) - timedelta(days=2)
            db.commit()
        assert (await client.get(f'/api/v1/attachments/{upload["attachment_id"]}/download')).status_code == 200
        charged = await client.post(f'/api/v1/goods-receipts/{receipt["id"]}/landed-cost', json={"charges": [{"charge_type": "FREIGHT", "amount": "9", "allocation_method": "QUANTITY"}]}, headers={"Idempotency-Key": uuid4().hex})
        assert charged.status_code == 201, charged.text
        costs = {line["product_id"]: Decimal(line["new_unit_cost"]) for line in charged.json()["lines"]}
        assert costs[serial_product] == 25 and costs[lot_product] == Decimal("13.5")
        released = await client.post(f"/api/v1/inventory/quarantine/{quarantine_id}/classify", json={"action": "RESTOCK", "notes": "Verificado"})
        assert released.status_code == 200, released.text
        with sync_session_factory() as db:
            stock = db.scalar(select(InventoryStockModel).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == UUID(serial_product)))
            assert stock.physical_quantity == 2 and stock.average_cost == 25
            assert {row.status for row in db.scalars(select(InventorySerial).where(InventorySerial.company_id == supply["company_id"])).all()} == {"IN_STOCK"}
            assert db.scalar(select(func.count()).select_from(SupplyDocument).where(SupplyDocument.company_id == supply["company_id"], SupplyDocument.kind == "GOODS_RECEIPT")) == 1
        with sync_session_factory() as db:
            serial_id = str(db.scalar(select(InventorySerial.id).where(InventorySerial.company_id == supply["company_id"], InventorySerial.serial_number == "SER-A")))
            lot_id = str(db.scalar(select(InventoryLot.id).where(InventoryLot.company_id == supply["company_id"], InventoryLot.lot_code == "LOTE-1")))
        serial_trace = await client.get(f"/api/v1/inventory/serials/{serial_id}/trace")
        assert serial_trace.status_code == 200, serial_trace.text
        assert serial_trace.json()["sku"] == "SERIAL"
        assert "Cuarentena liberada a stock" in {event["title"] for event in serial_trace.json()["events"]}
        lot_trace = await client.get(f"/api/v1/inventory/lots/{lot_id}/trace")
        assert lot_trace.status_code == 200, lot_trace.text
        assert "Recepción aceptada" in {event["title"] for event in lot_trace.json()["events"]}
        assert (await client.get(f"/api/v1/inventory/lots/{uuid4()}/trace")).status_code == 404
        stale = await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)
        assert stale.status_code == 409
        context = (await client.get(f'/api/v1/purchase-orders/{order["id"]}/receiving-context')).json()
        balances = {line["product_id"]: line for line in context["lines"]}
        serial_returnable = next(item for item in context["receipts"][0]["returnable_lines"] if item["product_id"] == serial_product)
        assert Decimal(serial_returnable["returnable_quantity"]) == 2
        assert Decimal(balances[lot_product]["pending_quantity"]) == 3
        assert Decimal(balances[str(supply["product_id"])]["pending_quantity"]) == 4
        assert Decimal(balances[str(supply["product_id"])]["rejected_quantity"]) == 1
        assert len(context["receipts"]) == 1
        with sync_session_factory() as db:
            db.get(UserModel, supply["user_id"]).role = "sales_rep"
            db.commit()
        assert (await client.get(f'/api/v1/attachments/{upload["attachment_id"]}/download')).status_code == 403
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_receipt_tracking_validation_rolls_back_all_lines_and_rejects_duplicate_serials(supply):
    serial_product = tracked_product(supply, "SERIAL")
    client = await client_for(supply)
    try:
        lines = [{"product_id": str(supply["product_id"]), "quantity": "4", "unit_cost": "6"}, {"product_id": serial_product, "quantity": "2", "unit_cost": "25"}]
        order = await order_for(client, supply, lines)
        payload = {"purchase_order_id": order["id"], "warehouse_id": str(supply["source"]), "items": lines}
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 422
        with sync_session_factory() as db:
            assert db.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == supply["product_id"])) == 10
            assert db.scalar(select(func.count()).select_from(SupplyDocument).where(SupplyDocument.company_id == supply["company_id"], SupplyDocument.kind == "GOODS_RECEIPT")) == 0
        payload["items"][1]["serial_numbers"] = ["SAME", "SAME"]
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 422
        payload["items"][1]["serial_numbers"] = ["S1", "S2"]
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 201
        other_order = await order_for(client, supply, [lines[1]])
        repeated = await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json={"purchase_order_id": other_order["id"], "warehouse_id": str(supply["source"]), "items": [payload["items"][1]]})
        assert repeated.status_code == 409
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_expired_lot_capacity_and_foreign_evidence_cannot_enter_stock(supply):
    lot_product = tracked_product(supply, "LOT")
    client = await client_for(supply)
    try:
        line = {"product_id": lot_product, "quantity": "2", "unit_cost": "9", "lots": [{"lot_code": "EXPIRED", "quantity": "2", "expiration_date": "2000-01-01"}]}
        order = await order_for(client, supply, [{key: value for key, value in line.items() if key != "lots"}])
        payload = {"purchase_order_id": order["id"], "warehouse_id": str(supply["source"]), "items": [line]}
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 409
        with sync_session_factory() as db:
            assert db.scalar(select(func.count()).select_from(InventoryLot).where(InventoryLot.company_id == supply["company_id"])) == 0
        line["lots"][0]["expiration_date"] = "2099-01-01"
        location = await client.post("/api/v1/inventory/locations", json={"warehouse_id": str(supply["source"]), "code": "SMALL", "aisle": "1", "rack": "1", "shelf": "1", "bin": "1", "capacity_units": "1"})
        line["location_id"] = location.json()["id"]
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 409
        del line["location_id"]
        payload["attachment_ids"] = [str(uuid4())]
        assert (await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 422
        with sync_session_factory() as db:
            assert db.scalar(select(func.count()).select_from(InventoryStockModel).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == UUID(lot_product))) == 0
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_supplier_return_limits_serials_and_replays_without_duplicate_stock(supply):
    serial_product = tracked_product(supply, "SERIAL")
    client = await client_for(supply)
    try:
        line = {"product_id": serial_product, "quantity": "2", "unit_cost": "25"}
        order = await order_for(client, supply, [line])
        received = await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json={"purchase_order_id": order["id"], "warehouse_id": str(supply["source"]), "items": [{**line, "serial_numbers": ["RET-1", "RET-2"]}]})
        assert received.status_code == 201, received.text
        payload = {"goods_receipt_id": received.json()["id"], "warehouse_id": str(supply["source"]), "reason": "Devolución acordada", "items": [{"product_id": serial_product, "quantity": "1", "serial_numbers": ["RET-1"]}]}
        key = {"Idempotency-Key": uuid4().hex}
        returned = await client.post("/api/v1/purchases/returns", headers=key, json=payload)
        assert returned.status_code == 201, returned.text
        assert (await client.post("/api/v1/purchases/returns", headers=key, json=payload)).json()["id"] == returned.json()["id"]
        assert (await client.post("/api/v1/purchases/returns", headers={"Idempotency-Key": uuid4().hex}, json=payload)).status_code == 409
        with sync_session_factory() as db:
            assert db.scalar(select(InventoryStockModel.physical_quantity).where(InventoryStockModel.company_id == supply["company_id"], InventoryStockModel.product_id == UUID(serial_product))) == 1
            statuses = {row.serial_number: row.status for row in db.scalars(select(InventorySerial).where(InventorySerial.company_id == supply["company_id"])).all()}
            assert statuses == {"RET-1": "RETURNED_TO_SUPPLIER", "RET-2": "IN_STOCK"}
            serial_id = str(db.scalar(select(InventorySerial.id).where(InventorySerial.company_id == supply["company_id"], InventorySerial.serial_number == "RET-1")))
        trace = await client.get(f"/api/v1/inventory/serials/{serial_id}/trace")
        assert "Devolución al proveedor" in {event["title"] for event in trace.json()["events"]}
        context = (await client.get(f'/api/v1/purchase-orders/{order["id"]}/receiving-context')).json()
        assert Decimal(context["receipts"][0]["returnable_lines"][0]["returnable_quantity"]) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_landed_cost_is_idempotent_and_expected_supplier_credit_excludes_freight(supply):
    client = await client_for(supply)
    try:
        line = {"product_id": str(supply["product_id"]), "quantity": "2", "unit_cost": "10"}
        order = await order_for(client, supply, [line])
        receipt = await client.post("/api/v1/goods-receipts", headers={"Idempotency-Key": uuid4().hex}, json={"purchase_order_id": order["id"], "warehouse_id": str(supply["source"]), "items": [line]})
        receipt_id = receipt.json()["id"]
        payload = {"charges": [{"charge_type": "FREIGHT", "amount": "6", "allocation_method": "QUANTITY"}]}
        key = {"Idempotency-Key": uuid4().hex}
        charged = await client.post(f"/api/v1/goods-receipts/{receipt_id}/landed-cost", headers=key, json=payload)
        assert charged.status_code == 201, charged.text
        repeated = await client.post(f"/api/v1/goods-receipts/{receipt_id}/landed-cost", headers=key, json=payload)
        assert repeated.json() == charged.json()
        assert Decimal(charged.json()["lines"][0]["new_unit_cost"]) == 13
        returned = await client.post("/api/v1/purchases/returns", headers={"Idempotency-Key": uuid4().hex}, json={"goods_receipt_id": receipt_id, "warehouse_id": str(supply["source"]), "reason": "Mercadería devuelta", "items": [{"product_id": str(supply["product_id"]), "quantity": "1"}]})
        assert returned.status_code == 201, returned.text
        assert Decimal(returned.json()["details"]["expected_credit_note_amount"]) == 10
    finally:
        await client.aclose()
