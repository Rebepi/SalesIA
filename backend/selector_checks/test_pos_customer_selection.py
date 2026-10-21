from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock
from salesia.modules.clientes.application import consulta, creacion
from salesia.modules.clientes.application.contracts.clientes import CustomerCreateModel
from salesia.modules.clientes.infrastructure.models import CustomerAddressModel


def test_random_customer_suggestions_are_tenant_scoped_and_limited():
    user = SimpleNamespace(company_id=uuid4(), permissions=[], role="company_admin")
    db = Mock()
    db.scalar.return_value = 5000
    db.execute.return_value.scalars.return_value.all.return_value = []
    result = consulta.list_customers(None, None, True, None, 100, 0, None, user, db, order="random")
    sql = str(db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": True}))
    assert "random()" in sql
    assert "LIMIT 5" in sql
    assert "is_active IS true" in sql
    assert "SIN_DOCUMENTO" in sql
    assert str(user.company_id).replace("-", "") in sql.replace("-", "")
    assert result["items"] == []


def test_search_covers_phone_without_loading_all_customers():
    user = SimpleNamespace(company_id=uuid4(), permissions=[], role="company_admin")
    db = Mock()
    db.scalar.return_value = 0
    db.execute.return_value.scalars.return_value.all.return_value = []
    consulta.list_customers("999888777", None, True, None, 10, 0, None, user, db)
    sql = str(db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": True}))
    assert "phone" in sql
    assert "999888777" in sql
    assert "LIMIT 10" in sql


def test_quick_customer_creation_preserves_address_in_same_transaction(monkeypatch):
    user = SimpleNamespace(company_id=uuid4(), user_id=uuid4(), email="admin@example.com", permissions=[], role="company_admin")
    db = Mock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.refresh.side_effect = lambda customer: setattr(customer, "created_at", __import__("datetime").datetime(2026, 10, 21))
    request = CustomerCreateModel(doc_type="RUC", doc_number="20123456789", legal_name="Empresa de prueba", address="Av. Ejemplo 123")
    result = creacion.create_customer(request, user, db)
    addresses = [call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], CustomerAddressModel)]
    assert len(addresses) == 1
    assert addresses[0].street == "Av. Ejemplo 123"
    assert addresses[0].address_type == "fiscal"
    assert addresses[0].company_id == user.company_id
    assert result["address"] == "Av. Ejemplo 123"
    db.commit.assert_called_once()
