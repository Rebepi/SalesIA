import ast
import hashlib
import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateIndex, CreateTable

from salesia import modules
from salesia.main import app
from salesia.shared.infrastructure.database import Base


def fingerprint(value):
    content = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def expected_contract():
    path = Path(__file__).parent / "contracts/arquitectura.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_architecture_preserves_all_public_operations():
    actual = {
        f"{method.upper()} {path}": fingerprint(operation)
        for path, item in app.openapi()["paths"].items()
        for method, operation in item.items()
    }
    assert actual == expected_contract()["operations"]


def test_architecture_preserves_public_schemas():
    actual = {name: fingerprint(value) for name, value in app.openapi()["components"]["schemas"].items()}
    assert actual == expected_contract()["schemas"]


def test_architecture_preserves_route_dispatch_order():
    actual = [
        {"path": route.path, "methods": sorted(route.methods), "name": route.name}
        for route in app.routes
        if hasattr(route, "methods")
    ]
    assert actual == expected_contract()["routes"]


def test_architecture_preserves_postgresql_tables_and_indexes():
    actual = {
        table.name: fingerprint(
            {
                "ddl": str(CreateTable(table).compile(dialect=dialect())),
                "indexes": sorted(str(CreateIndex(index).compile(dialect=dialect())) for index in table.indexes),
            }
        )
        for table in Base.metadata.sorted_tables
    }
    assert actual == expected_contract()["tables"]


def test_application_layer_does_not_import_http_presentation():
    root = Path(next(iter(modules.__path__)))
    violations = []
    for path in root.glob("*/application/**/*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            targets = []
            if isinstance(node, ast.ImportFrom) and node.module:
                targets.append(node.module)
            elif isinstance(node, ast.Import):
                targets.extend(alias.name for alias in node.names)
            for target in targets:
                if target.startswith("salesia.modules.") and ".presentation" in target:
                    violations.append(f"{path.relative_to(root)}:{node.lineno}:{target}")
    assert not violations, violations


def test_module_files_do_not_collide_with_packages():
    root = Path(next(iter(modules.__path__)))
    collisions = []
    for path in root.rglob("*.py"):
        package = path.with_suffix("")
        if (package / "__init__.py").is_file():
            collisions.append(str(path.relative_to(root)))
    assert not collisions, collisions
