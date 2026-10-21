from salesia.modules.analitica.application.contracts.analitica_demanda import DemandForecastCensoredRequest
from salesia.modules.analitica.domain.advanced import forecast_demand_censored_detailed


def post_demand_forecast(payload: DemandForecastCensoredRequest):
    return forecast_demand_censored_detailed(payload.records, horizon=payload.horizon)
