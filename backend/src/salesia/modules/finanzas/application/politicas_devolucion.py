import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.organizacion.application.periodos import business_date
from salesia.shared.infrastructure.models import CompanyModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

CONDITIONS = ("unused", "used", "damaged", "not_applicable")
PACKAGING = ("sealed", "opened", "missing", "not_applicable")
SCALE = Decimal("0.000001")


class ReturnRule(BaseModel):
    returnable: bool = True
    days: int = Field(default=30, ge=0, le=3650)
    allowed_conditions: list[Literal["unused", "used", "damaged", "not_applicable"]] = Field(default_factory=lambda: list(CONDITIONS), min_length=1, max_length=4)
    allowed_packaging: list[Literal["sealed", "opened", "missing", "not_applicable"]] = Field(default_factory=lambda: list(PACKAGING), min_length=1, max_length=4)
    evidence_required: bool = False
    allow_exceptions: bool = True
    retention_percentage: Decimal = Field(default=Decimal("0"), ge=0, lt=100, decimal_places=4)
    retention_description: str = Field(default="", max_length=255)

    @model_validator(mode="after")
    def valid_lists(self):
        if len(set(self.allowed_conditions)) != len(self.allowed_conditions) or len(set(self.allowed_packaging)) != len(self.allowed_packaging):
            raise ValueError("No repita condiciones de artículo ni empaque.")
        if self.retention_percentage > 0 and len(self.retention_description.strip()) < 5:
            raise ValueError("Describa el concepto retenido por devolución.")
        return self


class PolicySave(BaseModel):
    version: int = Field(default=0, ge=0)
    default_rule: ReturnRule = Field(default_factory=ReturnRule)
    rules: dict[Literal["product", "service", "kit"], ReturnRule] = Field(default_factory=dict)
    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value):
        return value.strip() if isinstance(value, str) else value


def policy_row(db, company_id):
    return db.scalar(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "return_policy", AnalyticsArtifact.artifact_key == "return_policy").order_by(AnalyticsArtifact.version.desc()).limit(1))


def policy_data(db, company_id):
    row = policy_row(db, company_id)
    return {"version": row.version if row else 0, "default_rule": ReturnRule().model_dump(mode="json"), "rules": {}, "reason": "Condiciones históricas por defecto", **(json.loads(row.data_json) if row else {})}


def save_policy(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "return_policy.save", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel.id).where(CompanyModel.id == user.company_id).with_for_update())
    previous = policy_row(db, user.company_id)
    if (previous.version if previous else 0) != payload.version:
        raise HTTPException(409, "La política cambió. Consulte su versión actual antes de guardar.")
    data = payload.model_dump(mode="json")
    data["version"] = payload.version + 1
    data["actor"] = user.email
    data["at"] = datetime.now(timezone.utc).isoformat()
    row = AnalyticsArtifact(company_id=user.company_id, kind="return_policy", artifact_key="return_policy", version=data["version"], status="active", parent_id=previous.id if previous else None, data_json=json.dumps(data), created_by=user.user_id)
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_RETURN_POLICY", entity_type="AnalyticsArtifact", entity_id=row.id, diff=data)
    complete_request(record, data)
    db.commit()
    return data


def policy_history(db, company_id):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "return_policy", AnalyticsArtifact.artifact_key == "return_policy").order_by(AnalyticsArtifact.version.desc())).all()
    return [json.loads(row.data_json) for row in rows]


def snapshot_for_product(db, company_id, product_id, at, policy=None):
    policy = policy or policy_data(db, company_id)
    profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == company_id, ProductProfileModel.product_id == product_id))
    product_type = "kit" if profile and profile.is_kit else profile.product_type if profile else "product"
    rule = policy["rules"].get(product_type, policy["default_rule"])
    return {"version": policy["version"], "source": "sale_confirmation", "product_type": product_type, "sold_on": business_date(db, company_id, at).isoformat(), "rule": rule}


def freeze_sale_policies(db, sale):
    policy = policy_data(db, sale.company_id)
    for line in sale.lines:
        line.return_policy_snapshot = json.dumps(snapshot_for_product(db, sale.company_id, line.product_id, sale.confirmed_at, policy))


def line_policy(db, sale, line):
    if line.return_policy_snapshot:
        return json.loads(line.return_policy_snapshot)
    return {"version": 0, "source": "legacy_default", "product_type": "unknown", "sold_on": business_date(db, sale.company_id, sale.confirmed_at or sale.created_at).isoformat(), "rule": ReturnRule().model_dump(mode="json")}


def assess(snapshot, today, condition=None, packaging=None, evidence_note="", evidence_references=None):
    rule = snapshot["rule"]
    sold = datetime.fromisoformat(snapshot["sold_on"]).date()
    deadline = sold + timedelta(days=rule["days"])
    reasons = []
    if not rule["returnable"]:
        reasons.append({"code": "not_returnable", "message": "La política ofrecida no admite devolución comercial de este artículo."})
    if today > deadline:
        reasons.append({"code": "expired", "message": f"El plazo de devolución venció el {deadline.isoformat()}."})
    if condition is None and set(rule["allowed_conditions"]) != set(CONDITIONS):
        reasons.append({"code": "condition_missing", "message": "Declare el estado del artículo para evaluar esta política."})
    if packaging is None and set(rule["allowed_packaging"]) != set(PACKAGING):
        reasons.append({"code": "packaging_missing", "message": "Declare el estado del empaque para evaluar esta política."})
    if condition is not None and condition not in rule["allowed_conditions"]:
        reasons.append({"code": "condition", "message": "El estado declarado del artículo no cumple las condiciones ofrecidas."})
    if packaging is not None and packaging not in rule["allowed_packaging"]:
        reasons.append({"code": "packaging", "message": "El empaque declarado no cumple las condiciones ofrecidas."})
    valid_references = any(isinstance(value, str) and len(value.strip()) >= 5 for value in evidence_references or [])
    if rule["evidence_required"] and len(evidence_note.strip()) < 5 and not valid_references:
        reasons.append({"code": "evidence", "message": "La política exige evidencia o un sustento documentado de al menos cinco caracteres."})
    return {"policy": snapshot, "deadline": deadline.isoformat(), "evaluated_on": today.isoformat(), "condition": condition, "packaging": packaging, "evidence_note": evidence_note.strip(), "reasons": reasons, "eligible": not reasons, "exception_possible": bool(rule["allow_exceptions"] and not any(item["code"] in {"evidence", "condition_missing", "packaging_missing"} for item in reasons)), "retention_percentage": str(rule["retention_percentage"])}


def require_policy(assessment, payload, user):
    if assessment["reasons"]:
        if not payload.authorized_exception or not assessment["exception_possible"]:
            raise HTTPException(422, " ".join(item["message"] for item in assessment["reasons"]))
    if payload.authorized_exception or payload.waive_retention:
        if "approvals:manage" not in user.permissions or not payload.exception_reason or len(payload.exception_reason.strip()) < 5:
            raise HTTPException(403, "La excepción o exoneración requiere permiso de aprobaciones y justificación documentada.")
        needs_exception = bool(assessment["reasons"]) or (payload.waive_retention and Decimal(assessment["retention_percentage"]) > 0)
        if needs_exception and not assessment["policy"]["rule"]["allow_exceptions"]:
            raise HTTPException(422, "La política ofrecida no permite excepciones para esta línea.")
    assessment["exception_applied"] = bool(assessment["reasons"] and payload.authorized_exception)
    assessment["retention_waived"] = bool(payload.waive_retention and Decimal(assessment["retention_percentage"]) > 0)
    assessment["applied_retention_percentage"] = "0" if payload.waive_retention else assessment["retention_percentage"]


def return_valuation(ret):
    details = json.loads(ret.details_json or "{}")
    assessments = details.get("policy_assessments", {})
    result = []
    for line in ret.lines:
        assessment = assessments.get(str(line.sale_line_id), {})
        percentage = Decimal(assessment.get("applied_retention_percentage", "0"))
        original_unit = max(Decimal("0"), line.unit_price_snapshot - line.discount_per_unit)
        gross_net = (line.quantity * original_unit).quantize(SCALE)
        retained_net = (gross_net * percentage / 100).quantize(SCALE)
        refundable_net = gross_net - retained_net
        original_tax = (gross_net * line.tax_rate_snapshot).quantize(SCALE)
        refundable_tax = (refundable_net * line.tax_rate_snapshot).quantize(SCALE)
        result.append({"line_id": str(line.id), "sale_line_id": str(line.sale_line_id) if line.sale_line_id else None, "gross_net": str(gross_net), "retained_net": str(retained_net), "retained_total": str(retained_net + original_tax - refundable_tax), "refundable_net": str(refundable_net), "refundable_tax": str(refundable_tax), "refundable_total": str(refundable_net + refundable_tax), "retention_percentage": str(percentage), "retention_description": assessment.get("policy", {}).get("rule", {}).get("retention_description", "")})
    if ret.is_without_receipt and ret.manual_valuation_total is not None:
        return {"lines": result, "retained_total": "0", "refundable_total": str(ret.manual_valuation_total), "requires_original_sale_review": True}
    return {"lines": result, "retained_total": str(sum((Decimal(item["retained_total"]) for item in result), Decimal("0"))), "refundable_total": str(sum((Decimal(item["refundable_total"]) for item in result), Decimal("0")))}
