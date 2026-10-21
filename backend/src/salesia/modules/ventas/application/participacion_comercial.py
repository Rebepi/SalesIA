import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.organizacion.application.auxiliares.default_settings_dict import default_settings_dict
from salesia.modules.organizacion.application.contracts.politicas import CommissionPolicy
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.ventas.application.auxiliares.scoped_sale import scoped_sale
from salesia.modules.ventas.application.politicas_comision import policy_at
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesRepresentative
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class Participant(BaseModel):
    representative_id: UUID
    role: Literal["seller", "prospector", "team", "replacement"] = "seller"
    percentage: Decimal = Field(gt=0, le=100, max_digits=9, decimal_places=6)


class ParticipationSave(BaseModel):
    expected_sale_version: int = Field(ge=1)
    participants: list[Participant] = Field(min_length=1, max_length=20)
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def valid_shares(self):
        if len({row.representative_id for row in self.participants}) != len(self.participants) or sum((row.percentage for row in self.participants), Decimal("0")) != 100:
            raise ValueError("La participación debe sumar exactamente 100 % sin repetir vendedores.")
        return self


class CoverageSave(BaseModel):
    identifier: UUID | None = None
    expected_version: int = Field(default=0, ge=0)
    representative_id: UUID
    replacement_id: UUID
    starts_on: date
    ends_on: date
    percentage: Decimal = Field(gt=0, le=100, max_digits=9, decimal_places=6)
    reason: str = Field(min_length=5, max_length=2000)
    status: Literal["active", "cancelled"] = "active"

    @model_validator(mode="after")
    def valid_dates(self):
        if self.ends_on < self.starts_on or self.representative_id == self.replacement_id:
            raise ValueError("El reemplazo requiere personas distintas y un rango de fechas válido.")
        return self


def coverage_rows(db, company_id):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "commission_coverage").order_by(AnalyticsArtifact.version.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.artifact_key, json.loads(row.data_json))
    return list(latest.values())


def representative(db, company_id, identifier, active=True):
    query = select(SalesRepresentative).where(SalesRepresentative.company_id == company_id, SalesRepresentative.id == identifier)
    if active:
        query = query.where(SalesRepresentative.is_active.is_(True))
    row = db.scalar(query)
    if row is None:
        raise HTTPException(422, "El vendedor debe pertenecer a la empresa activa y estar disponible.")
    return row


def freeze_commission(db, sale, historical=False, persist=True):
    db.flush()
    saved = json.loads(sale.commission_snapshot_json or "{}")
    if saved.get("frozen"):
        return saved
    if not historical:
        from salesia.modules.organizacion.application.perfil_operativo import current
        profile = current(db, sale.company_id)
        if "commissions" not in profile["enabled"]:
            day = business_date(db, sale.company_id, sale.confirmed_at or sale.created_at)
            snapshot = {"frozen": True, "historical": False, "sale_date": day.isoformat(), "participants": [], "eligible_line_ids": [], "policy": policy_at(db, sale.company_id, day), "coverage_id": None, "coverage_version": None, "operating_profile_version": profile["version"], "reason": "La empresa tenía desactivadas las comisiones al confirmar la venta.", "at": datetime.now(timezone.utc).isoformat()}
            if persist:
                sale.commission_snapshot_json = json.dumps(snapshot)
            return snapshot
    day = business_date(db, sale.company_id, sale.confirmed_at or sale.created_at)
    policy = CommissionPolicy.model_validate(default_settings_dict()["commission_policy"]).model_dump(mode="json") if historical else policy_at(db, sale.company_id, day)
    participants = saved.get("participants", [])
    if participants and sale.sales_rep_id and str(sale.sales_rep_id) not in {row["representative_id"] for row in participants}:
        raise HTTPException(409, "La autoría de la venta cambió. Revise su reparto antes de confirmar.")
    if participants and not historical:
        for participant in participants:
            representative(db, sale.company_id, UUID(participant["representative_id"]))
    coverage = None
    if not participants and sale.sales_rep_id:
        participants = [{"representative_id": str(sale.sales_rep_id), "role": "seller", "percentage": "100"}]
        if not historical:
            coverage = next((row for row in coverage_rows(db, sale.company_id) if row["status"] == "active" and row["representative_id"] == str(sale.sales_rep_id) and date.fromisoformat(row["starts_on"]) <= day <= date.fromisoformat(row["ends_on"])), None)
            if coverage:
                replacement = representative(db, sale.company_id, UUID(coverage["replacement_id"]))
                share = Decimal(coverage["percentage"])
                participants = ([{"representative_id": str(sale.sales_rep_id), "role": "seller", "percentage": str(100 - share)}] if share < 100 else []) + [{"representative_id": str(replacement.id), "role": "replacement", "percentage": str(share)}]
    for item in participants:
        owner = representative(db, sale.company_id, UUID(item["representative_id"]), active=not historical)
        item["name"] = owner.full_name
        item["team"] = owner.team
    if participants and not historical:
        require_open_period(db, sale.company_id, day, ["commissions"])
    eligible = []
    products = set(policy.get("product_ids", []))
    categories = set(policy.get("category_ids", []))
    for line in sale.lines:
        product = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == sale.company_id, ProductProfileModel.product_id == line.product_id))
        if not products and not categories or str(line.product_id) in products or product and product.category_id and str(product.category_id) in categories:
            eligible.append(str(line.id))
    snapshot = {"frozen": True, "historical": historical, "at": datetime.now(timezone.utc).isoformat(), "sale_date": day.isoformat(), "policy": policy, "participants": participants, "eligible_line_ids": eligible, "coverage_id": coverage["id"] if coverage else None, "coverage_version": coverage["version"] if coverage else None, "reason": saved.get("reason")}
    if persist:
        sale.commission_snapshot_json = json.dumps(snapshot)
    return snapshot


def save_participation(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"sale.participation:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    sale = scoped_sale(db, identifier, user, True)
    if sale.status != "draft" or sale.version != payload.expected_sale_version:
        raise HTTPException(409, "La participación se acuerda antes de confirmar y requiere la versión vigente de la venta.")
    for item in payload.participants:
        representative(db, user.company_id, item.representative_id)
    if sale.sales_rep_id and sale.sales_rep_id not in {item.representative_id for item in payload.participants}:
        raise HTTPException(422, "La venta compartida debe conservar la participación del vendedor autor.")
    data = {"frozen": False, "participants": [item.model_dump(mode="json") for item in payload.participants], "reason": payload.reason, "actor": user.email}
    sale.commission_snapshot_json = json.dumps(data)
    sale.version += 1
    result = {"sale_id": str(sale.id), "sale_version": sale.version, **data}
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SET_SALE_PARTICIPATION", entity_type="Sale", entity_id=sale.id, diff=result)
    complete_request(record, result)
    db.commit()
    return result


def save_coverage(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "commission.coverage", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    representative(db, user.company_id, payload.representative_id)
    representative(db, user.company_id, payload.replacement_id)
    identifier = str(payload.identifier or uuid4())
    rows = coverage_rows(db, user.company_id)
    previous = next((row for row in rows if row["id"] == identifier), None)
    if (previous["version"] if previous else 0) != payload.expected_version:
        raise HTTPException(409, "El reemplazo cambió. Consulte su versión vigente.")
    if previous and (any(previous[name] != str(getattr(payload, name)) for name in ("representative_id", "replacement_id", "starts_on", "ends_on")) or Decimal(previous["percentage"]) != payload.percentage):
        raise HTTPException(409, "Conserve las condiciones del reemplazo registrado; puede cancelarlo y crear otro para fechas futuras.")
    if previous is None and payload.starts_on < business_date(db, user.company_id):
        raise HTTPException(422, "Los reemplazos nuevos no pueden comenzar en una fecha pasada.")
    if previous and previous["status"] != "active":
        raise HTTPException(409, "Un reemplazo cancelado no puede reactivarse.")
    if payload.status == "active" and any(row["id"] != identifier and row["status"] == "active" and row["representative_id"] == str(payload.representative_id) and date.fromisoformat(row["starts_on"]) <= payload.ends_on and payload.starts_on <= date.fromisoformat(row["ends_on"]) for row in rows):
        raise HTTPException(409, "El vendedor ya tiene un reemplazo en parte de esas fechas.")
    data = {**payload.model_dump(mode="json", exclude={"identifier", "expected_version"}), "id": identifier, "version": payload.expected_version + 1, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()}
    db.add(AnalyticsArtifact(company_id=user.company_id, kind="commission_coverage", artifact_key=identifier, version=data["version"], status=payload.status, data_json=json.dumps(data), created_by=user.user_id))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SET_SALES_COVERAGE", entity_type="SalesRepresentative", entity_id=payload.representative_id, diff=data)
    complete_request(record, data)
    db.commit()
    return data
