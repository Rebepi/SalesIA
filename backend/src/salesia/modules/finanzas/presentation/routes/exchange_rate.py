from fastapi import APIRouter

import salesia.modules.finanzas.application.exchange_rate as service_exchange_rate
from salesia.modules.finanzas.application.contracts.exchange_rate import CurrencyConvertRequest

router = APIRouter(prefix="")


@router.post("/finance/exchange-rate/convert")
def convert_currency(payload: CurrencyConvertRequest):

    return service_exchange_rate.convert_currency(payload=payload)
