from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from salesia.modules.finanzas.application import devoluciones_operaciones
from salesia.modules.finanzas.application.auxiliares import get_sale_eligible_lines
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import ReturnCreateRequest
from salesia.modules.ventas.application.auxiliares.return_summary import sale_return_quantities, sale_return_status, returned_quantity_expression


def test_eligibility_deducts_requested_and_accepted_returns_and_excludes_reserved_serials(monkeypatch):
    company, sale_id, product_id, line_id = uuid4(), uuid4(), uuid4(), uuid4()
    sale = SimpleNamespace(id=sale_id, status="paid")
    line = SimpleNamespace(id=line_id, product_id=product_id, quantity=Decimal("5"), fulfilled_quantity=Decimal("4"), subtotal_amount=Decimal("100"), unit_cost_snapshot=Decimal("5"), discount_amount=Decimal("10"), tax_rate_snapshot=Decimal("0.18"), sku_snapshot="TEC", name_snapshot="Teclado", serial_numbers_json='["A", "B", "C", "D"]')
    previous = [SimpleNamespace(lines=[SimpleNamespace(sale_line_id=line_id, product_id=product_id, quantity=Decimal("1"), serial_numbers_json='["A"]')]), SimpleNamespace(lines=[SimpleNamespace(sale_line_id=line_id, product_id=product_id, quantity=Decimal("1"), serial_numbers_json='["B"]')])]
    db = Mock()
    db.scalar.return_value = sale
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.scalars.side_effect = [Mock(all=Mock(return_value=[line])), Mock(all=Mock(return_value=previous))]
    monkeypatch.setattr(get_sale_eligible_lines, "line_policy", lambda *args: {})
    monkeypatch.setattr(get_sale_eligible_lines, "assess", lambda *args: {})
    monkeypatch.setattr(get_sale_eligible_lines, "business_date", lambda *args: date(2026, 10, 21))
    _, items = get_sale_eligible_lines._get_sale_eligible_lines(db, sale_id, company)
    assert items[0]["eligible_quantity"] == Decimal("2")
    assert items[0]["returned_quantity"] == Decimal("2")
    assert items[0]["net_unit_price"] == Decimal("20")
    assert items[0]["serial_numbers"] == ["C", "D"]
    assert items[0]["allow_fractions"] is False
    assert items[0]["unit_of_measure"] == "NIU"
    sql = str(db.scalars.call_args.args[0].compile(compile_kwargs={"literal_binds": True}))
    assert "requested" in sql and "accepted" in sql
    assert str(company).replace("-", "") in sql.replace("-", "")


def test_actual_request_contract_rejects_old_modal_payload_and_accepts_warehouse_and_line():
    base = {"sale_id": str(uuid4()), "reason": "Artículo devuelto", "items": [{"product_id": str(uuid4()), "quantity": "0.5", "disposition": "STOCK"}]}
    with pytest.raises(ValidationError):
        ReturnCreateRequest.model_validate(base)
    base["warehouse_id"] = str(uuid4())
    base["items"][0].update(disposition="QUARANTINE", sale_line_id=str(uuid4()), condition="damaged", packaging="opened")
    result = ReturnCreateRequest.model_validate(base)
    assert result.items[0].quantity == Decimal("0.5")
    assert result.items[0].disposition == "QUARANTINE"


def test_create_rejects_overreturn_before_any_inventory_or_financial_mutation(monkeypatch):
    sale_id, line_id, product_id = uuid4(), uuid4(), uuid4()
    payload = ReturnCreateRequest(sale_id=sale_id, warehouse_id=uuid4(), reason="Artículo dañado", items=[{"product_id": product_id, "sale_line_id": line_id, "quantity": "2", "disposition": "RESTOCK"}])
    monkeypatch.setattr(devoluciones_operaciones, "claim_request", lambda *args: (None, None))
    monkeypatch.setattr(devoluciones_operaciones, "require_open_period", lambda *args: None)
    monkeypatch.setattr(devoluciones_operaciones, "business_date", lambda *args: date(2026, 10, 21))
    monkeypatch.setattr(devoluciones_operaciones, "_get_sale_eligible_lines", lambda *args: (SimpleNamespace(), [{"sale_line_id": line_id, "product_id": product_id, "eligible_quantity": Decimal("1")}]))
    db = Mock()
    with pytest.raises(HTTPException) as error:
        devoluciones_operaciones.create_return(payload, SimpleNamespace(company_id=uuid4()), db, "create-1")
    assert error.value.status_code == 409
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_sales_return_badges_use_accepted_quantities_and_allocate_legacy_lines_once():
    company, sale_id, product = uuid4(), uuid4(), uuid4()
    first, second = uuid4(), uuid4()
    sale = SimpleNamespace(id=sale_id, status="paid", lines=[SimpleNamespace(id=first, product_id=product, quantity=Decimal("2"), line_number=1), SimpleNamespace(id=second, product_id=product, quantity=Decimal("3"), line_number=2)])
    db = Mock()
    db.scalars.return_value.all.return_value = [SimpleNamespace(sale_id=sale_id, lines=[SimpleNamespace(sale_line_id=None, product_id=product, quantity=Decimal("3"))])]
    quantities = sale_return_quantities(db, company, [sale])[sale_id]
    assert quantities == {first: Decimal("2"), second: Decimal("1")}
    assert sale_return_status(sale, quantities) == "Parcial"
    assert sale_return_status(sale, {first: Decimal("2"), second: Decimal("3")}) == "Total"
    assert sale_return_status(sale, {}) == "Sin devolución"
    db.scalars.return_value.all.return_value[0].lines.append(SimpleNamespace(sale_line_id=first, product_id=product, quantity=Decimal("1")))
    combined = sale_return_quantities(db, company, [sale])[sale_id]
    assert combined == {first: Decimal("2"), second: Decimal("2")}
    sql = str(returned_quantity_expression(company).compile(compile_kwargs={"literal_binds": True}))
    assert "accepted" in sql
    assert str(company).replace("-", "") in sql.replace("-", "")


def test_eligibility_reports_independent_review_from_saved_company_policy(monkeypatch):
    from salesia.modules.seguridad.application import separacion_funciones

    monkeypatch.setattr(devoluciones_operaciones, "_get_sale_eligible_lines", lambda *args: (SimpleNamespace(status="paid", currency="PEN"), []))
    monkeypatch.setattr(devoluciones_operaciones, "business_date", lambda *args: date(2026, 10, 21))
    monkeypatch.setattr(separacion_funciones, "current", lambda *args: {"enabled": {"return_acceptance": True}})
    result = devoluciones_operaciones.get_eligible_return_lines(uuid4(), SimpleNamespace(company_id=uuid4(), permissions=[]), Mock())
    assert result["independent_review_required"] is True
    assert result["can_authorize_exception"] is False


def test_whole_unit_returns_reject_fractions_before_recording(monkeypatch):
    line_id, product_id = uuid4(), uuid4()
    payload = ReturnCreateRequest(sale_id=uuid4(), warehouse_id=uuid4(), reason="Artículo dañado", items=[{"product_id": product_id, "sale_line_id": line_id, "quantity": "0.5"}])
    monkeypatch.setattr(devoluciones_operaciones, "claim_request", lambda *args: (None, None))
    monkeypatch.setattr(devoluciones_operaciones, "require_open_period", lambda *args: None)
    monkeypatch.setattr(devoluciones_operaciones, "business_date", lambda *args: date(2026, 10, 21))
    monkeypatch.setattr(devoluciones_operaciones, "_get_sale_eligible_lines", lambda *args: (SimpleNamespace(), [{"sale_line_id": line_id, "product_id": product_id, "eligible_quantity": Decimal("1"), "allow_fractions": False}]))
    db = Mock()
    with pytest.raises(HTTPException) as error:
        devoluciones_operaciones.create_return(payload, SimpleNamespace(company_id=uuid4()), db, "fraction-1")
    assert error.value.status_code == 422
    assert "cantidad entera" in error.value.detail
    db.add.assert_not_called()
