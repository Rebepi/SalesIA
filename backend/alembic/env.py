import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.database import Base
import salesia.shared.infrastructure.models
import salesia.modules.seguridad.infrastructure.models
import salesia.shared.infrastructure.transactions
import salesia.modules.inventario.infrastructure_models
import salesia.modules.operaciones.infrastructure_models
import salesia.modules.catalogo.infrastructure_models
import salesia.modules.clientes.infrastructure.models
import salesia.modules.finanzas.infrastructure_models
import salesia.modules.operaciones.infrastructure.models.campos
import salesia.modules.operaciones.infrastructure.models.politicas_aprobacion
import salesia.modules.operaciones.infrastructure.models.planificacion
import salesia.modules.inventario.infrastructure.models.catalogo_proveedor

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
