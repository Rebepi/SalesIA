import io
import zipfile
from pathlib import Path

from fastapi import HTTPException


def scan_uploaded_file(path: Path, mime_type: str, file_name: str):

    data = path.read_bytes()

    if data.startswith(b"MZ") or data.startswith(b"\x7fELF"):
        raise HTTPException(422, "Ejecutable no permitido; archivo puesto en cuarentena.")

    if mime_type in ("image/svg+xml", "text/html") or file_name.endswith((".svg", ".html")):
        lower_data = data.lower()

        if (
            b"<script" in lower_data
            or b"javascript:" in lower_data
            or b"onload=" in lower_data
            or b"onerror=" in lower_data
        ):
            raise HTTPException(422, "Contenido de script activo no permitido; archivo puesto en cuarentena.")

    if mime_type == "application/zip" or file_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                total_uncompressed = sum(info.file_size for info in zf.infolist())

                if total_uncompressed > 100_000_000 or (len(data) > 0 and total_uncompressed / len(data) > 100):
                    raise HTTPException(422, "Archivo zip potencialmente expansivo (zip bomb).")

                for info in zf.infolist():
                    if ".." in info.filename or info.filename.startswith("/"):
                        raise HTTPException(422, "Ruta no segura detectada en archivo comprimido.")

        except zipfile.BadZipFile:
            raise HTTPException(422, "Archivo comprimido corrupto o inválido.")
