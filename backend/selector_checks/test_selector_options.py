import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, Column, MetaData, String, Table, Uuid, create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from salesia.modules.operaciones.presentation import selector_options as selectors
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db


class SelectorOptionsTests(unittest.TestCase):
    def setUp(self):
        self.company = uuid4()
        self.other_company = uuid4()
        self.actor = uuid4()
        self.metadata = MetaData()
        self.customers = Table("customers", self.metadata, Column("id", Uuid, primary_key=True), Column("company_id", Uuid), Column("legal_name", String), Column("code", String), Column("doc_number", String))
        self.categories = Table("categories", self.metadata, Column("id", Uuid, primary_key=True), Column("company_id", Uuid), Column("name", String), Column("code", String), Column("parent_id", Uuid), Column("is_active", Boolean))
        self.reps = Table("sales_representatives", self.metadata, Column("id", Uuid, primary_key=True), Column("company_id", Uuid), Column("full_name", String), Column("code", String), Column("team", String), Column("user_id", Uuid), Column("supervisor_id", Uuid))
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        self.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.execute(self.customers.insert(), [{"id": uuid4(), "company_id": self.company, "legal_name": f"Cliente {index:05}", "code": f"C{index:05}", "doc_number": str(index)} for index in range(5000)])
        self.db.execute(self.customers.insert(), {"id": uuid4(), "company_id": self.other_company, "legal_name": "Privado", "code": "OTRO", "doc_number": "99999"})
        self.db.commit()
        self.user = AuthenticatedUser(user_id=self.actor, company_id=self.company, email="test@example.test", role="custom", permissions=["customers:read", "sales:read"])
        self.metadata_patch = patch.object(selectors, "Base", SimpleNamespace(metadata=self.metadata))
        self.metadata_patch.start()
        app = FastAPI()
        app.include_router(selectors.router)
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.metadata_patch.stop()
        self.db.close()
        self.engine.dispose()

    def test_five_thousand_rows_are_paged_in_sql(self):
        statements = []
        event.listen(self.engine, "before_cursor_execute", lambda conn, cursor, statement, parameters, context, many: statements.append(statement))
        result = self.client.get("/selector-options/customers").json()
        self.assertEqual(result["total_count"], 5000)
        self.assertEqual(len(result["items"]), 20)
        self.assertTrue(result["has_more"])
        self.assertIn("LIMIT", statements[-1])
        second = self.client.get("/selector-options/customers?offset=20").json()
        self.assertFalse(set(row["value"] for row in result["items"]) & set(row["value"] for row in second["items"]))

    def test_search_finds_rows_outside_initial_page(self):
        result = self.client.get("/selector-options/customers?search=C04999").json()
        self.assertEqual(result["total_count"], 1)
        self.assertIn("04999", result["items"][0]["label"])
        identifier = result["items"][0]["value"]
        resolved = self.client.get(f"/selector-options/customers?ids={identifier}&limit=1").json()
        self.assertEqual(resolved["items"], result["items"])

    def test_tenant_permission_and_limits(self):
        self.assertEqual(self.client.get("/selector-options/customers?search=Privado").json()["items"], [])
        self.assertEqual(self.client.get("/selector-options/customers?limit=5000").status_code, 422)
        self.assertEqual(self.client.get("/selector-options/customers?offset=-1").status_code, 422)
        self.assertEqual(self.client.get("/selector-options/unknown").status_code, 404)
        self.user.permissions = []
        self.assertEqual(self.client.get("/selector-options/customers").status_code, 403)

    def test_representative_team_scope_also_applies_to_selected_ids(self):
        own, colleague, forbidden, supervised = [uuid4() for _ in range(4)]
        self.db.execute(self.reps.insert(), [
            {"id": own, "company_id": self.company, "full_name": "Propio", "code": "R1", "team": "Norte", "user_id": self.actor, "supervisor_id": None},
            {"id": colleague, "company_id": self.company, "full_name": "Equipo", "code": "R2", "team": "Norte", "user_id": uuid4(), "supervisor_id": None},
            {"id": forbidden, "company_id": self.company, "full_name": "Ajeno", "code": "R3", "team": "Sur", "user_id": uuid4(), "supervisor_id": None},
            {"id": supervised, "company_id": self.company, "full_name": "Supervisado", "code": "R4", "team": "Sur", "user_id": uuid4(), "supervisor_id": self.actor},
        ])
        self.db.commit()
        result = self.client.get("/selector-options/sales_reps").json()
        self.assertEqual(result["total_count"], 3)
        self.assertEqual(self.client.get(f"/selector-options/sales_reps?ids={forbidden}").json()["items"], [])
        self.assertEqual(self.client.get("/selector-options/teams").json()["total_count"], 2)

    def test_category_tree_exclusion_is_applied_before_pagination(self):
        root, child, grandchild, sibling = [uuid4() for _ in range(4)]
        self.user.permissions.append("products:read")
        self.db.execute(self.categories.insert(), [
            {"id": root, "company_id": self.company, "name": "Raíz", "code": "A", "parent_id": None, "is_active": True},
            {"id": child, "company_id": self.company, "name": "Hijo", "code": "B", "parent_id": root, "is_active": True},
            {"id": grandchild, "company_id": self.company, "name": "Nieto", "code": "C", "parent_id": child, "is_active": True},
            {"id": sibling, "company_id": self.company, "name": "Hermano", "code": "D", "parent_id": None, "is_active": True},
        ])
        self.db.commit()
        result = self.client.get(f"/selector-options/categories?exclude_subtree={root}&active_only=true").json()
        self.assertEqual([item["value"] for item in result["items"]], [str(sibling)])


if __name__ == "__main__":
    unittest.main()
