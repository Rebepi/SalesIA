import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.insights_evaluacion import (
    InsightEvaluationRequest,
    InsightRuleSimulateRequest,
)
from salesia.modules.analitica.domain.insights import RULE_CATALOG, get_rules_catalog, simulate_rule
from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, SaleLineModel, SaleModel


def list_insight_rules(current_user: AuthenticatedUser):
    return {"items": get_rules_catalog()}


def post_simulate_insight_rule(payload: InsightRuleSimulateRequest, current_user: AuthenticatedUser, db: Session):
    return simulate_rule(
        rule_code=payload.rule_code,
        candidate_threshold=payload.candidate_threshold,
        company_id=current_user.company_id,
        db=db,
    )


def evaluate_insights(payload: Optional[InsightEvaluationRequest], current_user: AuthenticatedUser, db: Session):
    if payload is None:
        payload = InsightEvaluationRequest()

    now = datetime.now(timezone.utc)

    suppression_log = []

    cooldown_count = 0

    if payload.data_pipeline_delayed:
        suppression_log.append(
            {
                "reason": "DATA_QUALITY_SUPPRESSED: Ingestión o pipeline de datos atrasado/incompleto",
                "suppressed_at": now.isoformat(),
            }
        )

        active_count = db.scalar(
            select(func.count())
            .select_from(AnalyticsArtifact)
            .where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "insight")
        )

        return {
            "status": "evaluated",
            "generated_count": 0,
            "total_active_insights": active_count,
            "suppression_log": suppression_log,
            "suppressed_by_cooldown_count": 0,
        }

    if payload.check_cooldown:
        recent_cutoff = now - timedelta(minutes=60)

        recent_rows = db.scalars(
            select(AnalyticsArtifact).where(
                AnalyticsArtifact.company_id == current_user.company_id,
                AnalyticsArtifact.kind == "insight",
                AnalyticsArtifact.updated_at >= recent_cutoff,
            )
        ).all()

        cooldown_count = len(recent_rows)

        if cooldown_count > 0:
            suppression_log.append(
                {
                    "reason": "Supresión por cooldown activo (60 minutos sin cambios materiales)",
                    "suppressed_count": cooldown_count,
                }
            )

    products = (
        db.execute(
            select(ProductModel).where(
                ProductModel.company_id == current_user.company_id, ProductModel.is_active.is_(True)
            )
        )
        .scalars()
        .all()
    )

    generated = []

    for p in products:
        if p.unit_price > 0:
            margin = p.unit_price - p.unit_cost

            margin_pct = margin / p.unit_price * Decimal("100")

        else:
            margin = Decimal("0.00")

            margin_pct = Decimal("0.00")

        if margin_pct < Decimal("20.00"):
            rule = RULE_CATALOG["RULE-MARGIN-COMPRESSION-v1"]

            threshold = rule.default_threshold

            dedup_key = f"{p.id}:RULE-MARGIN-COMPRESSION-v1"

            existing = db.scalar(
                select(AnalyticsArtifact).where(
                    AnalyticsArtifact.company_id == current_user.company_id,
                    AnalyticsArtifact.kind == "insight",
                    AnalyticsArtifact.artifact_key == dedup_key,
                    AnalyticsArtifact.version == 1,
                )
            )

            if existing and not payload.force_new_episode:
                data = json.loads(existing.data_json)

                data["evaluation_count"] = data.get("evaluation_count", 1) + 1

                data["last_evaluated_at"] = now.isoformat()

                existing.data_json = json.dumps(data)

                existing.updated_at = now

                continue

            if existing and payload.force_new_episode:
                dedup_key = f"{p.id}:RULE-MARGIN-COMPRESSION-v1:ep-{now.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"

            ins_id = uuid4()

            record = {
                "id": str(ins_id),
                "company_id": str(current_user.company_id),
                "dedup_key": dedup_key,
                "rule_id": "RULE-MARGIN-COMPRESSION-v1",
                "version": 1,
                "entity_type": "Product",
                "entity_id": str(p.id),
                "title": f"Margen bruto comprimido en {p.name}",
                "cifra_clave": f"{margin_pct:.2f}%",
                "period": "Catálogo activo",
                "severity": "high",
                "status": "pending",
                "evaluation_count": 1,
                "detected_at": now.isoformat(),
                "last_evaluated_at": now.isoformat(),
                "cost_confidential": False,
                "rule_definition": rule.to_dict(),
                "evidence_data": {
                    "metric_name": "list_margin_pct",
                    "current_value": f"{margin_pct:.2f}",
                    "baseline_value": f"{threshold:.2f}",
                    "numerator": f"{margin:.2f}",
                    "denominator": f"{p.unit_price:.2f}",
                    "unit_cost": f"{p.unit_cost:.2f}",
                    "difference_pct": f"{(margin_pct - threshold):.2f}",
                    "threshold": f"{threshold:.2f}",
                    "sample_size": 1,
                    "cutoff_date": now.isoformat(),
                    "filters_applied": {"is_active": True},
                },
                "evidence": f"Margen actual de {margin_pct:.2f}% es inferior al umbral mínimo de {threshold:.2f}%",
                "observation": f"El producto {p.name} (SKU {p.sku}) presenta un margen de precio de lista de {margin_pct:.2f}% frente al costo de {p.unit_cost:.2f} USD.",
                "interpretation": "La diferencia estrecha entre precio de lista y costo unitario compromete la rentabilidad comercial estándar sin descuentos. No se atribuye a desviaciones operativas externas.",
                "suggested_action": f"Ajustar precio de lista o negociar costo unitario de {p.unit_cost:.2f} USD con proveedor antes de cotizar.",
                "suggested_actions": [
                    {
                        "action_id": f"act-price-{p.id}",
                        "action_type": "draft_price_change",
                        "title": "Borrador de ajuste de precio",
                        "description": f"Elaborar propuesta de precio para restaurar margen al {threshold:.2f}%",
                        "projected_impact": f"Incremento potencial de margen al {threshold:.2f}%",
                        "requires_manual_confirmation": True,
                        "financial_auto_execution": False,
                        "draft_preview": {
                            "entity_type": "Product",
                            "entity_id": str(p.id),
                            "current_price": str(p.unit_price),
                            "current_cost": str(p.unit_cost),
                            "suggested_price": str(round(p.unit_cost / Decimal("0.80"), 2)),
                            "requires_manual_confirmation": True,
                        },
                    }
                ],
                "feedback": [],
                "lifecycle_history": [
                    {
                        "previous_status": None,
                        "new_status": "pending",
                        "reason": "Detección inicial por regla de margen de catálogo",
                        "changed_by": str(current_user.user_id),
                        "changed_at": now.isoformat(),
                    }
                ],
            }

            db.add(
                AnalyticsArtifact(
                    id=ins_id,
                    company_id=current_user.company_id,
                    kind="insight",
                    artifact_key=dedup_key,
                    version=1,
                    status="pending",
                    data_json=json.dumps(record),
                    created_by=current_user.user_id,
                )
            )

            generated.append(record)

    sale_lines = (
        db.execute(
            select(SaleLineModel)
            .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleModel.company_id == current_user.company_id, SaleModel.status.in_(["confirmed", "paid"]))
        )
        .scalars()
        .all()
    )

    product_lines_map: dict[UUID, list[SaleLineModel]] = {}

    for line in sale_lines:
        product_lines_map.setdefault(line.product_id, []).append(line)

    for p_id, lines in product_lines_map.items():
        hist_count = len(lines)

        if hist_count >= 1:
            tot_rev = sum(l.quantity * l.unit_price_snapshot for l in lines)

            tot_cost = sum(l.quantity * l.unit_cost_snapshot for l in lines)

            if tot_rev > 0:
                hist_margin = tot_rev - tot_cost

                hist_margin_pct = hist_margin / tot_rev * Decimal("100")

            else:
                hist_margin = Decimal("0.00")

                hist_margin_pct = Decimal("0.00")

            hist_rule = RULE_CATALOG["RULE-HISTORICAL-MARGIN-DIP-v1"]

            hist_threshold = hist_rule.default_threshold

            if hist_margin_pct < hist_threshold:
                p_obj = db.get(ProductModel, p_id)

                p_name = p_obj.name if p_obj else f"Producto {p_id}"

                p_sku = p_obj.sku if p_obj else "N/A"

                dedup_key = f"{p_id}:RULE-HISTORICAL-MARGIN-DIP-v1"

                existing_hist = db.scalar(
                    select(AnalyticsArtifact).where(
                        AnalyticsArtifact.company_id == current_user.company_id,
                        AnalyticsArtifact.kind == "insight",
                        AnalyticsArtifact.artifact_key == dedup_key,
                        AnalyticsArtifact.version == 1,
                    )
                )

                if existing_hist and not payload.force_new_episode:
                    data = json.loads(existing_hist.data_json)

                    data["evaluation_count"] = data.get("evaluation_count", 1) + 1

                    data["last_evaluated_at"] = now.isoformat()

                    existing_hist.data_json = json.dumps(data)

                    existing_hist.updated_at = now

                    continue

                if existing_hist and payload.force_new_episode:
                    dedup_key = (
                        f"{p_id}:RULE-HISTORICAL-MARGIN-DIP-v1:ep-{now.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
                    )

                ins_id = uuid4()

                record = {
                    "id": str(ins_id),
                    "company_id": str(current_user.company_id),
                    "dedup_key": dedup_key,
                    "rule_id": "RULE-HISTORICAL-MARGIN-DIP-v1",
                    "version": 1,
                    "entity_type": "Product",
                    "entity_id": str(p_id),
                    "title": f"Margen histórico comprimido en {p_name}",
                    "cifra_clave": f"{hist_margin_pct:.2f}%",
                    "period": "Ventas históricas cerradas",
                    "severity": "high",
                    "status": "pending",
                    "evaluation_count": 1,
                    "detected_at": now.isoformat(),
                    "last_evaluated_at": now.isoformat(),
                    "cost_confidential": False,
                    "rule_definition": hist_rule.to_dict(),
                    "evidence_data": {
                        "metric_name": "historical_margin_pct",
                        "current_value": f"{hist_margin_pct:.2f}",
                        "baseline_value": f"{hist_threshold:.2f}",
                        "numerator": f"{hist_margin:.2f}",
                        "denominator": f"{tot_rev:.2f}",
                        "difference_pct": f"{(hist_margin_pct - hist_threshold):.2f}",
                        "threshold": f"{hist_threshold:.2f}",
                        "sample_size": hist_count,
                        "cutoff_date": now.isoformat(),
                        "filters_applied": {"sale_status": ["confirmed", "paid"]},
                    },
                    "evidence": f"Margen histórico de {hist_margin_pct:.2f}% es inferior al umbral de {hist_threshold:.2f}% en {hist_count} ventas",
                    "observation": f"El producto {p_name} (SKU {p_sku}) registró un margen histórico realizado de {hist_margin_pct:.2f}% en {hist_count} transacciones cerradas.",
                    "interpretation": "Descuentos comerciales acumulados o variaciones temporales en costo redujeron la rentabilidad efectiva por debajo del umbral mínimo. No se atribuye automáticamente al desempeño del vendedor.",
                    "suggested_action": f"Revisar el historial de descuentos aplicados a {p_name} y evaluar topes de descuento en cotizaciones.",
                    "suggested_actions": [
                        {
                            "action_id": f"act-hist-{p_id}",
                            "action_type": "open_catalog",
                            "title": "Auditoría de precios y descuentos",
                            "description": "Examinar líneas de venta para identificar descuentos excepcionales",
                            "projected_impact": "Control de erosión de margen en ventas futuras",
                            "requires_manual_confirmation": True,
                            "financial_auto_execution": False,
                            "draft_preview": {
                                "entity_type": "Product",
                                "entity_id": str(p_id),
                                "sample_size": hist_count,
                                "historical_margin": f"{hist_margin_pct:.2f}%",
                                "requires_manual_confirmation": True,
                            },
                        }
                    ],
                    "feedback": [],
                    "lifecycle_history": [
                        {
                            "previous_status": None,
                            "new_status": "pending",
                            "reason": "Detección por regla de margen histórico realizado",
                            "changed_by": str(current_user.user_id),
                            "changed_at": now.isoformat(),
                        }
                    ],
                }

                db.add(
                    AnalyticsArtifact(
                        id=ins_id,
                        company_id=current_user.company_id,
                        kind="insight",
                        artifact_key=dedup_key,
                        version=1,
                        status="pending",
                        data_json=json.dumps(record),
                        created_by=current_user.user_id,
                    )
                )

                generated.append(record)

    db.commit()

    total = db.scalar(
        select(func.count())
        .select_from(AnalyticsArtifact)
        .where(AnalyticsArtifact.company_id == current_user.company_id, AnalyticsArtifact.kind == "insight")
    )

    return {
        "status": "evaluated",
        "generated_count": len(generated),
        "total_active_insights": total,
        "suppressed_by_cooldown_count": cooldown_count,
        "suppression_log": suppression_log,
    }
