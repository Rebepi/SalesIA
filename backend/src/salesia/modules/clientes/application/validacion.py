import re
from typing import Optional

from fastapi import HTTPException


def validate_customer_document(doc_type: str, doc_number: str) -> None:
    dt = doc_type.upper().strip()
    dn = doc_number.strip()
    if dt == "RUC":
        if not (dn.isdigit() and len(dn) == 11):
            raise HTTPException(
                422, {"field": "doc_number", "rule": "RUC debe contener exactamente 11 dígitos numéricos"}
            )
    elif dt == "DNI":
        if not (dn.isdigit() and len(dn) == 8):
            raise HTTPException(
                422, {"field": "doc_number", "rule": "DNI debe contener exactamente 8 dígitos numéricos"}
            )
    elif dt in ("PASSPORT", "PASAPORTE"):
        if not (len(dn) >= 6 and len(dn) <= 16 and re.match(r"^[A-Za-z0-9]+$", dn)):
            raise HTTPException(
                422, {"field": "doc_number", "rule": "Pasaporte debe ser alfanumérico entre 6 y 16 caracteres"}
            )
    elif dt in ("NONE", "SIN_DOCUMENTO"):
        if dn not in ("SIN_DOCUMENTO", "00000000", "0"):
            raise HTTPException(
                422, {"field": "doc_number", "rule": "Cliente sin documento solo permitido bajo código SIN_DOCUMENTO"}
            )
    elif len(dn) < 3 or len(dn) > 32:
        raise HTTPException(
            422, {"field": "doc_number", "rule": "Número de documento debe tener entre 3 y 32 caracteres"}
        )


def validate_customer_phone(phone: Optional[str]) -> None:
    if not phone:
        return
    cleaned = phone.strip()
    if not re.match(r"^\+?[0-9\s\-\(\)\.]{6,32}$", cleaned):
        raise HTTPException(
            422,
            {
                "field": "phone",
                "rule": "Teléfono debe contener un formato internacional válido de entre 6 y 32 caracteres",
            },
        )


def validate_customer_email(email: Optional[str]) -> None:
    if not email:
        return
    cleaned = email.strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned) or len(cleaned) > 255:
        raise HTTPException(422, {"field": "email", "rule": "Correo electrónico con formato RFC inválido"})
