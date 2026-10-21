from pathlib import Path

from salesia.shared.infrastructure.config import settings


def private_root():

    root = Path(settings.private_storage_path).resolve()

    root.mkdir(parents=True, exist_ok=True)

    return root
