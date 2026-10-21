from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.shared.infrastructure.models import ProductModel


@dataclass
class InsightRuleDefinition:
    code: str
    version: int
    scope: str
    name: str
    formula: str
    default_threshold: Decimal
    severity: str
    min_n: int
    metric_name: str
    unit: str
    parameter_template: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "version": self.version,
            "scope": self.scope,
            "name": self.name,
            "formula": self.formula,
            "threshold": str(self.default_threshold),
            "severity": self.severity,
            "min_n": self.min_n,
            "metric_name": self.metric_name,
            "unit": self.unit,
            "parameter_template": self.parameter_template,
        }


RULE_CATALOG: dict[str, InsightRuleDefinition] = {
    "RULE-MARGIN-COMPRESSION-v1": InsightRuleDefinition(
        code="RULE-MARGIN-COMPRESSION-v1",
        version=1,
        scope="product",
        name="Compresión de margen de precio de lista",
        formula="((unit_price - unit_cost) / unit_price) * 100 < threshold",
        default_threshold=Decimal("20.00"),
        severity="high",
        min_n=1,
        metric_name="list_margin_pct",
        unit="%",
        parameter_template="Margen actual de {margin_pct:.2f}% es inferior al umbral mínimo de {threshold:.2f}%",
    ),
    "RULE-HISTORICAL-MARGIN-DIP-v1": InsightRuleDefinition(
        code="RULE-HISTORICAL-MARGIN-DIP-v1",
        version=1,
        scope="sales_history",
        name="Caída de margen bruto histórico en ventas cerradas",
        formula="historical_margin_pct < threshold",
        default_threshold=Decimal("15.00"),
        severity="high",
        min_n=3,
        metric_name="historical_margin_pct",
        unit="%",
        parameter_template="Margen histórico realizado de {historical_margin_pct:.2f}% es inferior al umbral de {threshold:.2f}%",
    ),
    "RULE-SALES-DROP-TEAM-v1": InsightRuleDefinition(
        code="RULE-SALES-DROP-TEAM-v1",
        version=1,
        scope="team",
        name="Caída observada de volumen de ventas en periodo",
        formula="(current_volume - baseline_volume) / baseline_volume * 100 < -threshold",
        default_threshold=Decimal("30.00"),
        severity="medium",
        min_n=5,
        metric_name="sales_drop_pct",
        unit="%",
        parameter_template="Volumen observado de ventas cayó un {drop_pct:.2f}% respecto al periodo base",
    ),
    "RULE-INVENTORY-TURNOVER-v1": InsightRuleDefinition(
        code="RULE-INVENTORY-TURNOVER-v1",
        version=1,
        scope="inventory",
        name="Baja rotación / stock estancado",
        formula="stock_units > 0 and days_without_sales > threshold_days",
        default_threshold=Decimal("60.00"),
        severity="medium",
        min_n=1,
        metric_name="days_without_sales",
        unit="días",
        parameter_template="Producto con stock inmovilizado durante {days_without_sales} días",
    ),
}


def get_rules_catalog() -> list[dict[str, Any]]:
    return [rule.to_dict() for rule in RULE_CATALOG.values()]


def redact_insight_for_user(insight_dict: dict[str, Any], can_view_costs: bool) -> dict[str, Any]:
    cloned = dict(insight_dict)
    rule_code = cloned.get("rule_id") or cloned.get("rule_definition", {}).get("code", "")
    is_cost_sensitive = (
        "margin" in rule_code.lower() or "cost" in rule_code.lower() or cloned.get("entity_type") == "Product"
    )

    if not can_view_costs and is_cost_sensitive:
        cloned["cost_confidential"] = True
        cloned["cifra_clave"] = "[RESTRINGIDO]"
        prod_name = (
            cloned.get("title", "")
            .replace("Margen bruto comprimido en ", "")
            .replace("Margen histórico comprimido en ", "")
        )
        cloned["title"] = (
            f"Alerta de rentabilidad comercial en {prod_name}" if prod_name else "Alerta de rentabilidad comercial"
        )
        cloned["evidence"] = "Información de costos y margen restringida según política de permisos del usuario."
        cloned["observation"] = (
            "Se detecta desviación de rentabilidad comercial teórica sujeta a revisión administrativa."
        )
        cloned["interpretation"] = (
            "Métricas de margen y costo confidenciales; no accesibles sin permiso de lectura de costos."
        )
        cloned["suggested_action"] = "Contactar a un administrador o responsable de compras para evaluar la ficha."

        if "evidence_data" in cloned and isinstance(cloned["evidence_data"], dict):
            ev = dict(cloned["evidence_data"])
            ev["current_value"] = "[RESTRINGIDO]"
            ev["baseline_value"] = "[RESTRINGIDO]"
            ev["numerator"] = "[RESTRINGIDO]"
            ev["denominator"] = "[RESTRINGIDO]"
            ev["difference_pct"] = "[RESTRINGIDO]"
            ev["threshold"] = "[RESTRINGIDO]"
            if "unit_cost" in ev:
                ev["unit_cost"] = "[RESTRINGIDO]"
            cloned["evidence_data"] = ev

        if "suggested_actions" in cloned and isinstance(cloned["suggested_actions"], list):
            redacted_actions = []
            for act in cloned["suggested_actions"]:
                act_copy = dict(act)
                act_copy["description"] = "Revisión interna reservada para personal autorizado de costos."
                act_copy["projected_impact"] = "Impacto reservado."
                if "draft_preview" in act_copy and isinstance(act_copy["draft_preview"], dict):
                    dp = dict(act_copy["draft_preview"])
                    dp["current_cost"] = "[RESTRINGIDO]"
                    dp["suggested_price"] = "[RESTRINGIDO]"
                    act_copy["draft_preview"] = dp
                redacted_actions.append(act_copy)
            cloned["suggested_actions"] = redacted_actions
    else:
        cloned["cost_confidential"] = False

    return cloned


def simulate_rule(rule_code: str, candidate_threshold: Decimal, company_id: UUID, db: Session) -> dict[str, Any]:
    rule = RULE_CATALOG.get(rule_code)
    if not rule:
        return {"error": "Regla no encontrada", "rule_code": rule_code, "persisted_changes": False}

    simulated_triggered = 0
    baseline_triggered = 0

    if rule.scope == "product":
        products = (
            db.execute(
                select(ProductModel).where(ProductModel.company_id == company_id, ProductModel.is_active.is_(True))
            )
            .scalars()
            .all()
        )

        for p in products:
            if p.unit_price > 0:
                margin = p.unit_price - p.unit_cost
                margin_pct = (margin / p.unit_price) * Decimal("100")
                if margin_pct < candidate_threshold:
                    simulated_triggered += 1
                if margin_pct < rule.default_threshold:
                    baseline_triggered += 1

    return {
        "rule_code": rule_code,
        "candidate_threshold": str(candidate_threshold),
        "baseline_threshold": str(rule.default_threshold),
        "simulated_triggered_count": simulated_triggered,
        "baseline_triggered_count": baseline_triggered,
        "potential_false_positives_diff": max(0, simulated_triggered - baseline_triggered),
        "persisted_changes": False,
        "simulated_at": datetime.now(timezone.utc).isoformat(),
    }
