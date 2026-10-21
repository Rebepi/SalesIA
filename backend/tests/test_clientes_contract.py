import json
from pathlib import Path

from salesia.main import app
from salesia.modules.clientes.infrastructure.models import CustomerModel
from salesia.shared.infrastructure.models import CustomerModel as SharedCustomerModel


def test_clientes_preserves_public_api_and_route_order():
    assert CustomerModel is SharedCustomerModel
    expected = json.loads((Path(__file__).parent / "contracts/clientes_api.json").read_text(encoding="utf-8"))
    prefixes = ("/api/v1/customers", "/api/v1/crm", "/api/v1/customer-portal")
    schema = app.openapi()
    paths = {path: operations for path, operations in schema["paths"].items() if path.startswith(prefixes)}
    assert paths == expected["paths"]
    for name, definition in expected["schemas"].items():
        assert schema["components"]["schemas"][name] == definition, name
    routes = [
        {"path": route.path, "methods": sorted(route.methods)}
        for route in app.routes
        if hasattr(route, "methods") and route.path.startswith(prefixes)
    ]
    assert routes == expected["route_order"]
