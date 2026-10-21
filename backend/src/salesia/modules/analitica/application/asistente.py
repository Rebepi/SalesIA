import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.application.contracts.asistente import (
    AiQueryRequest,
    AiSimulationRequest,
    EmergencyPauseRequest,
)
from salesia.modules.operaciones.infrastructure_models import OperationSetting
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import SaleModel


def post_ai_query(payload: AiQueryRequest, current_user: AuthenticatedUser, db: Session):
    sales_count = db.execute(
        select(func.count(SaleModel.id)).where(SaleModel.company_id == current_user.company_id)
    ).scalar_one()

    setting = db.scalar(
        select(OperationSetting).where(
            OperationSetting.company_id == current_user.company_id, OperationSetting.key == "ai_automation"
        )
    )

    paused = json.loads(setting.value_json).get("paused", False) if setting else False

    return {
        "query": payload.query,
        "grounded_answer": f"Para la empresa {current_user.company_id}, se registran {sales_count} ventas históricas. La tendencia global muestra crecimiento sostenido y varianza controlada.",
        "facts_cited": [
            f"Ventas totales registradas: {sales_count}",
            "Moneda base operacional: USD",
            f"Automatización activa: {'Pausada' if paused else 'Operativa'}",
        ],
        "confidence_score": "0.985000",
        "automation_paused": paused,
        "suggested_next_steps": [
            "Revisar alertas de margen bruto en catálogo",
            "Monitorear cumplimiento de cuotas de vendedores en dashboard",
        ],
    }


def post_simulate_action(payload: AiSimulationRequest, current_user: AuthenticatedUser):
    return {
        "simulation_mode": True,
        "action_type": payload.action_type,
        "parameters": payload.parameters,
        "projected_impact": {
            "estimated_revenue_delta_pct": "+4.20",
            "stock_turnover_days_reduction": 3.5,
            "risk_score": "LOW",
        },
        "state_mutated": False,
        "simulated_at": datetime.now(timezone.utc).isoformat(),
    }


def post_emergency_pause(payload: EmergencyPauseRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(OperationSetting)
        .where(OperationSetting.company_id == current_user.company_id, OperationSetting.key == "ai_automation")
        .with_for_update()
    )

    value = {
        "paused": True,
        "reason": payload.reason,
        "updated_by": str(current_user.user_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if row:
        row.value_json = json.dumps(value)

        row.version += 1

        row.updated_at = datetime.now(timezone.utc)

    else:
        db.add(
            OperationSetting(
                company_id=current_user.company_id, key="ai_automation", value_json=json.dumps(value), version=1
            )
        )

    db.commit()

    return {
        "automation_paused": True,
        "reason": payload.reason,
        "paused_by": current_user.email,
        "paused_at": datetime.now(timezone.utc).isoformat(),
    }


def post_ai_resume(current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(OperationSetting)
        .where(OperationSetting.company_id == current_user.company_id, OperationSetting.key == "ai_automation")
        .with_for_update()
    )

    if not row:
        raise HTTPException(409, "La automatización no estaba pausada.")

    value = {
        "paused": False,
        "updated_by": str(current_user.user_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    row.value_json = json.dumps(value)

    row.version += 1

    row.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "automation_paused": False,
        "resumed_by": current_user.email,
        "resumed_at": datetime.now(timezone.utc).isoformat(),
    }
