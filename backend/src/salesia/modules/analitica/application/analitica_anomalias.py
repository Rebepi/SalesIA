from salesia.modules.analitica.application.contracts.analitica_anomalias import AnomalyDetectionRequest
from salesia.modules.analitica.domain.advanced import detect_anomalies_detailed


def post_anomaly_detection(payload: AnomalyDetectionRequest):
    return detect_anomalies_detailed(
        records=payload.records,
        feature_columns=payload.feature_columns,
        method=payload.method,
        expected_alert_rate=payload.expected_alert_rate,
    )
