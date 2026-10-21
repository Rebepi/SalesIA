from fastapi import HTTPException

from salesia.modules.operaciones.application.recursos import RESOURCES, entity


def related_exists(db, user, entity_type, entity_id):
    if entity_type == "import" and entity_id is None:
        return True
    if entity_type not in RESOURCES or entity_id is None:
        return False
    try:
        entity(db, user, entity_type, entity_id, write=entity_type == "purchase_order")
    except HTTPException as failure:
        if failure.status_code in (403, 404, 422):
            return False
        raise
    return True
