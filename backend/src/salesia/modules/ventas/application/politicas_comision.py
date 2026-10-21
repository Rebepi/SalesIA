import json
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.organizacion.application.auxiliares.default_settings_dict import default_settings_dict
from salesia.modules.organizacion.application.contracts.politicas import CommissionPolicy
from salesia.modules.organizacion.application.periodos import business_date
from salesia.modules.organizacion.application.politicas import effective_policy
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import CompanySettings, claim_request, complete_request


class CommissionPolicySave(BaseModel):
    expected_version: int = Field(ge=1)
    policy: CommissionPolicy
    reason: str = Field(min_length=5, max_length=2000)


def current_policy(db, company_id):
    return CommissionPolicy.model_validate(effective_policy(db, company_id, "commission_policy")).model_dump(mode="json")


def archive_policy(db, user, policy, reason):
    parsed = CommissionPolicy.model_validate(policy)
    if parsed.product_ids:
        actual = set(db.scalars(select(ProductModel.id).where(ProductModel.company_id == user.company_id, ProductModel.id.in_(parsed.product_ids))).all())
        if actual != set(parsed.product_ids):
            raise HTTPException(422, "Los productos de la política deben pertenecer a la empresa activa.")
    if parsed.category_ids:
        from salesia.modules.catalogo.infrastructure.models.clasificacion import CategoryModel
        actual = set(db.scalars(select(CategoryModel.id).where(CategoryModel.company_id == user.company_id, CategoryModel.id.in_(parsed.category_ids))).all())
        if actual != set(parsed.category_ids):
            raise HTTPException(422, "Las categorías de comisión deben pertenecer a la empresa activa.")
    existing = db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "commission_policy", AnalyticsArtifact.artifact_key == "default", AnalyticsArtifact.version == parsed.version))
    if existing:
        return
    data = {"policy": parsed.model_dump(mode="json"), "reason": reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()}
    db.add(AnalyticsArtifact(company_id=user.company_id, kind="commission_policy", artifact_key="default", version=parsed.version, status="active", data_json=json.dumps(data), created_by=user.user_id))
    db.flush()


def policy_at(db, company_id, operation_date):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "commission_policy", AnalyticsArtifact.artifact_key == "default").order_by(AnalyticsArtifact.version.desc())).all()
    candidates = [json.loads(row.data_json)["policy"] for row in rows]
    if not rows:
        candidates.append(current_policy(db, company_id))
    for policy in candidates:
        if date.fromisoformat(policy["valid_from"]) <= operation_date and (not policy.get("valid_until") or operation_date <= date.fromisoformat(policy["valid_until"])):
            return policy
    return CommissionPolicy.model_validate(default_settings_dict()["commission_policy"]).model_dump(mode="json")


def save_policy(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "commission_policy.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    previous = current_policy(db, user.company_id)
    if previous["version"] != payload.expected_version:
        raise HTTPException(409, "La política cambió. Consulte su versión vigente.")
    if payload.policy.valid_from < business_date(db, user.company_id):
        raise HTTPException(422, "Las políticas nuevas requieren vigencia desde hoy o una fecha futura; las ventas confirmadas conservan sus condiciones.")
    archive_policy(db, user, previous, "Adopción de la política configurada previamente")
    policy = payload.policy.model_dump(mode="json")
    policy["version"] = previous["version"] + 1
    archive_policy(db, user, policy, payload.reason)
    settings = db.get(CompanySettings, user.company_id)
    values = json.loads(settings.values_json or "{}") if settings else {}
    values["commission_policy"] = policy
    if settings:
        settings.version += 1
        settings.values_json = json.dumps(values)
    else:
        db.add(CompanySettings(company_id=user.company_id, version=1, values_json=json.dumps(values)))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_COMMISSION_POLICY", entity_type="CompanySettings", entity_id=user.company_id, diff={"policy": policy, "reason": payload.reason})
    complete_request(record, policy)
    db.commit()
    return policy


def history(db, company_id):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "commission_policy", AnalyticsArtifact.artifact_key == "default").order_by(AnalyticsArtifact.version.desc())).all()
    return [json.loads(row.data_json) for row in rows]
