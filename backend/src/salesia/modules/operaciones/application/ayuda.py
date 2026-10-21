from typing import Optional

from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings


def get_contextual_help(screen: Optional[str], error_code: Optional[str], current_user: AuthenticatedUser, db: Session):
    guides = [
        {
            "screen": "sales",
            "error_code": None,
            "role": "salesperson",
            "version": "1.0",
            "title": "Guía de Ventas",
            "content": "Verifique el stock antes de confirmar cotizaciones a clientes.",
        },
        {
            "screen": "operations",
            "error_code": None,
            "role": "all",
            "version": "1.0",
            "title": "Guía Operativa",
            "content": "Los respaldos y restauraciones requieren llaves AESGCM configuradas.",
        },
        {
            "screen": "imports",
            "error_code": "ERR_CSV_COLUMNS",
            "role": "all",
            "version": "1.0",
            "title": "Columnas CSV",
            "content": "El archivo debe tener cabeceras en minúsculas y formato UTF-8.",
        },
        {
            "screen": "security",
            "error_code": None,
            "role": "all",
            "version": "1.0",
            "title": "Autenticación MFA",
            "content": "Configure su aplicación TOTP y almacene los códigos de respaldo.",
        },
    ]

    matched = [
        g
        for g in guides
        if (not screen or g["screen"] == screen)
        and (not error_code or g["error_code"] == error_code)
        and (g["role"] in ("all", current_user.role))
    ]

    return {
        "screen": screen,
        "error_code": error_code,
        "role": current_user.role,
        "version": settings.app_version,
        "articles": matched,
    }
