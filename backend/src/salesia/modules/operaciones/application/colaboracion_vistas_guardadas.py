import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.colaboracion_vistas_guardadas import (
    SavedViewCreateRequest,
    SavedViewUpdateRequest,
)
from salesia.modules.operaciones.infrastructure_models import SavedView
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_saved_view(payload: SavedViewCreateRequest, current_user: AuthenticatedUser, db: Session):
    view = SavedView(
        company_id=current_user.company_id,
        user_id=current_user.user_id,
        resource_type=payload.resource_type,
        name=payload.name,
        config_json=payload.config_json,
        schema_version=payload.schema_version,
        is_shared=payload.is_shared,
        created_at=now(),
        updated_at=now(),
    )

    db.add(view)

    db.commit()

    return {
        "id": str(view.id),
        "name": view.name,
        "resource_type": view.resource_type,
        "schema_version": view.schema_version,
    }


def list_saved_views(resource_type: str, current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(SavedView).where(
            SavedView.company_id == current_user.company_id,
            SavedView.resource_type == resource_type,
            (SavedView.user_id == current_user.user_id) | (SavedView.is_shared.is_(True)),
        )
    ).all()

    results = []

    current_schema = 2

    for r in rows:
        conf = json.loads(r.config_json)

        migrated = False

        if r.schema_version < current_schema:
            if "legacy_filter" in conf:
                conf["filters"] = [conf.pop("legacy_filter")]

            conf["density"] = conf.get("density", "normal")

            migrated = True

        results.append(
            {
                "id": str(r.id),
                "name": r.name,
                "resource_type": r.resource_type,
                "schema_version": current_schema if migrated else r.schema_version,
                "is_migrated": migrated,
                "config": conf,
                "is_shared": r.is_shared,
            }
        )

    return {"items": results}


def update_saved_view(view_id: UUID, payload: SavedViewUpdateRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(SavedView)
        .where(
            SavedView.id == view_id,
            SavedView.company_id == current_user.company_id,
            SavedView.user_id == current_user.user_id,
        )
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Vista guardada no encontrada.")

    if payload.name:
        row.name = payload.name

    if payload.config_json:
        row.config_json = payload.config_json

    if payload.schema_version:
        row.schema_version = payload.schema_version

    if payload.is_shared is not None:
        row.is_shared = payload.is_shared

    row.updated_at = now()

    db.commit()

    return {"id": str(row.id), "name": row.name, "schema_version": row.schema_version}


def delete_saved_view(view_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.company_id == current_user.company_id,
            SavedView.user_id == current_user.user_id,
        )
    )

    if not row:
        raise HTTPException(404, "Vista no encontrada.")

    db.delete(row)

    db.commit()

    return {"id": str(view_id), "deleted": True}
