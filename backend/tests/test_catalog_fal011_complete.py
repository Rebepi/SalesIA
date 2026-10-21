import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
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
    PaymentModel,
    InventoryStockModel,
    KardexMovementModel,
    AuditLogModel
)
from salesia.modules.catalogo.infrastructure_models import (
    CategoryModel,
    ProductProfileModel,
    ProductVariantModel,
    ProductBarcodeModel,
    UnitOfMeasureModel,
    UnitConversionModel,
    PriceListModel,
    PriceListItemModel,
    ProductVolumeTierModel,
    PromotionModel,
    CouponModel,
    ProductAttachmentModel,
    ProductKitItemModel,
    ProductWarrantyClaimModel,
    ProductPriceHistoryModel
)
from salesia.shared.infrastructure.transactions import RefundModel
from tests.support.auth_helpers import create_durable_identity

COMPANY_A = UUID("00000000-0000-0000-0000-000000000001")
COMPANY_B = UUID("00000000-0000-0000-0000-000000000009")
BRANCH_A = UUID("00000000-0000-0000-0000-000000000002")
WAREHOUSE_A = UUID("00000000-0000-0000-0000-000000000004")
USER_ADMIN_A = UUID("00000000-0000-0000-0000-000000000003")
USER_SELLER_A = UUID("00000000-0000-0000-0000-000000000005")
USER_ADMIN_B = UUID("00000000-0000-0000-0000-000000000008")


@pytest.fixture(autouse=True, scope="module")
def setup_catalog_test_db():
    Base.metadata.create_all(sync_engine)
    with sync_session_factory() as session:
        for cid, tax in [(COMPANY_A, "20111111111"), (COMPANY_B, "20222222222")]:
            comp = session.execute(select(CompanyModel).where(CompanyModel.id == cid)).scalar_one_or_none()
            if not comp:
                session.add(CompanyModel(
                    id=cid,
                    tax_id=tax,
                    legal_name=f"EMPRESA CATALOGO {tax}",
                    trade_name=f"CATALOG {tax}",
                    base_currency="USD",
                    is_active=True
                ))
        branch = session.execute(select(BranchModel).where(BranchModel.id == BRANCH_A)).scalar_one_or_none()
        if not branch:
            session.add(BranchModel(
                id=BRANCH_A,
                company_id=COMPANY_A,
                code="SUC-CAT-01",
                name="Sucursal Catalogo",
                timezone="America/Lima",
                is_active=True
            ))
        wh = session.execute(select(WarehouseModel).where(WarehouseModel.id == WAREHOUSE_A)).scalar_one_or_none()
        if not wh:
            session.add(WarehouseModel(
                id=WAREHOUSE_A,
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                code="ALM-CAT-01",
                name="Almacen Catalogo",
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
        email="admin@catalog.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def seller_headers():
    identity = create_durable_identity(
        company_id=COMPANY_A,
        user_id=USER_SELLER_A,
        role="salesperson",
        email="seller@catalog.enterprise"
    )
    return identity["headers"]


@pytest.fixture
def admin_b_headers():
    identity = create_durable_identity(
        company_id=COMPANY_B,
        user_id=USER_ADMIN_B,
        role="company_admin",
        email="admin@companyb.enterprise"
    )
    return identity["headers"]


@pytest.mark.asyncio
async def test_cat_001_product_vs_service_mixed_sale_inventory(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sku_phys = f"PHYS-{uuid4().hex[:6].upper()}"
        sku_serv = f"SERV-{uuid4().hex[:6].upper()}"

        res_p = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku_phys,
            "name": "Impresora Fiscal Termica",
            "category": "Equipos",
            "unit_price": 500.0,
            "product_type": "product",
            "track_inventory": True
        })
        assert res_p.status_code == 201
        prod_id = res_p.json()["id"]

        res_s = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku_serv,
            "name": "Instalacion y Configuracion",
            "category": "Servicios",
            "unit_price": 100.0,
            "product_type": "service",
            "track_inventory": False
        })
        assert res_s.status_code == 201
        serv_id = res_s.json()["id"]

        with sync_session_factory() as session:
            stock = InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A,
                product_id=UUID(prod_id),
                physical_quantity=Decimal("10.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)

            cust = CustomerModel(
                id=uuid4(),
                company_id=COMPANY_A,
                code=f"CUST-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Comprador Mixto SAC",
                credit_limit=Decimal("10000.000000"),
                current_balance=Decimal("0.000000"),
                is_active=True
            )
            session.add(cust)
            session.commit()
            cust_id = str(cust.id)

        draft_res = await client.post(
            "/api/v1/sales/draft",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A),
                "warehouse_id": str(WAREHOUSE_A),
                "customer_id": cust_id,
                "currency": "USD",
                "is_credit": False,
                "lines": [
                    {"product_id": prod_id, "sku": sku_phys, "product_name": "Impresora Fiscal", "unit_price": 500.0, "quantity": 2, "discount": 0},
                    {"product_id": serv_id, "sku": sku_serv, "product_name": "Instalacion", "unit_price": 100.0, "quantity": 1, "discount": 0}
                ]
            }
        )
        assert draft_res.status_code == 201
        sale_id = draft_res.json()["sale_id"]

        confirm_res = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={"is_credit_sale": False}
        )
        assert confirm_res.status_code == 200

        with sync_session_factory() as session:
            updated_stock = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == COMPANY_A,
                    InventoryStockModel.warehouse_id == WAREHOUSE_A,
                    InventoryStockModel.product_id == UUID(prod_id)
                )
            ).scalar_one()
            assert updated_stock.physical_quantity == Decimal("8.000000")

            serv_stock = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == COMPANY_A,
                    InventoryStockModel.product_id == UUID(serv_id)
                )
            ).scalar_one_or_none()
            assert serv_stock is None


@pytest.mark.asyncio
async def test_cat_002_variants_attributes_and_duplicate_prevention(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sku = f"POLO-{uuid4().hex[:6].upper()}"
        res = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku,
            "name": "Polo Algodon Pima",
            "category": "Textil",
            "unit_price": 50.0
        })
        prod_id = res.json()["id"]

        v1_res = await client.post(
            f"/api/v1/products/{prod_id}/variants",
            headers=admin_headers,
            json={
                "sku": f"{sku}-AZUL-M",
                "attributes": {"color": "Azul", "talla": "M"},
                "price_delta": 5.0
            }
        )
        assert v1_res.status_code == 201
        v1_id = v1_res.json()["id"]

        dup_res = await client.post(
            f"/api/v1/products/{prod_id}/variants",
            headers=admin_headers,
            json={
                "sku": f"{sku}-AZUL-M-OTRO",
                "attributes": {"color": "Azul", "talla": "M"},
                "price_delta": 5.0
            }
        )
        assert dup_res.status_code == 409

        preview_res = await client.post(
            "/api/v1/prices/preview",
            headers=admin_headers,
            json={"product_id": prod_id, "variant_id": v1_id, "quantity": 1}
        )
        assert preview_res.status_code == 200
        assert Decimal(preview_res.json()["unit_price_base"]) == Decimal("55.000000")


@pytest.mark.asyncio
async def test_cat_003_barcodes_uniqueness_and_scanner_lookup(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        barcode_val = f"775{uuid4().int % 10000000000:010d}"
        sku1 = f"BC1-{uuid4().hex[:6].upper()}"
        p1 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku1,
            "name": "Lector Laser",
            "category": "Hardware",
            "unit_price": 120.0
        })
        p1_id = p1.json()["id"]

        bc_res = await client.post(
            f"/api/v1/products/{p1_id}/barcodes",
            headers=admin_headers,
            json={"barcode": barcode_val, "barcode_type": "CODE128"}
        )
        assert bc_res.status_code == 201

        sku2 = f"BC2-{uuid4().hex[:6].upper()}"
        p2 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku2,
            "name": "Teclado Mecanico",
            "category": "Hardware",
            "unit_price": 90.0
        })
        p2_id = p2.json()["id"]

        dup_bc = await client.post(
            f"/api/v1/products/{p2_id}/barcodes",
            headers=admin_headers,
            json={"barcode": barcode_val}
        )
        assert dup_bc.status_code == 409

        lookup_ok = await client.get(
            f"/api/v1/products/lookup/barcode?code={barcode_val}",
            headers=admin_headers
        )
        assert lookup_ok.status_code == 200
        assert lookup_ok.json()["product_id"] == p1_id

        lookup_unknown = await client.get(
            "/api/v1/products/lookup/barcode?code=9999999999999",
            headers=admin_headers
        )
        assert lookup_unknown.status_code == 404


@pytest.mark.asyncio
async def test_cat_004_hierarchical_categories_tree_and_cycle_prevention(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        c1 = await client.post("/api/v1/categories", headers=admin_headers, json={
            "code": f"ROOT-{uuid4().hex[:4]}",
            "name": "Electronica"
        })
        assert c1.status_code == 201
        c1_id = c1.json()["id"]

        c2 = await client.post("/api/v1/categories", headers=admin_headers, json={
            "code": f"CHILD-{uuid4().hex[:4]}",
            "name": "Computo",
            "parent_id": c1_id
        })
        assert c2.status_code == 201
        c2_id = c2.json()["id"]

        c3 = await client.post("/api/v1/categories", headers=admin_headers, json={
            "code": f"GRAND-{uuid4().hex[:4]}",
            "name": "Laptops",
            "parent_id": c2_id
        })
        assert c3.status_code == 201
        c3_id = c3.json()["id"]

        cycle_res = await client.patch(
            f"/api/v1/categories/{c1_id}",
            headers=admin_headers,
            json={"parent_id": c3_id}
        )
        assert cycle_res.status_code == 409

        reorder_res = await client.patch(
            f"/api/v1/categories/{c3_id}",
            headers=admin_headers,
            json={"parent_id": c1_id}
        )
        assert reorder_res.status_code == 200
        assert reorder_res.json()["parent_id"] == c1_id


@pytest.mark.asyncio
async def test_cat_005_units_and_conversions(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/v1/units", headers=admin_headers, json={
            "code": "BX12",
            "name": "Caja x 12 unidades",
            "allow_fractions": False
        })
        await client.post("/api/v1/units", headers=admin_headers, json={
            "code": "UNID",
            "name": "Unidad simple",
            "allow_fractions": False
        })

        conv_res = await client.post("/api/v1/units/conversions", headers=admin_headers, json={
            "from_unit": "BX12",
            "to_unit": "UNID",
            "factor": 12.0
        })
        assert conv_res.status_code in (201, 409)

        calc = await client.post("/api/v1/units/convert", headers=admin_headers, json={
            "from_unit": "BX12",
            "to_unit": "UNID",
            "quantity": 1
        })
        assert calc.status_code == 200
        assert Decimal(calc.json()["converted_quantity"]) == Decimal("12.000000")
        assert Decimal(calc.json()["converted_quantity"]) - Decimal("3.000000") == Decimal("9.000000")


@pytest.mark.asyncio
async def test_cat_006_fractional_quantities_validation(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        p_kg = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"KG-{uuid4().hex[:6].upper()}",
            "name": "Clavos de Acero a Granel",
            "category": "Ferreteria",
            "unit_of_measure": "KGM",
            "unit_price": 10.0
        })
        p_kg_id = p_kg.json()["id"]

        p_unit = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"SER-{uuid4().hex[:6].upper()}",
            "name": "Generador Diesel",
            "category": "Maquinaria",
            "unit_of_measure": "NIU",
            "unit_price": 5000.0
        })
        p_unit_id = p_unit.json()["id"]

        preview_kg = await client.post("/api/v1/prices/preview", headers=admin_headers, json={
            "product_id": p_kg_id,
            "quantity": 0.5
        })
        assert preview_kg.status_code == 200
        assert Decimal(preview_kg.json()["final_unit_price"]) == Decimal("10.000000")

        preview_serial = await client.post("/api/v1/prices/preview", headers=admin_headers, json={
            "product_id": p_unit_id,
            "quantity": 0.5
        })
        assert preview_serial.status_code == 409


@pytest.mark.asyncio
async def test_cat_007_price_lists_priority_and_deterministic_explanation(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"PL-{uuid4().hex[:6].upper()}",
            "name": "Switch Cisco 24 Puertos",
            "category": "Redes",
            "unit_price": 1000.0
        })
        prod_id = prod.json()["id"]

        pl_low = await client.post("/api/v1/price-lists", headers=admin_headers, json={
            "code": f"PL-STD-{uuid4().hex[:4]}",
            "name": "Lista Minorista",
            "priority": 10
        })
        pl_low_id = pl_low.json()["id"]
        await client.post(f"/api/v1/price-lists/{pl_low_id}/items", headers=admin_headers, json={
            "product_id": prod_id,
            "discount_percentage": 0.05
        })

        pl_high = await client.post("/api/v1/price-lists", headers=admin_headers, json={
            "code": f"PL-VIP-{uuid4().hex[:4]}",
            "name": "Lista Distribuidor VIP",
            "priority": 50
        })
        pl_high_id = pl_high.json()["id"]
        await client.post(f"/api/v1/price-lists/{pl_high_id}/items", headers=admin_headers, json={
            "product_id": prod_id,
            "discount_percentage": 0.20
        })

        preview = await client.post("/api/v1/prices/preview", headers=admin_headers, json={
            "product_id": prod_id,
            "quantity": 1
        })
        assert preview.status_code == 200
        data = preview.json()
        assert Decimal(data["final_unit_price"]) == Decimal("800.000000")
        assert len(data["rules_applied"]) >= 1
        assert data["rules_applied"][0]["name"] == "Lista Distribuidor VIP"


@pytest.mark.asyncio
async def test_cat_008_price_versioning_and_snapshot_immutability(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"VERS-{uuid4().hex[:6].upper()}",
            "name": "Tablet Industrial",
            "category": "Movil",
            "unit_price": 500.0
        })
        prod_id = prod.json()["id"]

        with sync_session_factory() as session:
            cust = CustomerModel(
                id=uuid4(),
                company_id=COMPANY_A,
                code=f"C-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Comprador Historico SAC",
                is_active=True
            )
            session.add(cust)
            sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                customer_id=cust.id,
                series="F001",
                number=uuid4().int % 100000,
                status="confirmed",
                currency="USD",
                total_amount=Decimal("590.000000")
            )
            session.add(sale)
            line = SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale.id,
                product_id=UUID(prod_id),
                line_number=1,
                sku_snapshot="VERS-OLD",
                name_snapshot="Tablet Industrial",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("1.000000"),
                unit_price_snapshot=Decimal("500.000000"),
                unit_cost_snapshot=Decimal("300.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("500.000000"),
                tax_amount=Decimal("90.000000"),
                total_amount=Decimal("590.000000")
            )
            session.add(line)
            session.commit()
            line_id = line.id

        patch_res = await client.patch(
            f"/api/v1/products/{prod_id}",
            headers=admin_headers,
            json={"unit_price": 750.0}
        )
        assert patch_res.status_code == 200

        with sync_session_factory() as session:
            persisted = session.execute(
                select(SaleLineModel).where(SaleLineModel.id == line_id)
            ).scalar_one()
            assert persisted.unit_price_snapshot == Decimal("500.000000")

            history = session.execute(
                select(ProductPriceHistoryModel).where(
                    ProductPriceHistoryModel.product_id == UUID(prod_id)
                )
            ).scalars().all()
            assert len(history) >= 1
            assert history[0].old_price == Decimal("500.000000")
            assert history[0].new_price == Decimal("750.000000")


@pytest.mark.asyncio
async def test_cat_009_discounts_role_limits_and_negative_total_prevention(seller_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/sales/draft",
            headers={**seller_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A),
                "warehouse_id": str(WAREHOUSE_A),
                "customer_id": str(uuid4()),
                "currency": "USD",
                "is_credit": False,
                "lines": [
                    {"sku": "SKU-ANY", "quantity": 1, "discount": 9999}
                ]
            }
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_cat_010_taxes_subtotal_discount_base_tax_total_match(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"TAX-{uuid4().hex[:6].upper()}",
            "name": "Panel Solar 450W",
            "category": "Energia",
            "unit_price": 200.0,
            "tax_rate": 0.18
        })
        prod_id = prod.json()["id"]

        preview = await client.post("/api/v1/prices/preview", headers=admin_headers, json={
            "product_id": prod_id,
            "quantity": 10
        })
        assert preview.status_code == 200
        p = preview.json()
        assert Decimal(p["final_unit_price"]) == Decimal("190.000000")
        assert Decimal(p["subtotal"]) == Decimal("1900.000000")
        assert Decimal(p["tax_amount"]) == Decimal("342.000000")
        assert Decimal(p["total_estimated"]) == Decimal("2242.000000")


@pytest.mark.asyncio
async def test_cat_011_promotions_combinable_and_quota_limits(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"PRM-{uuid4().hex[:6].upper()}",
            "name": "Router Inalambrico Mesh",
            "category": "Redes",
            "unit_price": 100.0
        })
        prod_id = prod.json()["id"]

        now = datetime.now(timezone.utc)
        p1 = await client.post("/api/v1/promotions", headers=admin_headers, json={
            "name": "Promo Verano 10%",
            "code": f"VER-{uuid4().hex[:4]}",
            "priority": 10,
            "is_exclusive": False,
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=1)).isoformat(),
            "product_id": prod_id,
            "discount_percentage": 0.10,
            "max_quota": 5
        })
        assert p1.status_code == 201

        p2 = await client.post("/api/v1/promotions", headers=admin_headers, json={
            "name": "Promo Flash 5%",
            "code": f"FLA-{uuid4().hex[:4]}",
            "priority": 5,
            "is_exclusive": False,
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=1)).isoformat(),
            "product_id": prod_id,
            "discount_percentage": 0.05,
            "max_quota": 5
        })
        assert p2.status_code == 201

        preview = await client.post("/api/v1/prices/preview", headers=admin_headers, json={
            "product_id": prod_id,
            "quantity": 1
        })
        assert preview.status_code == 200
        rules = preview.json()["rules_applied"]
        assert len(rules) == 2
        assert Decimal(preview.json()["final_unit_price"]) == Decimal("85.500000")


@pytest.mark.asyncio
async def test_cat_012_coupons_normalization_and_atomic_consumption(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        now = datetime.now(timezone.utc)
        code = f"DESC-{uuid4().hex[:6].upper()}"
        res = await client.post("/api/v1/coupons", headers=admin_headers, json={
            "code": f"  {code.lower()}  ",
            "discount_type": "PERCENTAGE",
            "discount_value": 0.15,
            "min_purchase_amount": 50.0,
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=1)).isoformat(),
            "max_uses": 2
        })
        assert res.status_code == 201
        assert res.json()["code"] == code

        val = await client.post("/api/v1/coupons/validate", headers=admin_headers, json={
            "code": code.lower(),
            "amount": 100.0
        })
        assert val.status_code == 200
        assert val.json()["valid"] is True
        assert Decimal(val.json()["calculated_discount"]) == Decimal("15.000000")


@pytest.mark.asyncio
async def test_cat_013_restricted_costs_hidden_from_seller(seller_headers, admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"CST-{uuid4().hex[:6].upper()}",
            "name": "Camara de Seguridad PTZ",
            "category": "CCTV",
            "unit_price": 250.0,
            "unit_cost": 150.0
        })
        prod_id = prod.json()["id"]

        seller_list = await client.get("/api/v1/products", headers=seller_headers)
        assert seller_list.status_code == 200
        for item in seller_list.json()["items"]:
            assert "unit_cost" not in item
            assert "margin_amount" not in item

        seller_get = await client.get(f"/api/v1/products/{prod_id}", headers=seller_headers)
        assert seller_get.status_code == 200
        assert "unit_cost" not in seller_get.json()
        assert "margin_amount" not in seller_get.json()

        seller_preview = await client.post("/api/v1/prices/preview", headers=seller_headers, json={
            "product_id": prod_id,
            "quantity": 1
        })
        assert seller_preview.status_code == 200
        assert "unit_cost" not in seller_preview.json()
        assert "estimated_margin" not in seller_preview.json()

        admin_get = await client.get(f"/api/v1/products/{prod_id}", headers=admin_headers)
        assert admin_get.status_code == 200
        assert admin_get.json()["unit_cost"] == "150.000000"


@pytest.mark.asyncio
async def test_cat_014_catalog_status_archived_blocks_new_sale_allows_refund(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"ARC-{uuid4().hex[:6].upper()}",
            "name": "Modulo Bluetooth v4",
            "category": "Repuestos",
            "unit_price": 80.0
        })
        prod_id = prod.json()["id"]

        with sync_session_factory() as session:
            stock = InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A,
                product_id=UUID(prod_id),
                physical_quantity=Decimal("5.000000"),
                reserved_quantity=Decimal("0.000000")
            )
            session.add(stock)
            cust = CustomerModel(
                id=uuid4(),
                company_id=COMPANY_A,
                code=f"C-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Archivo SAC",
                is_active=True
            )
            session.add(cust)
            sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                warehouse_id=WAREHOUSE_A,
                customer_id=cust.id,
                series="F001",
                number=uuid4().int % 100000,
                status="confirmed",
                currency="USD",
                total_amount=Decimal("94.400000"),
                paid_amount=Decimal("94.400000")
            )
            session.add(sale)
            session.flush()
            line = SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale.id,
                product_id=UUID(prod_id),
                line_number=1,
                sku_snapshot="ARC-OLD",
                name_snapshot="Modulo Bluetooth",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("1.000000"),
                unit_price_snapshot=Decimal("80.000000"),
                unit_cost_snapshot=Decimal("40.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("80.000000"),
                tax_amount=Decimal("14.400000"),
                total_amount=Decimal("94.400000")
            )
            session.add(line)
            pay = PaymentModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale.id,
                amount=Decimal("94.400000"),
                payment_method="CASH",
                status="confirmed"
            )
            session.add(pay)
            session.commit()
            cust_id = str(cust.id)
            pay_id = str(pay.id)

        arch_res = await client.post(f"/api/v1/products/{prod_id}/archive", headers=admin_headers)
        assert arch_res.status_code == 200

        new_sale_fail = await client.post(
            "/api/v1/sales/draft",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A),
                "warehouse_id": str(WAREHOUSE_A),
                "customer_id": cust_id,
                "currency": "USD",
                "is_credit": False,
                "lines": [{"product_id": prod_id, "sku": "ARC-OLD", "product_name": "Modulo", "unit_price": 80.0, "quantity": 1, "discount": 0}]
            }
        )
        assert new_sale_fail.status_code == 422

        refund_res = await client.post(
            "/api/v1/refunds",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={"payment_id": pay_id, "amount": 94.40, "reason": "Devolucion de modulo defectuoso"}
        )
        assert refund_res.status_code in [200, 201]


@pytest.mark.asyncio
async def test_cat_015_images_and_documents_fallback_for_missing(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"IMG-{uuid4().hex[:6].upper()}",
            "name": "Smartwatch Deportivo",
            "category": "Relojes",
            "unit_price": 180.0
        })
        prod_id = prod.json()["id"]

        det = await client.get(f"/api/v1/products/{prod_id}", headers=admin_headers)
        assert det.status_code == 200
        attachments = det.json()["attachments"]
        assert len(attachments) >= 1
        assert "placeholder" in attachments[0]["file_url"]


@pytest.mark.asyncio
async def test_cat_016_search_and_filters_pagination(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cat_unique = f"CAT-{uuid4().hex[:6]}"
        for idx in range(3):
            await client.post("/api/v1/products", headers=admin_headers, json={
                "sku": f"FLT-{uuid4().hex[:6].upper()}",
                "name": f"Item Filtro {idx}",
                "category": cat_unique,
                "unit_price": 100.0 * (idx + 1)
            })

        res_cat = await client.get(f"/api/v1/products?category={cat_unique}&limit=2&offset=0", headers=admin_headers)
        assert res_cat.status_code == 200
        assert len(res_cat.json()["items"]) == 2
        assert res_cat.json()["total_count"] == 3


@pytest.mark.asyncio
async def test_cat_017_bulk_update_preview_and_execution_audit(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cat_bulk = f"BULK-{uuid4().hex[:6]}"
        p1 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"BLK1-{uuid4().hex[:6].upper()}",
            "name": "Cable HDMI 2m",
            "category": cat_bulk,
            "unit_price": 20.0
        })
        p2 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"BLK2-{uuid4().hex[:6].upper()}",
            "name": "Cable HDMI 5m",
            "category": cat_bulk,
            "unit_price": 40.0
        })

        preview_res = await client.post("/api/v1/products/bulk-update", headers=admin_headers, json={
            "filters": {"category": cat_bulk},
            "operation": {"type": "PERCENTAGE_PRICE_ADJUSTMENT", "value": "10.0"},
            "preview": True
        })
        assert preview_res.status_code == 200
        assert preview_res.json()["is_preview"] is True
        assert preview_res.json()["total_affected"] == 2

        chk = await client.get(f"/api/v1/products/{p1.json()['id']}", headers=admin_headers)
        assert Decimal(chk.json()["unit_price"]) == Decimal("20.000000")

        apply_res = await client.post("/api/v1/products/bulk-update", headers=admin_headers, json={
            "filters": {"category": cat_bulk},
            "operation": {"type": "PERCENTAGE_PRICE_ADJUSTMENT", "value": "10.0"},
            "preview": False
        })
        assert apply_res.status_code == 200
        assert apply_res.json()["is_preview"] is False

        chk2 = await client.get(f"/api/v1/products/{p1.json()['id']}", headers=admin_headers)
        assert Decimal(chk2.json()["unit_price"]) == Decimal("22.000000")


@pytest.mark.asyncio
async def test_cat_018_catalog_import_atomic_rollback(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sku_good = f"IMP-OK-{uuid4().hex[:6].upper()}"
        sku_bad = f"IMP-BAD-{uuid4().hex[:6].upper()}"

        bad_batch = await client.post("/api/v1/products/import", headers=admin_headers, json={
            "items": [
                {"sku": sku_good, "name": "Item Valido", "category": "General", "unit_price": 100.0},
                {"sku": sku_bad, "name": "Item Invalido", "category": "General", "unit_price": -50.0}
            ]
        })
        assert bad_batch.status_code in [409, 422]

        search_good = await client.get(f"/api/v1/products?search={sku_good}", headers=admin_headers)
        assert search_good.json()["total_count"] == 0

        good_batch = await client.post("/api/v1/products/import", headers=admin_headers, json={
            "items": [
                {"sku": sku_good, "name": "Item Valido", "category": "General", "unit_price": 100.0}
            ]
        })
        assert good_batch.status_code == 201
        assert good_batch.json()["total_imported"] == 1


@pytest.mark.asyncio
async def test_cat_019_kits_and_combos_atomic_stock_reservation(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        c1 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"CMP1-{uuid4().hex[:6].upper()}",
            "name": "Teclado Inalambrico",
            "category": "Perifericos",
            "unit_price": 60.0
        })
        c1_id = c1.json()["id"]

        c2 = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"CMP2-{uuid4().hex[:6].upper()}",
            "name": "Mouse Inalambrico",
            "category": "Perifericos",
            "unit_price": 30.0
        })
        c2_id = c2.json()["id"]

        kit = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"KIT-{uuid4().hex[:6].upper()}",
            "name": "Combo Escritorio Wireless",
            "category": "Combos",
            "unit_price": 75.0,
            "is_kit": True
        })
        kit_id = kit.json()["id"]

        await client.post(f"/api/v1/products/{kit_id}/kit-items", headers=admin_headers, json={
            "component_product_id": c1_id,
            "quantity": 1
        })
        await client.post(f"/api/v1/products/{kit_id}/kit-items", headers=admin_headers, json={
            "component_product_id": c2_id,
            "quantity": 1
        })

        with sync_session_factory() as session:
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A,
                product_id=UUID(c1_id),
                physical_quantity=Decimal("10.000000"),
                reserved_quantity=Decimal("0.000000")
            ))
            session.add(InventoryStockModel(
                id=uuid4(),
                company_id=COMPANY_A,
                warehouse_id=WAREHOUSE_A,
                product_id=UUID(c2_id),
                physical_quantity=Decimal("0.000000"),
                reserved_quantity=Decimal("0.000000")
            ))
            cust = CustomerModel(
                id=uuid4(),
                company_id=COMPANY_A,
                code=f"C-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Cliente Kit SAC",
                is_active=True
            )
            session.add(cust)
            session.commit()
            cust_id = str(cust.id)

        draft = await client.post(
            "/api/v1/sales/draft",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={
                "branch_id": str(BRANCH_A),
                "warehouse_id": str(WAREHOUSE_A),
                "customer_id": cust_id,
                "currency": "USD",
                "is_credit": False,
                "lines": [{"product_id": kit_id, "sku": f"KIT-TEST", "product_name": "Combo Escritorio", "unit_price": 75.0, "quantity": 1, "discount": 0}]
            }
        )
        assert draft.status_code == 201
        sale_id = draft.json()["sale_id"]

        confirm_fail = await client.post(
            f"/api/v1/sales/{sale_id}/confirm",
            headers={**admin_headers, "Idempotency-Key": uuid4().hex},
            json={"is_credit_sale": False}
        )
        assert confirm_fail.status_code == 409

        with sync_session_factory() as session:
            stock_c1 = session.execute(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == COMPANY_A,
                    InventoryStockModel.warehouse_id == WAREHOUSE_A,
                    InventoryStockModel.product_id == UUID(c1_id)
                )
            ).scalar_one()
            assert stock_c1.physical_quantity == Decimal("10.000000")


@pytest.mark.asyncio
async def test_cat_020_volume_tiers_boundary_tests(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"VLM-{uuid4().hex[:6].upper()}",
            "name": "Resma Papel Bond A4",
            "category": "Papeleria",
            "unit_price": 10.0
        })
        prod_id = prod.json()["id"]

        await client.post(f"/api/v1/products/{prod_id}/volume-tiers", headers=admin_headers, json={
            "min_quantity": 10,
            "discount_percentage": 0.05
        })
        await client.post(f"/api/v1/products/{prod_id}/volume-tiers", headers=admin_headers, json={
            "min_quantity": 50,
            "discount_percentage": 0.10
        })

        p_below_10 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 9})
        assert p_below_10.json()["discount_percentage"] == "0.00"

        p_at_10 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 10})
        assert Decimal(p_at_10.json()["discount_percentage"]) == Decimal("5.00")

        p_above_10 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 11})
        assert Decimal(p_above_10.json()["discount_percentage"]) == Decimal("5.00")

        p_below_50 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 49})
        assert Decimal(p_below_50.json()["discount_percentage"]) == Decimal("5.00")

        p_at_50 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 50})
        assert Decimal(p_at_50.json()["discount_percentage"]) == Decimal("10.00")

        p_above_50 = await client.post("/api/v1/prices/preview", headers=admin_headers, json={"product_id": prod_id, "quantity": 51})
        assert Decimal(p_above_50.json()["discount_percentage"]) == Decimal("10.00")


@pytest.mark.asyncio
async def test_cat_021_commercial_warranty_policy_change_preserves_sold_coverage(admin_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"WAR-{uuid4().hex[:6].upper()}",
            "name": "Servidor Storage NAS",
            "category": "Servidores",
            "unit_price": 3000.0,
            "warranty_period_months": 24,
            "warranty_policy": "Garantia Integral 24 Meses"
        })
        prod_id = prod.json()["id"]

        with sync_session_factory() as session:
            cust = CustomerModel(
                id=uuid4(),
                company_id=COMPANY_A,
                code=f"C-{uuid4().hex[:6]}",
                doc_type="RUC",
                doc_number=f"20{uuid4().int % 1000000000:09d}",
                legal_name="Comprador Storage SAC",
                is_active=True
            )
            session.add(cust)
            sale = SaleModel(
                id=uuid4(),
                company_id=COMPANY_A,
                branch_id=BRANCH_A,
                warehouse_id=WAREHOUSE_A,
                customer_id=cust.id,
                series="F001",
                number=uuid4().int % 100000,
                status="confirmed",
                currency="USD",
                total_amount=Decimal("3540.000000")
            )
            session.add(sale)
            line = SaleLineModel(
                id=uuid4(),
                company_id=COMPANY_A,
                sale_id=sale.id,
                product_id=UUID(prod_id),
                line_number=1,
                sku_snapshot="WAR-SNAPSHOT",
                name_snapshot="Servidor Storage NAS",
                unit_of_measure_snapshot="NIU",
                quantity=Decimal("1.000000"),
                unit_price_snapshot=Decimal("3000.000000"),
                unit_cost_snapshot=Decimal("2000.000000"),
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=Decimal("0.1800"),
                subtotal_amount=Decimal("3000.000000"),
                tax_amount=Decimal("540.000000"),
                total_amount=Decimal("3540.000000")
            )
            session.add(line)
            session.commit()
            sale_id = str(sale.id)

        claim_res = await client.post("/api/v1/products/warranty/claims", headers=admin_headers, json={
            "sale_id": sale_id,
            "product_id": prod_id,
            "serial_number": "SN-NAS-987654",
            "issue_description": "Fallo en fuente de alimentacion secundaria"
        })
        assert claim_res.status_code == 201
        assert claim_res.json()["warranty_period_months_snapshot"] == 24

        await client.patch(f"/api/v1/products/{prod_id}", headers=admin_headers, json={
            "warranty_period_months": 6
        })

        claim_chk = await client.get(f"/api/v1/products/{prod_id}", headers=admin_headers)
        assert claim_chk.json()["warranty_period_months"] == 6


@pytest.mark.asyncio
async def test_api_024_products_get_contract_and_tenant_isolation(admin_headers, admin_b_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_a = await client.get("/api/v1/products?limit=10&offset=0", headers=admin_headers)
        assert res_a.status_code == 200
        assert "items" in res_a.json()
        assert "total_count" in res_a.json()

        res_inv = await client.get("/api/v1/products?limit=500", headers=admin_headers)
        assert res_inv.status_code == 422

        res_b = await client.get("/api/v1/products", headers=admin_b_headers)
        assert res_b.status_code == 200
        for item in res_b.json()["items"]:
            assert item["company_id"] == str(COMPANY_B)


@pytest.mark.asyncio
async def test_api_025_products_post_contract_validation_and_permissions(admin_headers, seller_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sku = f"CR-{uuid4().hex[:6].upper()}"
        res_ok = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku,
            "name": "Microscopio Digital",
            "category": "Laboratorio",
            "unit_price": 450.0
        })
        assert res_ok.status_code == 201

        res_dup = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": sku,
            "name": "Microscopio Duplicado",
            "category": "Laboratorio",
            "unit_price": 460.0
        })
        assert res_dup.status_code == 409

        res_neg = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"NEG-{uuid4().hex[:6]}",
            "name": "Invalido",
            "category": "General",
            "unit_price": -100.0
        })
        assert res_neg.status_code == 422

        res_forbid = await client.post("/api/v1/products", headers=seller_headers, json={
            "sku": f"FORB-{uuid4().hex[:6]}",
            "name": "Sin Permiso",
            "category": "General",
            "unit_price": 100.0
        })
        assert res_forbid.status_code == 403


@pytest.mark.asyncio
async def test_api_026_products_patch_contract_validation_and_permissions(admin_headers, admin_b_headers, seller_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prod = await client.post("/api/v1/products", headers=admin_headers, json={
            "sku": f"PAT-{uuid4().hex[:6].upper()}",
            "name": "Osciloscopio USB",
            "category": "Instrumental",
            "unit_price": 320.0
        })
        prod_id = prod.json()["id"]

        patch_ok = await client.patch(
            f"/api/v1/products/{prod_id}",
            headers=admin_headers,
            json={"name": "Osciloscopio Digital Pro USB"}
        )
        assert patch_ok.status_code == 200
        assert patch_ok.json()["name"] == "Osciloscopio Digital Pro USB"

        patch_seller = await client.patch(
            f"/api/v1/products/{prod_id}",
            headers=seller_headers,
            json={"name": "No Autorizado"}
        )
        assert patch_seller.status_code == 403

        patch_b = await client.patch(
            f"/api/v1/products/{prod_id}",
            headers=admin_b_headers,
            json={"name": "Otra Empresa"}
        )
        assert patch_b.status_code == 403


@pytest.mark.asyncio
async def test_api_027_categories_get_and_post_contract(admin_headers, admin_b_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cats_a = await client.get("/api/v1/categories", headers=admin_headers)
        assert cats_a.status_code == 200
        assert isinstance(cats_a.json(), list)

        code_b = f"CATB-{uuid4().hex[:4]}"
        cat_b = await client.post("/api/v1/categories", headers=admin_b_headers, json={
            "code": code_b,
            "name": "Categoria Empresa B"
        })
        assert cat_b.status_code == 201

        cats_after_a = await client.get("/api/v1/categories", headers=admin_headers)
        codes_a = [c["code"] for c in cats_after_a.json()]
        assert code_b not in codes_a


@pytest.mark.asyncio
async def test_api_028_prices_preview_contract_rules_and_isolation(admin_headers, admin_b_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_id = uuid4()
        res_404 = await client.post(
            "/api/v1/prices/preview",
            headers=admin_headers,
            json={"product_id": str(fake_id), "quantity": 5}
        )
        assert res_404.status_code == 404

        prod_b = await client.post("/api/v1/products", headers=admin_b_headers, json={
            "sku": f"PRVB-{uuid4().hex[:6].upper()}",
            "name": "Servidor Empresa B",
            "category": "TI",
            "unit_price": 5000.0
        })
        prod_b_id = prod_b.json()["id"]

        cross_preview = await client.post(
            "/api/v1/prices/preview",
            headers=admin_headers,
            json={"product_id": prod_b_id, "quantity": 1}
        )
        assert cross_preview.status_code == 403
