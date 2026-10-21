from typing import List

from pydantic import BaseModel

from salesia.modules.catalogo.application.contracts.comunes import ImportItemModel


class ImportBatchRequest(BaseModel):
    items: List[ImportItemModel]
