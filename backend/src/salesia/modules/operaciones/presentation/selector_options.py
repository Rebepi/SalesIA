import unicodedata
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Uuid, func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import Base, get_db

router = APIRouter(prefix="/selector-options", tags=["selector-options"])

RESOURCES = {
    "customers": ("customers", "id", "legal_name", ("code", "doc_number"), ("customers:read",)),
    "products": ("products", "id", "name", ("sku",), ("products:read",)),
    "categories": ("categories", "id", "name", ("code",), ("products:read",)),
    "units": ("units_of_measure", "code", "name", ("code",), ("products:read",)),
    "suppliers": ("suppliers", "id", "legal_name", ("tax_id",), ("purchases:read", "inventory:read")),
    "branches": ("branches", "id", "name", ("code",), ("sales:read", "inventory:read", "organization:manage", "products:read", "analytics:dataset:read", "cash:register:manage", "purchases:read")),
    "warehouses": ("warehouses", "id", "name", ("code",), ("inventory:read", "sales:read", "purchases:read")),
    "sales_reps": ("sales_representatives", "id", "full_name", ("code",), ("sales:read",)),
    "teams": ("sales_representatives", "team", "team", (), ("sales:read",)),
    "approvers": ("users", "id", "full_name", (), ("organization:manage", "approvals:manage")),
    "people": ("users", "id", "full_name", (), ("sales:read", "operations:manage", "approvals:manage", "cash:register:manage", "users:manage", "inventory:read", "organization:manage", "analytics:dataset:read")),
    "locations": ("warehouse_locations", "id", "code", ("code",), ("inventory:read", "purchases:read")),
    "price_lists": ("price_lists", "id", "name", ("code",), ("products:read", "customers:read")),
}


def scoped_query(resource, current_user, db):
    config = RESOURCES.get(resource)
    if not config:
        raise HTTPException(404, "Lista no disponible.")
    table_name, key, label, codes, permissions = config
    if not any(permission in current_user.permissions for permission in permissions):
        raise HTTPException(403, "No tiene permiso para consultar esta lista.")
    table = Base.metadata.tables[table_name]
    fields = [table.c[key].label("value"), table.c[label].label("name")]
    code = next((name for name in codes if name in table.c and name != key), None)
    if code:
        fields.append(table.c[code].label("code"))
    for extra in ("id", "branch_id", "is_active", "allow_fractions", "precision_digits", "timezone"):
        if extra in table.c and resource != "teams":
            fields.append(table.c[extra].label(f"extra_{extra}"))
    query = select(*fields).where(table.c.company_id == current_user.company_id)
    if resource in ("sales_reps", "teams") and "organization:manage" not in current_user.permissions:
        own = db.execute(select(table.c.id, table.c.team).where(table.c.company_id == current_user.company_id, table.c.user_id == current_user.user_id).limit(1)).first()
        access = table.c.supervisor_id == current_user.user_id
        if own:
            access = or_(access, table.c.id == own.id)
            if own.team:
                access = or_(access, table.c.team == own.team)
        query = query.where(access)
    if resource == "approvers":
        from salesia.modules.seguridad.domain.roles import get_role_catalog
        roles = [role.role.value for role in get_role_catalog() if "approvals:manage" in role.permissions]
        custom = Base.metadata.tables["custom_roles"]
        allowed_custom = select(custom.c.role_key).where(custom.c.company_id == current_user.company_id, custom.c.permissions_json.contains('"approvals:manage"', autoescape=True))
        query = query.where(table.c.is_active.is_(True), or_(table.c.role.in_(roles), table.c.role.in_(allowed_custom)))
    if resource == "teams":
        query = query.where(table.c.team.is_not(None), table.c.team != "").distinct()
    return table, query, key, label, codes


def list_selector_options(resource, search, limit, offset, ids, branch_id, warehouse_id, exclude_id, active_only, current_user, db, exclude_subtree=None, selected_value=None):
    table, query, key, label, codes = scoped_query(resource, current_user, db)
    if branch_id and "branch_id" in table.c:
        query = query.where(table.c.branch_id == branch_id)
    if warehouse_id and "warehouse_id" in table.c:
        query = query.where(table.c.warehouse_id == warehouse_id)
    if active_only and "is_active" in table.c:
        query = query.where(table.c.is_active.is_(True))
    def identifier(value):
        if isinstance(table.c[key].type, Uuid):
            try:
                return UUID(value)
            except ValueError:
                raise HTTPException(422, "Identificador de selección inválido.")
        return value
    if exclude_subtree and resource == "categories":
        subtree = select(table.c.id).where(table.c.company_id == current_user.company_id, table.c.id == exclude_subtree).cte("selector_category_subtree", recursive=True)
        subtree = subtree.union(select(table.c.id).where(table.c.company_id == current_user.company_id, table.c.parent_id == subtree.c.id))
        query = query.where(table.c.id.not_in(select(subtree.c.id)))
    if exclude_id:
        query = query.where(table.c[key] != identifier(exclude_id))
    if selected_value is not None:
        query = query.where(table.c[key] == identifier(selected_value))
    if ids:
        selected = [value for value in ids.split(",") if value]
        if len(selected) > 50:
            raise HTTPException(422, "Como máximo 50 selecciones por consulta.")
        query = query.where(table.c[key].in_([identifier(value) for value in selected]))
    if search.strip():
        needle = search.strip().lower()
        columns = [table.c[name] for name in (label, *codes) if name in table.c]
        if db.bind.dialect.name == "postgresql":
            accented = "áéíóúüñÁÉÍÓÚÜÑ"
            plain = "aeiouunAEIOUUN"
            needle = "".join(character for character in unicodedata.normalize("NFD", needle) if not unicodedata.combining(character))
            columns = [func.translate(column, accented, plain) for column in columns]
        query = query.where(or_(*(func.lower(column).contains(needle, autoescape=True) for column in columns)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(table.c.code if resource in ("branches", "warehouses") else table.c[label], table.c[key]).offset(offset).limit(limit)).mappings().all()
    items = []
    for row in rows:
        identifier = str(row["value"])
        name = row["name"] or identifier
        data = {"id": str(row.get("extra_id", row["value"])), "name": name, "legal_name": name, "full_name": name, "code": row.get("code", identifier), "sku": row.get("code", identifier)}
        for extra in ("branch_id", "is_active", "allow_fractions", "precision_digits", "timezone"):
            if f"extra_{extra}" in row:
                value = row[f"extra_{extra}"]
                data[extra] = str(value) if isinstance(value, UUID) else value
        if resource == "branches":
            data["branch_id"] = identifier
        if resource == "warehouses":
            data["warehouse_id"] = identifier
        if resource == "sales_reps":
            data["rep_id"] = identifier
        items.append({"value": identifier, "label": f"{row['code']} · {name}" if row.get("code") else str(name), "data": data})
    return {"items": items, "total_count": total, "has_more": offset + len(items) < total}


@router.get("/{resource}")
def selector_options(resource: str, search: str = Query("", max_length=128), limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=10000), ids: str = Query("", max_length=2000), branch_id: UUID | None = None, warehouse_id: UUID | None = None, exclude_id: str = Query("", max_length=64), active_only: bool = False, exclude_subtree: UUID | None = None, selected_value: str | None = Query(None, max_length=128), current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_selector_options(resource, search, limit, offset, ids, branch_id, warehouse_id, exclude_id, active_only, current_user, db, exclude_subtree, selected_value)
