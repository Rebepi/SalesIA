from dataclasses import dataclass
from typing import Any, Optional
from fastapi import HTTPException, status

ALLOWED_OPERATORS = {"eq", "neq", "gt", "gte", "lt", "lte", "in", "like"}

DISALLOWED_SQL_PATTERNS = {
    "select", "insert", "update", "delete", "drop", "truncate", "alter",
    "table", "where", "union", "exec", "declare", "--", ";", "/*", "*/", "or 1=1"
}

MAX_FILTER_CLAUSES = 10
MAX_IN_LIST_SIZE = 50


@dataclass(frozen=True)
class SafeFilterClause:
    field: str
    operator: str
    value: Any


def validate_filter_field(field: str, allowlist: set[str]) -> str:
    if not field or not field.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El nombre del campo de filtrado no puede estar vacio"
        )
    clean_field = field.strip().lower()
    if clean_field not in allowlist:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo no permitido para filtrado: '{field}'. Campos autorizados: {sorted(list(allowlist))}"
        )
    return clean_field


def validate_filter_operator(operator: str) -> str:
    clean_op = operator.strip().lower()
    if clean_op not in ALLOWED_OPERATORS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Operador no soportado: '{operator}'. Operadores permitidos: {sorted(list(ALLOWED_OPERATORS))}"
        )
    return clean_op


def sanitize_filter_value(value: Any) -> Any:
    if isinstance(value, str):
        lower_val = value.lower()
        for pattern in DISALLOWED_SQL_PATTERNS:
            if pattern in lower_val:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Valor de filtro rechazado por contener patrones de riesgo de inyeccion SQL"
                )
    elif isinstance(value, (list, tuple)):
        if len(value) > MAX_IN_LIST_SIZE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tamano de lista excede el maximo permitido ({MAX_IN_LIST_SIZE} elementos)"
            )
        for item in value:
            sanitize_filter_value(item)
    return value


def build_safe_filter(
    filters: list[dict[str, Any]],
    allowlist: set[str]
) -> list[SafeFilterClause]:
    if len(filters) > MAX_FILTER_CLAUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Complejidad de filtrado excede el limite ({MAX_FILTER_CLAUSES} condiciones)"
        )

    clauses: list[SafeFilterClause] = []
    for item in filters:
        field = validate_filter_field(str(item.get("field", "")), allowlist)
        op = validate_filter_operator(str(item.get("operator", "eq")))
        val = sanitize_filter_value(item.get("value"))
        clauses.append(SafeFilterClause(field=field, operator=op, value=val))

    return clauses
