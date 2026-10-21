"""Run the test suite against an isolated, migrated PostgreSQL database."""

from __future__ import annotations

import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
import psycopg2
from psycopg2 import sql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
_CREATED_DATABASE: str | None = None
_ADMIN_DSN: str | None = None


def _dotenv_database_url() -> str | None:
    env_file = BACKEND_ROOT / ".env"
    if not env_file.exists():
        return None
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _without_sqlalchemy_driver(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg://", "postgresql://"
    )


def _with_database(url: str, database: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, f"/{database}", parsed.query, parsed.fragment))


def _prepare_database() -> None:
    global _CREATED_DATABASE, _ADMIN_DSN
    explicit = os.getenv("SALESIA_TEST_DATABASE_URL")
    if explicit:
        os.environ["DATABASE_URL"] = explicit
        return

    source_url = os.getenv("DATABASE_URL") or _dotenv_database_url()
    if not source_url or not source_url.startswith("postgresql"):
        raise RuntimeError(
            "La suite requiere PostgreSQL. Configure SALESIA_TEST_DATABASE_URL o DATABASE_URL."
        )

    database_name = f"salesia_pytest_{os.getpid()}_{secrets.token_hex(4)}"
    sync_source = _without_sqlalchemy_driver(source_url)
    _ADMIN_DSN = _with_database(sync_source, "postgres")
    admin = psycopg2.connect(_ADMIN_DSN)
    admin.autocommit = True
    try:
        with admin.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
    finally:
        admin.close()

    _CREATED_DATABASE = database_name
    os.environ["DATABASE_URL"] = _with_database(source_url, database_name)


_prepare_database()


def _drop_created_database() -> None:
    if not _CREATED_DATABASE or not _ADMIN_DSN:
        return
    admin = psycopg2.connect(_ADMIN_DSN)
    admin.autocommit = True
    try:
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s",
                (_CREATED_DATABASE,),
            )
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(_CREATED_DATABASE)))
    finally:
        admin.close()


def pytest_configure(config) -> None:
    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    try:
        command.upgrade(alembic_config, "head")
    except Exception:
        _drop_created_database()
        raise


def pytest_sessionfinish(session, exitstatus) -> None:
    if not _CREATED_DATABASE or not _ADMIN_DSN:
        return
    try:
        from salesia.shared.infrastructure.database import get_async_engine, get_sync_engine

        get_sync_engine().dispose()
        async_engine = get_async_engine()
        if async_engine:
            import asyncio

            asyncio.run(async_engine.dispose())
    except Exception:
        pass

    _drop_created_database()
