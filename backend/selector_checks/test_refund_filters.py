import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import HTTPException
from sqlalchemy import Boolean, Column, DateTime, String, Uuid, create_engine
from sqlalchemy.orm import Session, declarative_base
from salesia.modules.finanzas.application import reembolsos

Base = declarative_base()

class Refund(Base):
    __tablename__ = "filter_refunds"
    id = Column(Uuid, primary_key=True)
    company_id = Column(Uuid)
    payment_id = Column(Uuid)
    amount = Column(String)
    currency = Column(String)
    reason = Column(String)
    status = Column(String)
    provider_reference = Column(String)
    failure_reason = Column(String)
    return_id = Column(Uuid)
    cash_session_id = Column(Uuid)
    unapplied_only = Column(Boolean)
    created_at = Column(DateTime)

class RefundFiltersTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = SimpleNamespace(company_id=uuid4())
        self.patch = patch.object(reembolsos, "RefundModel", Refund)
        self.patch.start()
        self.ids = []
        for company, timestamp, currency, linked, reason in [
            (self.user.company_id, "2026-10-21T04:59:59", "PEN", False, "Anterior"),
            (self.user.company_id, "2026-10-21T05:00:00", "USD", True, "Ajuste 10%"),
            (self.user.company_id, "2026-10-22T04:59:59", "PEN", False, "Corrección"),
            (self.user.company_id, "2026-10-22T05:00:00", "USD", True, "Posterior"),
            (uuid4(), "2026-10-21T15:00:00", "USD", True, "Ajuste 10%")]:
            identifier = uuid4()
            self.ids.append(str(identifier))
            self.db.add(Refund(id=identifier, company_id=company, payment_id=uuid4(), amount="10.00", currency=currency, reason=reason, status="confirmado", return_id=uuid4() if linked else None, created_at=datetime.fromisoformat(timestamp), unapplied_only=False))
        self.db.commit()

    def tearDown(self):
        self.patch.stop()
        self.db.close()
        self.engine.dispose()

    def run_filter(self, **filters):
        return reembolsos.list_refunds(None, None, self.user, self.db, **filters)

    def test_local_day_includes_last_second_and_excludes_next_day(self):
        result = self.run_filter(date_from=date(2026, 10, 21), date_to=date(2026, 10, 21))
        self.assertEqual({row["id"] for row in result}, set(self.ids[1:3]))

    def test_currency_and_return_filters_combine_without_crossing_companies(self):
        result = self.run_filter(currency="USD", linked_return=True, date_to=date(2026, 10, 21))
        self.assertEqual([row["id"] for row in result], [self.ids[1]])
        result = self.run_filter(linked_return=False)
        self.assertEqual({row["id"] for row in result}, {self.ids[0], self.ids[2]})

    def test_search_escapes_wildcards_and_finds_reason_and_identifier(self):
        self.assertEqual([row["id"] for row in self.run_filter(search="10%")], [self.ids[1]])
        self.assertEqual([row["id"] for row in self.run_filter(search=self.ids[2])], [self.ids[2]])

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.run_filter(date_from=date(2026, 10, 22), date_to=date(2026, 10, 21))
        self.assertEqual(error.exception.status_code, 422)

if __name__ == "__main__":
    unittest.main()
