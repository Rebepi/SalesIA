import json
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.organizacion.application.periodos import business_date, require_open_month, require_open_period
from salesia.modules.ventas.application.motor_comisiones import collected, period_cut, rounded, sale_measure
from salesia.modules.ventas.application.participacion_comercial import freeze_commission, representative
from salesia.modules.ventas.infrastructure.models.equipo_comisiones import SalesRepresentative
from salesia.shared.infrastructure.models import CompanyModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class MetricTarget(BaseModel):
    metric: Literal["amount", "margin", "units", "clients", "new_clients", "collections"]
    target: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    weight: Decimal = Field(gt=0, le=100, max_digits=9, decimal_places=6)


class CombinedTargetSave(BaseModel):
    identifier: UUID | None = None
    expected_version: int = Field(default=0, ge=0)
    name: str = Field(min_length=3, max_length=128)
    period: str = Field(pattern=r"^\d{4}-\d{2}$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    scope: Literal["individual", "team", "company"]
    representative_id: UUID | None = None
    team: str | None = Field(default=None, min_length=1, max_length=128)
    metrics: list[MetricTarget] = Field(min_length=1, max_length=6)
    status: Literal["active", "archived"] = "active"
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def valid_scope(self):
        if self.scope == "individual" and not self.representative_id or self.scope == "team" and not self.team:
            raise ValueError("La meta individual requiere vendedor y la meta de equipo requiere un equipo.")
        if len({item.metric for item in self.metrics}) != len(self.metrics):
            raise ValueError("No repita indicadores en una meta combinada.")
        return self


def target_rows(db, company_id):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == company_id, AnalyticsArtifact.kind == "combined_sales_target").order_by(AnalyticsArtifact.version.desc())).all()
    latest = {}
    for row in rows:
        latest.setdefault(row.artifact_key, json.loads(row.data_json))
    return list(latest.values())


def save_target(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "sales.combined_target", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    start, _ = period_cut(db, user.company_id, payload.period)
    require_open_month(db, user.company_id, payload.period, ["commissions"])
    require_open_period(db, user.company_id, business_date(db, user.company_id, start))
    if payload.scope == "individual":
        representative(db, user.company_id, payload.representative_id)
    if payload.scope == "team" and not db.scalar(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.team == payload.team).limit(1)):
        raise HTTPException(422, "El equipo debe estar registrado en los vendedores de la empresa activa.")
    identifier = str(payload.identifier or uuid4())
    previous = next((row for row in target_rows(db, user.company_id) if row["id"] == identifier), None)
    if (previous["version"] if previous else 0) != payload.expected_version:
        raise HTTPException(409, "La meta cambió. Consulte su versión vigente antes de guardar.")
    data = {**payload.model_dump(mode="json", exclude={"identifier", "expected_version"}), "id": identifier, "version": payload.expected_version + 1, "actor": user.email}
    db.add(AnalyticsArtifact(company_id=user.company_id, kind="combined_sales_target", artifact_key=identifier, version=data["version"], status=data["status"], data_json=json.dumps(data), created_by=user.user_id))
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SAVE_COMBINED_SALES_TARGET", entity_type="AnalyticsArtifact", entity_id=UUID(identifier), diff=data)
    complete_request(record, data)
    db.commit()
    return data


def progress(db, user, target):
    start, cutoff = period_cut(db, user.company_id, target["period"])
    sales = db.scalars(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.currency == target["currency"], SaleModel.status != "draft", SaleModel.confirmed_at < cutoff).order_by(SaleModel.confirmed_at, SaleModel.id)).all()
    values = {item["metric"]: Decimal("0") for item in target["metrics"]}
    customers = set()
    new_customers = set()
    contributions = []
    warnings = []
    for sale in sales:
        snapshot = freeze_commission(db, sale, historical=True, persist=False)
        participants = snapshot["participants"]
        if target["scope"] == "individual":
            share = sum((Decimal(row["percentage"]) / 100 for row in participants if row["representative_id"] == target["representative_id"]), Decimal("0"))
        elif target["scope"] == "team":
            share = min(Decimal("1"), sum((Decimal(row["percentage"]) / 100 for row in participants if row.get("team") == target["team"]), Decimal("0")))
            if snapshot["historical"] and share > 0:
                warnings.append("Las ventas históricas sin equipo conservado usan el equipo conocido al adoptar su participación; revise ese origen al comparar metas anteriores.")
        else:
            share = Decimal("1")
        if share <= 0:
            continue
        full = {**snapshot, "eligible_line_ids": [str(line.id) for line in sale.lines], "policy": {**snapshot["policy"], "base": "sales", "include_tax": True, "earned_on": "sale"}}
        measure = sale_measure(db, user, sale, full, cutoff)
        warnings.extend(measure["warnings"])
        in_period = start <= sale.confirmed_at.replace(tzinfo=sale.confirmed_at.tzinfo or start.tzinfo) < cutoff
        actual = {name: Decimal("0") for name in values}
        if in_period and not measure["cancelled"]:
            remaining = {UUID(row["line_id"]): max(Decimal("0"), Decimal(row["quantity"]) - Decimal(row["returned_quantity"])) for row in measure["lines"]}
            if "amount" in actual:
                actual["amount"] = measure["net"] * share
            if "margin" in actual:
                actual["margin"] = sum(((line.subtotal_amount - line.quantity * line.unit_cost_snapshot) * remaining[line.id] / line.quantity for line in sale.lines), Decimal("0")) * share
            if "units" in actual:
                actual["units"] = sum(remaining.values(), Decimal("0")) * share
            if sum(remaining.values(), Decimal("0")) > 0:
                if "clients" in actual and sale.customer_id not in customers:
                    actual["clients"] = Decimal("1")
                customers.add(sale.customer_id)
                prior = db.scalar(select(SaleModel.id).where(SaleModel.company_id == user.company_id, SaleModel.customer_id == sale.customer_id, SaleModel.status.in_(("confirmed", "paid", "refunded")), SaleModel.confirmed_at < start).limit(1))
                if prior is None:
                    if "new_clients" in actual and sale.customer_id not in new_customers:
                        actual["new_clients"] = Decimal("1")
                    new_customers.add(sale.customer_id)
        if "collections" in actual:
            at_end = sum((Decimal(item["amount"]) for item in collected(db, user.company_id, sale, cutoff)), Decimal("0"))
            before = sum((Decimal(item["amount"]) for item in collected(db, user.company_id, sale, start)), Decimal("0"))
            actual["collections"] = (at_end - before) * share
        for name, value in actual.items():
            values[name] += value
        if any(value != 0 for value in actual.values()):
            contributions.append({"sale_id": str(sale.id), "document_number": f"{sale.series}-{sale.number:08d}", "participation": str(share * 100), "values": {name: str(rounded(value)) for name, value in actual.items()}})
    if "clients" in values:
        values["clients"] = Decimal(len(customers))
    if "new_clients" in values:
        values["new_clients"] = Decimal(len(new_customers))
    metrics = []
    weighted = Decimal("0")
    total_weight = sum((Decimal(item["weight"]) for item in target["metrics"]), Decimal("0"))
    for item in target["metrics"]:
        actual = rounded(values[item["metric"]])
        attainment = max(Decimal("0"), actual / Decimal(item["target"]) * 100)
        weighted += min(Decimal("100"), attainment) * Decimal(item["weight"])
        metrics.append({**item, "actual": str(actual), "attainment": str(rounded(attainment))})
    return {**target, "metrics": metrics, "weighted_attainment": str(rounded(weighted / total_weight)), "contributions": contributions, "warnings": sorted(set(warnings)), "calendar": {"start": start.isoformat(), "end_exclusive": cutoff.isoformat(), "timezone": "company"}, "definition": "Cada venta aporta una sola vez con la suma de las participaciones del ámbito. Clientes se cuenta por persona, sin sumar participantes. La ponderación normaliza pesos y limita a 100 % el aporte de cada indicador. Todos los datos usan la moneda y el mes operativo indicados; cobranza es la variación neta de dinero confirmado y aplicado dentro del período."}


def list_targets(db, user, period=None, limit=20, offset=0):
    rows = target_rows(db, user.company_id)
    if "organization:manage" not in user.permissions:
        identifiers = {str(value) for value in db.scalars(select(SalesRepresentative.id).where(SalesRepresentative.company_id == user.company_id, SalesRepresentative.user_id == user.user_id)).all()}
        rows = [row for row in rows if row["scope"] == "individual" and row["representative_id"] in identifiers]
    if period:
        rows = [row for row in rows if row["period"] == period]
    rows.sort(key=lambda row: (row["period"], row["name"], row["id"]), reverse=True)
    return {"total_count": len(rows), "items": [progress(db, user, row) for row in rows[offset:offset + limit]]}
