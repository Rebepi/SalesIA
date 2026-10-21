from pathlib import Path

from salesia.shared.infrastructure.config import AppSettings, BACKEND_ROOT, settings


def test_default_private_storage_is_inside_backend():
    expected_path = (BACKEND_ROOT / "private_storage").resolve()

    assert Path(settings.private_storage_path) == expected_path
    assert expected_path.is_dir()


def test_relative_private_storage_is_resolved_from_backend():
    configured = AppSettings(private_storage_path="private_storage", _env_file=None)
    expected_path = (BACKEND_ROOT / "private_storage").resolve()

    assert Path(configured.private_storage_path) == expected_path
    assert expected_path.is_dir()


def test_absolute_private_storage_override_is_preserved(tmp_path):
    configured = AppSettings(private_storage_path=str(tmp_path), _env_file=None)

    assert Path(configured.private_storage_path) == tmp_path.resolve()
    assert tmp_path.is_dir()
