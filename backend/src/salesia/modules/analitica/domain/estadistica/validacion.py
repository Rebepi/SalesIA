from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Sequence

from salesia.modules.analitica.domain.estadistica.tipos import VariableScale
from salesia.shared.domain.exceptions import IncompatibleVariableScaleException


def sanitize_numeric_values(values: Sequence[Any], null_policy: str = "skip") -> tuple[list[Decimal], int]:
    cleaned: list[Decimal] = []
    null_count = 0

    for item in values:
        if item is None:
            if null_policy == "error":
                raise ValueError("La muestra contiene valores nulos bajo politica de error")
            elif null_policy == "zero":
                cleaned.append(Decimal("0.000000"))
            else:
                null_count += 1
            continue

        raw_str = str(item).strip()
        if raw_str.lower() in ("", "none", "null", "nan", "na", "<na>", "nat"):
            if null_policy == "error":
                raise ValueError("La muestra contiene valores no validos bajo politica de error")
            elif null_policy == "zero":
                cleaned.append(Decimal("0.000000"))
            else:
                null_count += 1
            continue

        if raw_str.lower() in ("inf", "-inf", "+inf", "infinity", "-infinity"):
            if null_policy == "error":
                raise ValueError("La muestra contiene valores infinitos bajo politica de error")
            elif null_policy == "zero":
                cleaned.append(Decimal("0.000000"))
            else:
                null_count += 1
            continue

        try:
            d = Decimal(raw_str)
            if d.is_nan() or d.is_infinite():
                if null_policy == "error":
                    raise ValueError("La muestra contiene valores no finitos")
                elif null_policy == "zero":
                    cleaned.append(Decimal("0.000000"))
                else:
                    null_count += 1
            else:
                cleaned.append(d)
        except InvalidOperation:
            raise ValueError(f"Valor no numerico o formato ambiguo: {item}")

    return cleaned, null_count


def classify_variable(name: str, values: Optional[Sequence[Any]] = None) -> dict:
    clean_name = name.strip().lower()
    if clean_name in (
        "canal",
        "channel",
        "numero_documento",
        "document_number",
        "nro_documento",
        "codigo",
        "id",
        "ruc",
        "telefono",
        "phone",
    ):
        return {
            "name": name,
            "scale": VariableScale.QUALITATIVE_NOMINAL.value,
            "is_numeric_computable": False,
            "unit": "identificador_categorico",
            "justification": "Canal y número de documento son identificadores categóricos y no admiten media numérica aunque sus códigos sean dígitos.",
        }

    if clean_name in ("categoria_cliente", "nivel", "rango", "prioridad", "fase"):
        return {
            "name": name,
            "scale": VariableScale.QUALITATIVE_ORDINAL.value,
            "is_numeric_computable": False,
            "unit": "jerarquia_ordinal",
            "justification": "Variable cualitativa ordinal con jerarquía definida pero sin distancia métrica aditiva.",
        }

    if clean_name in ("cantidad", "items", "unidades", "tickets_count", "pedidos"):
        return {
            "name": name,
            "scale": VariableScale.QUANTITATIVE_DISCRETE.value,
            "is_numeric_computable": True,
            "unit": "unidades",
            "justification": "Conteo cuantitativo discreto con soporte entero no negativo.",
        }

    return {
        "name": name,
        "scale": VariableScale.QUANTITATIVE_CONTINUOUS.value,
        "is_numeric_computable": True,
        "unit": "monetaria/continua",
        "justification": "Magnitud cuantitativa continua con soporte en la recta real.",
    }


def validate_variable_scale_for_mean(name: str, scale: Optional[VariableScale] = None) -> None:
    clean_name = name.strip().lower()
    if clean_name in ("canal", "channel", "numero_documento", "document_number", "nro_documento", "codigo_canal"):
        raise IncompatibleVariableScaleException(
            "Canal y número de documento no admiten media numérica aunque sus códigos sean dígitos"
        )
    if scale in (VariableScale.QUALITATIVE_NOMINAL, VariableScale.QUALITATIVE_ORDINAL):
        raise IncompatibleVariableScaleException("Las variables cualitativas no admiten media numérica")


def validate_universe_consistency(universe_a: str, universe_b: str) -> dict:
    is_same = universe_a.strip().lower() == universe_b.strip().lower()
    return {
        "universe_a": universe_a,
        "universe_b": universe_b,
        "is_consistent": is_same,
        "warning": None
        if is_same
        else "No se deben comparar distribuciones de universos distintos sin aclaracion metodologica explicita.",
    }
