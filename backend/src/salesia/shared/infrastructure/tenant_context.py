from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_current_tenant(session: AsyncSession, company_id: UUID) -> None:
    session.info["current_company_id"] = company_id
    bind = session.bind
    if bind is not None and "postgresql" in bind.dialect.name:
        await session.execute(
            text("SELECT set_config('app.current_company_id', :cid, true)"),
            {"cid": str(company_id)}
        )


def get_current_tenant_id(session: AsyncSession) -> Optional[UUID]:
    return session.info.get("current_company_id")


@asynccontextmanager
async def scoped_tenant_transaction(
    session: AsyncSession,
    company_id: UUID
) -> AsyncGenerator[AsyncSession, None]:
    await set_current_tenant(session, company_id)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
