import base64
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status


def encode_cursor(created_at: datetime, record_id: UUID, scope_hash: Optional[str] = None) -> str:
    iso_time = created_at.isoformat()
    raw = f"{iso_time}|{str(record_id)}"
    if scope_hash:
        raw += f"|{scope_hash}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str, expected_scope_hash: Optional[str] = None) -> tuple[datetime, UUID]:
    if not cursor_str or not cursor_str.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cursor de paginacion vacio o invalido"
        )
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        parts = raw.split("|")
        if len(parts) < 2:
            raise ValueError("Formato de cursor incompleto")
        time_part, id_part = parts[0], parts[1]
        scope_part = parts[2] if len(parts) > 2 else None

        if expected_scope_hash and scope_part != expected_scope_hash:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El cursor no corresponde al ambito o filtro solicitado"
            )

        parsed_time = datetime.fromisoformat(time_part)
        parsed_id = UUID(id_part)
        return parsed_time, parsed_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cursor de paginacion invalido o corrupto"
        )
