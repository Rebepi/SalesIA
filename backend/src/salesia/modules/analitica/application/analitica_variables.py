from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.statistics import VariableScale, compute_statistical_summary
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import PaymentModel, SaleLineModel, SaleModel


def get_analytics_variables(current_user: AuthenticatedUser, db: Session):
    sale_rows = db.execute(
        select(SaleModel.total_amount, SaleModel.customer_id, SaleModel.status).where(
            SaleModel.company_id == current_user.company_id
        )
    ).all()

    quantities = list(
        db.scalars(
            select(SaleLineModel.quantity)
            .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
            .where(SaleModel.company_id == current_user.company_id)
        ).all()
    )

    payment_methods = list(
        db.scalars(select(PaymentModel.payment_method).where(PaymentModel.company_id == current_user.company_id)).all()
    )

    def numeric_summary(values: list[Decimal]) -> dict[str, Any]:

        if not values:
            return {
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "mode": None,
                "distinct_count": 0,
                "null_count": 0,
            }

        summary = compute_statistical_summary(values)

        counts: dict[str, int] = {}

        for value in values:
            key = str(value)

            counts[key] = counts.get(key, 0) + 1

        mode_value = max(counts, key=counts.get) if counts else None

        return {
            "mean": str(summary.mean),
            "median": str(summary.median),
            "min": str(summary.minimum),
            "max": str(summary.maximum),
            "mode": mode_value,
            "distinct_count": len(counts),
            "null_count": 0,
        }

    def categorical_summary(values: list[str]) -> dict[str, Any]:

        counts: dict[str, int] = {}

        for value in values:
            key = str(value)

            counts[key] = counts.get(key, 0) + 1

        total = len(values)

        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

        return {
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "mode": ordered[0][0] if ordered else None,
            "distinct_count": len(counts),
            "null_count": 0,
            "frequencies": [
                {
                    "value": value,
                    "count": count,
                    "pct": str((Decimal(count) * Decimal("100") / Decimal(total)).quantize(Decimal("0.01")))
                    if total
                    else "0.00",
                }
                for value, count in ordered
            ],
        }

    totals = [row.total_amount for row in sale_rows if row.total_amount is not None]

    customer_ids = [str(row.customer_id) for row in sale_rows if row.customer_id is not None]

    statuses = [row.status for row in sale_rows if row.status]

    variable_specs = [
        {
            "id": "sales.total_amount",
            "name": "total_amount",
            "label": "Importe total de venta",
            "scale": VariableScale.QUANTITATIVE_CONTINUOUS.value,
            "scale_label": "Cuantitativa continua",
            "data_type": "DECIMAL(20,6)",
            "source_table": "sales",
            "description": "Monto total registrado por operación comercial.",
            "allowed_operations": ["media", "mediana", "varianza", "desviación estándar", "cuartiles"],
            "sample_values": [str(value) for value in totals[:5]],
            "summary": numeric_summary(totals),
        },
        {
            "id": "sale_lines.quantity",
            "name": "quantity",
            "label": "Cantidad de unidades vendidas",
            "scale": VariableScale.QUANTITATIVE_DISCRETE.value,
            "scale_label": "Cuantitativa discreta",
            "data_type": "DECIMAL(20,6)",
            "source_table": "sale_lines",
            "description": "Cantidad registrada en cada línea de venta.",
            "allowed_operations": ["media", "mediana", "moda", "suma", "desviación estándar"],
            "sample_values": [str(value) for value in quantities[:5]],
            "summary": numeric_summary(quantities),
        },
        {
            "id": "payments.payment_method",
            "name": "payment_method",
            "label": "Método de pago",
            "scale": VariableScale.QUALITATIVE_NOMINAL.value,
            "scale_label": "Cualitativa nominal",
            "data_type": "VARCHAR(32)",
            "source_table": "payments",
            "description": "Canal utilizado para registrar el cobro.",
            "allowed_operations": ["frecuencias", "porcentajes", "moda", "tabla de contingencia"],
            "sample_values": payment_methods[:5],
            "summary": categorical_summary(payment_methods),
        },
        {
            "id": "sales.customer_id",
            "name": "customer_id",
            "label": "Identificador de cliente",
            "scale": VariableScale.QUALITATIVE_NOMINAL.value,
            "scale_label": "Cualitativa nominal",
            "data_type": "UUID",
            "source_table": "sales",
            "description": "Identificador de agrupación de la entidad cliente.",
            "allowed_operations": ["recuento único", "agrupación", "frecuencia"],
            "sample_values": [f"{value[:8]}…" for value in customer_ids[:5]],
            "summary": categorical_summary(customer_ids),
        },
        {
            "id": "sales.status",
            "name": "status",
            "label": "Estado de la venta",
            "scale": VariableScale.QUALITATIVE_ORDINAL.value,
            "scale_label": "Cualitativa ordinal",
            "data_type": "VARCHAR(32)",
            "source_table": "sales",
            "description": "Etapa alcanzada por la operación dentro de su ciclo comercial.",
            "allowed_operations": ["frecuencias", "porcentajes", "moda", "frecuencia acumulada"],
            "sample_values": statuses[:5],
            "summary": categorical_summary(statuses),
        },
    ]

    return {
        "items": variable_specs,
        "count": len(variable_specs),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
