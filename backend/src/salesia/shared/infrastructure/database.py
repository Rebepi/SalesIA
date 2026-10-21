from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from uuid import UUID
from sqlalchemy import DateTime, MetaData, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from salesia.shared.infrastructure.config import settings

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)


class Base(DeclarativeBase):
    metadata = metadata


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class TenantScopedMixin:
    company_id: Mapped[UUID] = mapped_column(nullable=False, index=True)


_async_engine = None
_sync_engine = None
_async_session_factory = None
_sync_session_factory = None


def configure_sqlite(connection, record):
    connection.isolation_level = None
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=30000")
    try:
        cursor.execute("CREATE TRIGGER IF NOT EXISTS audit_logs_no_update BEFORE UPDATE ON audit_logs BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END;")
        cursor.execute("CREATE TRIGGER IF NOT EXISTS audit_logs_no_delete BEFORE DELETE ON audit_logs BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END;")
    except Exception:
        pass
    try:
        cursor.execute("PRAGMA table_info(notifications)")
        notif_cols = {row[1] for row in cursor.fetchall()}
        if notif_cols:
            if "priority" not in notif_cols:
                cursor.execute("ALTER TABLE notifications ADD COLUMN priority VARCHAR(32) DEFAULT 'normal'")
            if "category" not in notif_cols:
                cursor.execute("ALTER TABLE notifications ADD COLUMN category VARCHAR(64) DEFAULT 'general'")
            if "resource_type" not in notif_cols:
                cursor.execute("ALTER TABLE notifications ADD COLUMN resource_type VARCHAR(64)")
            if "resource_id" not in notif_cols:
                cursor.execute("ALTER TABLE notifications ADD COLUMN resource_id CHAR(32)")
        cursor.execute("PRAGMA table_info(attachments)")
        att_cols = {row[1] for row in cursor.fetchall()}
        if att_cols:
            if "scan_status" not in att_cols:
                cursor.execute("ALTER TABLE attachments ADD COLUMN scan_status VARCHAR(32) DEFAULT 'clean'")
            if "classification" not in att_cols:
                cursor.execute("ALTER TABLE attachments ADD COLUMN classification VARCHAR(32) DEFAULT 'internal'")
            if "owner_id" not in att_cols:
                cursor.execute("ALTER TABLE attachments ADD COLUMN owner_id CHAR(32)")
    except Exception:
        pass
    cursor.close()


def begin_sqlite(connection):
    connection.exec_driver_sql("BEGIN")


def postgres_session_settings():
    return {
        "lock_timeout": str(settings.database_lock_timeout_seconds * 1000),
        "statement_timeout": str(settings.database_statement_timeout_seconds * 1000),
        "idle_in_transaction_session_timeout": str(settings.database_idle_transaction_timeout_seconds * 1000),
        "application_name": "salesia",
    }


def get_async_engine():
    global _async_engine
    if _async_engine is None:
        is_sqlite = settings.database_url.startswith("sqlite")
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        if settings.database_url.startswith("postgresql+asyncpg:"):
            connect_args = {"timeout": settings.database_connect_timeout_seconds, "command_timeout": settings.database_statement_timeout_seconds, "server_settings": postgres_session_settings()}
        _async_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            connect_args=connect_args,
            poolclass=NullPool
        )
        if is_sqlite:
            event.listen(_async_engine.sync_engine, "connect", configure_sqlite)
            event.listen(_async_engine.sync_engine, "begin", begin_sqlite)
    return _async_engine


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        is_sqlite = settings.database_url.startswith("sqlite")
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        sync_database_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")
        if sync_database_url.startswith("postgresql://") or sync_database_url.startswith("postgres://"):
            try:
                import psycopg
            except ImportError:
                sync_database_url = sync_database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
                sync_database_url = sync_database_url.replace("postgres://", "postgresql+psycopg2://", 1)
        engine_options = {}
        if sync_database_url.startswith(("postgresql:", "postgresql+", "postgres:")):
            connect_args = {"connect_timeout": settings.database_connect_timeout_seconds, "options": " ".join(f"-c {name}={value}" for name, value in postgres_session_settings().items())}
            engine_options = {"pool_size": settings.database_pool_size, "max_overflow": settings.database_max_overflow, "pool_timeout": settings.database_pool_timeout_seconds, "pool_pre_ping": True}
        _sync_engine = create_engine(
            sync_database_url,
            echo=settings.debug,
            connect_args=connect_args,
            **engine_options
        )
        if is_sqlite:
            event.listen(_sync_engine, "connect", configure_sqlite)
            event.listen(_sync_engine, "begin", begin_sqlite)
    return _sync_engine


def get_async_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _async_session_factory


def get_sync_session_factory():
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _sync_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> Generator[Session, None, None]:
    factory = get_sync_session_factory()
    with factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def reset_engines():
    global _async_engine, _sync_engine, _async_session_factory, _sync_session_factory
    _async_engine = None
    _sync_engine = None
    _async_session_factory = None
    _sync_session_factory = None


def __getattr__(name: str):
    if name == "engine":
        return get_async_engine()
    if name == "sync_engine":
        return get_sync_engine()
    if name == "async_session_factory":
        return get_async_session_factory()
    if name == "sync_session_factory":
        return get_sync_session_factory()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
