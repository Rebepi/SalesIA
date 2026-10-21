import json
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.operaciones.application.recursos import RESOURCES, definition, entity, summary
from salesia.modules.operaciones.infrastructure_models import SavedView
from salesia.shared.infrastructure.models import UserModel


class FavoriteRequest(BaseModel):
    active: bool


class RecordViewRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    resource_type: str = Field(max_length=64)
    query: str = Field(default="", max_length=100)
    field_key: str = Field(default="", max_length=64)
    field_value: str = Field(default="", max_length=4000)
    is_shared: bool = False
    version: int = Field(default=0, ge=0)


def favorites(db, user):
    rows = db.scalars(select(SavedView).where(SavedView.company_id == user.company_id, SavedView.user_id == user.user_id, SavedView.resource_type == "business_favorite").order_by(SavedView.created_at.desc())).all()
    result = []
    for row in rows:
        try:
            config = json.loads(row.config_json)
            target = entity(db, user, config["type"], UUID(config["id"]))
            result.append(summary(config["type"], target))
        except HTTPException as failure:
            if failure.status_code not in (403, 404, 422):
                raise
    return result


def set_favorite(db, user, kind, identifier, payload):
    target = entity(db, user, kind, identifier)
    db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == user.user_id).with_for_update())
    name = f"{kind}:{identifier}"
    row = db.scalar(select(SavedView).where(SavedView.company_id == user.company_id, SavedView.user_id == user.user_id, SavedView.resource_type == "business_favorite", SavedView.name == name))
    if payload.active and row is None:
        db.add(SavedView(company_id=user.company_id, user_id=user.user_id, resource_type="business_favorite", name=name, schema_version=1, config_json=json.dumps({"type": kind, "id": str(target.id)}), is_shared=False))
    elif not payload.active and row:
        db.delete(row)
    db.commit()
    return {"active": payload.active}


def record_views(db, user):
    rows = db.scalars(select(SavedView).where(SavedView.company_id == user.company_id, SavedView.resource_type == "business_records", (SavedView.user_id == user.user_id) | SavedView.is_shared.is_(True)).order_by(SavedView.name, SavedView.id)).all()
    result = []
    for row in rows:
        config = json.loads(row.config_json)
        resource = RESOURCES.get(config.get("resource_type"))
        if resource is None or (resource[2] and resource[2] not in user.permissions):
            continue
        result.append({"id": str(row.id), "name": row.name, "is_shared": row.is_shared, "can_edit": row.user_id == user.user_id, "version": row.schema_version, **config})
    return result


def save_record_view(db, user, payload):
    definition(payload.resource_type, user)
    if len(payload.name.strip()) < 2:
        raise HTTPException(422, "El nombre del filtro debe contener al menos dos caracteres.")
    if payload.is_shared and "operations:manage" not in user.permissions and "organization:manage" not in user.permissions:
        raise HTTPException(403, "Compartir filtros requiere administración de operaciones u organización.")
    db.scalar(select(UserModel).where(UserModel.company_id == user.company_id, UserModel.id == user.user_id).with_for_update())
    row = db.scalar(select(SavedView).where(SavedView.company_id == user.company_id, SavedView.user_id == user.user_id, SavedView.resource_type == "business_records", SavedView.name == payload.name.strip()).with_for_update())
    if (row.schema_version if row else 0) != payload.version:
        raise HTTPException(409, "El filtro guardado cambió. Vuelve a cargarlo antes de reemplazarlo.")
    if row is None:
        row = SavedView(company_id=user.company_id, user_id=user.user_id, resource_type="business_records", name=payload.name.strip(), schema_version=0, config_json="{}", is_shared=False)
        db.add(row)
    row.config_json = json.dumps(payload.model_dump(exclude={"name", "is_shared", "version"}))
    row.is_shared = payload.is_shared
    row.schema_version += 1
    db.commit()
    return {"id": str(row.id), "version": row.schema_version}


def delete_record_view(db, user, identifier):
    row = db.scalar(select(SavedView).where(SavedView.company_id == user.company_id, SavedView.user_id == user.user_id, SavedView.id == identifier, SavedView.resource_type == "business_records").with_for_update())
    if row is None:
        raise HTTPException(404, "Filtro personal no encontrado.")
    db.delete(row)
    db.commit()
    return {"deleted": True}
