from salesia.modules.analitica.application.contracts.analitica_series_temporales import TimeSeriesSplitRequest
from salesia.modules.analitica.domain.advanced import analyze_time_series_split


def post_time_series(payload: TimeSeriesSplitRequest):
    return analyze_time_series_split(
        records=payload.records,
        date_column=payload.date_column,
        value_column=payload.value_column,
        train_ratio=payload.train_ratio,
    )
