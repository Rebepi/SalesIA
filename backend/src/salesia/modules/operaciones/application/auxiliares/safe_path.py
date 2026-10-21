from fastapi import HTTPException

from salesia.modules.operaciones.application.auxiliares.private_root import private_root


def safe_path(folder, identifier):

    root = private_root()

    directory = (root / folder).resolve()

    directory.mkdir(parents=True, exist_ok=True)

    path = (directory / identifier).resolve()

    if root not in path.parents:
        raise HTTPException(400, "Ruta de almacenamiento inválida.")

    return path
