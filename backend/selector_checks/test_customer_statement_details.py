from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from salesia.modules.clientes.application.estado_cuenta import get_customer_statement


@pytest.mark.parametrize("sensitive", [True, False])
def test_statement_exposes_purchase_currency_and_preserves_sensitive_redaction(sensitive):
    company_id, customer_id = uuid4(), uuid4()
    user = SimpleNamespace(company_id=company_id, role="company_admin" if sensitive else "staff", permissions=[])
    customer = SimpleNamespace(id=customer_id, legal_name="Cliente", doc_number="20123456789", credit_limit=Decimal("100"), current_balance=Decimal("50"))
    sale = SimpleNamespace(id=uuid4(), series="F001", number=1, status="confirmed", currency="PEN", is_credit=True, total_amount=Decimal("100"), paid_amount=Decimal("50"), created_at=datetime(2026, 10, 21, tzinfo=timezone.utc))
    db = Mock()
    db.execute.side_effect = [Mock(scalar_one_or_none=Mock(return_value=customer)), Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=[sale]))))]
    result = get_customer_statement(customer_id, user, db)
    invoice = result["invoices"][0]
    assert invoice["currency"] == "PEN"
    assert invoice["is_credit"] is True
    assert invoice["pending_balance"] == ("50" if sensitive else None)
    assert invoice["total_amount"] == ("100" if sensitive else None)
    sql = str(db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": True}))
    assert str(company_id).replace("-", "") in sql.replace("-", "")
    assert str(customer_id).replace("-", "") in sql.replace("-", "")
