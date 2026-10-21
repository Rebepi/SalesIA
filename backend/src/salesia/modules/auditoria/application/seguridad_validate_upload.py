import base64
import re
from uuid import uuid4

from fastapi import HTTPException, status

from salesia.modules.auditoria.application.contracts.seguridad_validate_upload import FileUploadValidationRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def validate_file_upload(payload: FileUploadValidationRequest, current_user: AuthenticatedUser):
    try:
        raw_bytes = base64.b64decode(payload.content_base64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Contenido base64 inválido")
    if len(raw_bytes) > payload.max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El tamaño del archivo ({len(raw_bytes)} bytes) excede el límite permitido de {payload.max_size_bytes} bytes",
        )
    lower_name = payload.filename.lower()
    dangerous_extensions = (".exe", ".bat", ".cmd", ".sh", ".php", ".py", ".elf", ".bin", ".dll", ".so", ".vbs", ".ps1")
    if any(lower_name.endswith(ext) for ext in dangerous_extensions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Extensión de archivo prohibida por política de seguridad (archivos ejecutables o scripts no permitidos)",
        )
    if raw_bytes.startswith(b"\x7fELF") or raw_bytes.startswith(b"MZ") or raw_bytes.startswith(b"#!"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Firma binaria ejecutable detectada. Carga rechazada por el analizador estático.",
        )
    detected_mime = "application/octet-stream"
    if raw_bytes.startswith(b"%PDF-"):
        detected_mime = "application/pdf"
    elif raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif raw_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
    elif lower_name.endswith(".csv"):
        detected_mime = "text/csv"
    elif lower_name.endswith(".txt"):
        detected_mime = "text/plain"

    storage_token = uuid4().hex
    safe_key = f"isolated-uploads/{current_user.company_id}/{storage_token}/{re.sub(r'[^a-zA-Z0-9._-]', '_', payload.filename)}"
    return {
        "is_safe": True,
        "filename": payload.filename,
        "size_bytes": len(raw_bytes),
        "detected_mime": detected_mime,
        "storage_path": safe_key,
        "isolated": True,
    }
