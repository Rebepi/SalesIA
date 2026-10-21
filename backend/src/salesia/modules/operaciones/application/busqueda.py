from typing import Optional
import re

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.recursos import RESOURCES, entity, search_statement, summary
from salesia.modules.operaciones.infrastructure_models import CollaborationComment
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def unified_search(q: str, limit: int, offset: int, types: Optional[str], current_user: AuthenticatedUser, db: Session):
    selected = {value.strip() for value in types.split(",")} if types else set(RESOURCES)
    if "document" in selected:
        selected.remove("document")
        selected.add("sale")
    unknown = selected - set(RESOURCES) - {"comment"}
    if unknown:
        raise HTTPException(422, "Tipo de búsqueda desconocido: " + ", ".join(sorted(unknown)))
    results, total = [], 0
    term = re.sub(r"\b([A-Za-z][A-Za-z0-9]*)-0*(\d+)\b", lambda match: match.group(1) + "-" + str(int(match.group(2))), q)
    for kind in sorted(selected & set(RESOURCES)):
        resource = RESOURCES[kind]
        if resource[2] and resource[2] not in current_user.permissions:
            continue
        statement = search_statement(kind, current_user, term)
        total += db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        for row in db.scalars(statement.order_by(resource[0].id).limit(offset + limit)).all():
            item = summary(kind, row)
            item["subtitle"] = " · ".join(str(value) for value in (resource[1], item["currency"], item["amount"], item["status"]) if value is not None)
            results.append(item)
    if "comment" in selected:
        comments = db.scalars(select(CollaborationComment).where(CollaborationComment.company_id == current_user.company_id, CollaborationComment.sanitized_content.ilike("%" + q + "%"))).all()
        for comment in comments:
            if comment.resource_type not in RESOURCES:
                continue
            try:
                entity(db, current_user, comment.resource_type, comment.resource_id)
            except HTTPException:
                continue
            total += 1
            results.append({"type": comment.resource_type, "id": str(comment.resource_id), "title": f"Comentario: {comment.sanitized_content[:100]}", "subtitle": RESOURCES[comment.resource_type][1]})
    results.sort(key=lambda item: (item["type"], item["id"]))
    return {"query": q, "total": total, "count": len(results[offset:offset + limit]), "results": results[offset:offset + limit]}
