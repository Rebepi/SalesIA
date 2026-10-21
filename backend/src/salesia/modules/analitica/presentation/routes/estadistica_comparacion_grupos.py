from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_comparacion_grupos as service_estadistica_comparacion_grupos
from salesia.modules.analitica.application.contracts.estadistica_comparacion_grupos import GroupsTestRequest

router = APIRouter(prefix="")


@router.post("/statistics/groups-test")
def post_groups_test(payload: GroupsTestRequest):

    return service_estadistica_comparacion_grupos.post_groups_test(payload=payload)
