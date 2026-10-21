from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional

from salesia.modules.analitica.domain.probabilidades.configuracion import (
    ALLOWED_EVENT_FIELDS,
    ALLOWED_OPERATORS,
    DISALLOWED_PREDICTOR_FIELDS,
    DISALLOWED_SQL_PATTERNS,
)
from salesia.shared.domain.exceptions import InvariantViolationException


def validate_structured_condition(condition: dict[str, Any]) -> None:
    if not isinstance(condition, dict):
        raise InvariantViolationException("La condicion del evento debe ser una expresion estructurada valida")
    field = str(condition.get("field", "")).strip().lower()
    operator = str(condition.get("operator", "")).strip().lower()
    if not field or field not in ALLOWED_EVENT_FIELDS:
        raise InvariantViolationException(f"Campo no permitido en condicion estructurada: {field}")
    if not operator or operator not in ALLOWED_OPERATORS:
        raise InvariantViolationException(f"Operador no permitido en condicion estructurada: {operator}")
    val_str = str(condition.get("value", "")).lower()
    for pattern in DISALLOWED_SQL_PATTERNS:
        if pattern in val_str or pattern in field or pattern in operator:
            raise InvariantViolationException(
                "Expresion rechazada por contener patrones o palabras clave SQL no permitidas"
            )


def validate_temporal_leakage(
    predictor_fields: list[str], predictor_window_end: Optional[str] = None, outcome_window_start: Optional[str] = None
) -> None:
    for field in predictor_fields:
        clean = field.strip().lower()
        if clean in DISALLOWED_PREDICTOR_FIELDS:
            raise InvariantViolationException(
                f"Fuga temporal detectada: el campo predictor '{field}' ocurre despues del resultado de compra"
            )
    if predictor_window_end and outcome_window_start:
        if predictor_window_end > outcome_window_start:
            raise InvariantViolationException(
                "Fuga temporal detectada: la ventana del predictor no puede sobrepasar el inicio del resultado"
            )


def calculate_empirical_probability(
    sample_space_size: int,
    event_a_count: int,
    event_b_count: int,
    intersection_count: int,
    min_support_threshold: int = 30,
) -> dict[str, Any]:
    if sample_space_size <= 0:
        return {
            "is_defined": False,
            "reason": "Universo vacio: el espacio muestral no contiene observaciones elegibles",
            "sample_space_size": 0,
            "event_a_count": 0,
            "event_b_count": 0,
            "intersection_count": 0,
            "probability_a": None,
            "probability_b": None,
            "probability_intersection": None,
            "probability_union": None,
            "probability_complement_a": None,
            "probability_complement_b": None,
            "conditional_probability_a_given_b": None,
            "conditional_probability_b_given_a": None,
            "direction_labels": {
                "p_a_given_b": "P(A|B) no definida por universo vacio",
                "p_b_given_a": "P(B|A) no definida por universo vacio",
            },
            "contingency_table": None,
            "low_sample_warning": True,
            "warning_message": "El universo de analisis esta vacio",
            "causality_disclaimer": "No se puede inferir causalidad ni asociacion sobre un universo sin soporte muestral",
        }

    if event_a_count > sample_space_size or event_b_count > sample_space_size:
        raise InvariantViolationException("Los recuentos de eventos no pueden superar el tamano del universo")
    if intersection_count > min(event_a_count, event_b_count):
        raise InvariantViolationException("La interseccion no puede superar los recuentos individuales de eventos")

    n = Decimal(str(sample_space_size))
    na = Decimal(str(event_a_count))
    nb = Decimal(str(event_b_count))
    ni = Decimal(str(intersection_count))

    pa = (na / n).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    pb = (nb / n).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    p_inter = (ni / n).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    p_union = (pa + pb - p_inter).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    p_comp_a = (Decimal("1") - pa).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    p_comp_b = (Decimal("1") - pb).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    p_a_given_b = (
        (p_inter / pb).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        if pb > Decimal("0")
        else Decimal("0.000000")
    )
    p_b_given_a = (
        (p_inter / pa).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        if pa > Decimal("0")
        else Decimal("0.000000")
    )

    a_and_b = intersection_count
    a_and_not_b = event_a_count - intersection_count
    not_a_and_b = event_b_count - intersection_count
    not_a_and_not_b = sample_space_size - (event_a_count + event_b_count - intersection_count)

    low_sample = sample_space_size < min_support_threshold or min(event_a_count, event_b_count) < 5
    warn_text = None
    if low_sample:
        warn_text = f"Soporte muestral bajo (n={sample_space_size} < {min_support_threshold}). Resultados extremos como 100% o 0% tienen alta varianza y no son una ley universal"

    return {
        "is_defined": True,
        "reason": None,
        "sample_space_size": sample_space_size,
        "event_a_count": event_a_count,
        "event_b_count": event_b_count,
        "intersection_count": intersection_count,
        "probability_a": str(pa),
        "probability_b": str(pb),
        "probability_intersection": str(p_inter),
        "probability_union": str(p_union),
        "probability_complement_a": str(p_comp_a),
        "probability_complement_b": str(p_comp_b),
        "conditional_probability_a_given_b": str(p_a_given_b),
        "conditional_probability_b_given_a": str(p_b_given_a),
        "direction_labels": {
            "p_a_given_b": f"P(A|B) - Probabilidad de A dado B (denominador n(B)={event_b_count})",
            "p_b_given_a": f"P(B|A) - Probabilidad de B dado A (denominador n(A)={event_a_count})",
        },
        "contingency_table": {
            "a_and_b": a_and_b,
            "a_and_not_b": a_and_not_b,
            "not_a_and_b": not_a_and_b,
            "not_a_and_not_b": not_a_and_not_b,
            "total_a": event_a_count,
            "total_not_a": sample_space_size - event_a_count,
            "total_b": event_b_count,
            "total_not_b": sample_space_size - event_b_count,
            "grand_total": sample_space_size,
        },
        "low_sample_warning": low_sample,
        "warning_message": warn_text,
        "causality_disclaimer": "Asociacion condicional observada en el dataset. No implica que provocar artificialmente B cause A en la operacion comercial",
    }
