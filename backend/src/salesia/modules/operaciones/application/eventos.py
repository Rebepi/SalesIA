import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from salesia.modules.operaciones.infrastructure_models import Notification
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.database import sync_session_factory
from salesia.shared.infrastructure.models import UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company


async def stream_events(cursor: Optional[str], limit: Optional[int], request: Request, current_user: AuthenticatedUser):
    last_event_id = request.headers.get("Last-Event-ID") if request else None

    effective_cursor = cursor or last_event_id

    async def events():

        seen = set()

        user_company = current_user.company_id

        iterations = 0

        while True:
            if request and await request.is_disconnected():
                break

            rows = await run_in_threadpool(notification_batch, current_user.user_id, user_company, effective_cursor)
            if rows is None:
                break
            for row in rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                data = json.dumps(row)
                yield f"id: {row['id']}\nevent: notification\ndata: {data}\n\n"

            yield ": heartbeat\n\n"

            iterations += 1

            if limit and iterations >= limit:
                break

            try:
                await asyncio.sleep(15)

            except asyncio.CancelledError:
                break

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


def notification_batch(user_id, company_id, cursor):
    with sync_session_factory() as session:
        bind_company(session, company_id)
        active_user = session.scalar(select(UserModel.id).where(UserModel.id == user_id, UserModel.company_id == company_id, UserModel.is_active.is_(True)))
        if active_user is None:
            return None
        query = select(Notification).where(Notification.company_id == company_id, Notification.user_id == user_id)
        if cursor:
            try:
                query = query.where(Notification.created_at >= datetime.fromisoformat(cursor))
            except ValueError:
                pass
        rows = session.scalars(query.order_by(Notification.created_at, Notification.id).limit(100)).all()
        return [{"id": str(row.id), "title": row.title, "message": row.message, "event_type": row.event_type, "priority": row.priority, "category": row.category, "created_at": row.created_at.isoformat()} for row in rows]
