from fastapi import APIRouter

from salesia.modules.analitica.application.auxiliares.build_csv import _build_csv as _build_csv
from salesia.modules.analitica.application.auxiliares.execute_report_data import (
    _execute_report_data as _execute_report_data,
)
from salesia.modules.analitica.application.auxiliares.report_run_data import report_run_data as report_run_data
from salesia.modules.analitica.application.auxiliares.report_run_row import report_run_row as report_run_row
from salesia.modules.analitica.application.auxiliares.resolve_dataset_values import (
    resolve_dataset_values as resolve_dataset_values,
)
from salesia.modules.analitica.application.auxiliares.sanitize_csv_cell import _sanitize_csv_cell as _sanitize_csv_cell
from salesia.modules.analitica.application.auxiliares.write_report_artifact import (
    write_report_artifact as write_report_artifact,
)
from salesia.modules.analitica.application.contracts.analitica_anomalias import (
    AnomalyDetectionRequest as AnomalyDetectionRequest,
)
from salesia.modules.analitica.application.contracts.analitica_demanda import (
    DemandForecastCensoredRequest as DemandForecastCensoredRequest,
)
from salesia.modules.analitica.application.contracts.analitica_models import ModelMonitorRequest as ModelMonitorRequest
from salesia.modules.analitica.application.contracts.analitica_models import (
    ModelRegisterRequest as ModelRegisterRequest,
)
from salesia.modules.analitica.application.contracts.analitica_series_temporales import (
    TimeSeriesSplitRequest as TimeSeriesSplitRequest,
)
from salesia.modules.analitica.application.contracts.asistente import AiQueryRequest as AiQueryRequest
from salesia.modules.analitica.application.contracts.asistente import AiSimulationRequest as AiSimulationRequest
from salesia.modules.analitica.application.contracts.asistente import EmergencyPauseRequest as EmergencyPauseRequest
from salesia.modules.analitica.application.contracts.comunes import EventDefinitionModel as EventDefinitionModel
from salesia.modules.analitica.application.contracts.comunes import StructuredConditionModel as StructuredConditionModel
from salesia.modules.analitica.application.contracts.comunes import UniverseDefinitionModel as UniverseDefinitionModel
from salesia.modules.analitica.application.contracts.datasets_gestion import (
    DatasetCreateRequest as DatasetCreateRequest,
)
from salesia.modules.analitica.application.contracts.datasets_gestion import (
    DatasetExpireRequest as DatasetExpireRequest,
)
from salesia.modules.analitica.application.contracts.datasets_gestion import SamplingRequest as SamplingRequest
from salesia.modules.analitica.application.contracts.datasets_versiones_construccion import (
    DatasetVersionCreateRequest as DatasetVersionCreateRequest,
)
from salesia.modules.analitica.application.contracts.datasets_versiones_construccion import (
    OperationalDatasetExtractRequest as OperationalDatasetExtractRequest,
)
from salesia.modules.analitica.application.contracts.distribuciones_frecuencias import (
    DistributionRequest as DistributionRequest,
)
from salesia.modules.analitica.application.contracts.distribuciones_frecuencias import (
    FrequenciesRequest as FrequenciesRequest,
)
from salesia.modules.analitica.application.contracts.distribuciones_frecuencias import (
    OutliersAnalysisRequest as OutliersAnalysisRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_avanzada import (
    AdvancedStatisticsRequest as AdvancedStatisticsRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_comparacion_grupos import (
    GroupsTestRequest as GroupsTestRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_comparaciones_multiples import (
    MultipleComparisonsRequest as MultipleComparisonsRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import CompareRequest as CompareRequest
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import (
    DescriptiveSummaryRequest as DescriptiveSummaryRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import MeanRequest as MeanRequest
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import MedianRequest as MedianRequest
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import (
    WeightedMeanRequest as WeightedMeanRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_desviacion import (
    StdevDetailedRequest as StdevDetailedRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_distribucion_teorica import (
    TheoreticalDistributionRequest as TheoreticalDistributionRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_efecto import EffectSizeRequest as EffectSizeRequest
from salesia.modules.analitica.application.contracts.estadistica_esperanza import (
    MathExpectationRequest as MathExpectationRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_estabilidad import (
    NumericalStabilityRequest as NumericalStabilityRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_intervalos import (
    ConfidenceIntervalRequest as ConfidenceIntervalRequest,
)
from salesia.modules.analitica.application.contracts.estadistica_varianza import (
    VarianceDetailedRequest as VarianceDetailedRequest,
)
from salesia.modules.analitica.application.contracts.experimentos import ABExperimentRequest as ABExperimentRequest
from salesia.modules.analitica.application.contracts.historial import AnalysisCreateRequest as AnalysisCreateRequest
from salesia.modules.analitica.application.contracts.historial import AnalysisRepeatRequest as AnalysisRepeatRequest
from salesia.modules.analitica.application.contracts.insights_evaluacion import (
    InsightEvaluationRequest as InsightEvaluationRequest,
)
from salesia.modules.analitica.application.contracts.insights_evaluacion import (
    InsightRuleSimulateRequest as InsightRuleSimulateRequest,
)
from salesia.modules.analitica.application.contracts.insights_gestion import (
    InsightBulkActionRequest as InsightBulkActionRequest,
)
from salesia.modules.analitica.application.contracts.insights_gestion import (
    InsightFeedbackRequest as InsightFeedbackRequest,
)
from salesia.modules.analitica.application.contracts.insights_gestion import (
    InsightStatusUpdateRequest as InsightStatusUpdateRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_bayes import (
    BayesCalculationRequest as BayesCalculationRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_bayes import (
    SmoothedBayesRequest as SmoothedBayesRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    HypothesisTestRequest as HypothesisTestRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    PreregisterHypothesisRequest as PreregisterHypothesisRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    ProbabilityEventsRequest as ProbabilityEventsRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    ScenarioCompareRequest as ScenarioCompareRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    TemporalLeakageValidationRequest as TemporalLeakageValidationRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_historial import (
    DuplicateScenarioRequest as DuplicateScenarioRequest,
)
from salesia.modules.analitica.application.contracts.probabilidad_historial import (
    ProbabilityAnalysisSaveRequest as ProbabilityAnalysisSaveRequest,
)
from salesia.modules.analitica.application.contracts.reportes_catalogo import (
    ReportCompareRequest as ReportCompareRequest,
)
from salesia.modules.analitica.application.contracts.reportes_ejecuciones import ReportRunRequest as ReportRunRequest
from salesia.modules.analitica.application.contracts.reportes_programacion import (
    ReportScheduleCreateRequest as ReportScheduleCreateRequest,
)
from salesia.modules.analitica.application.contracts.variables_aleatorias import (
    VariableAnalyzeRequest as VariableAnalyzeRequest,
)
from salesia.modules.analitica.domain.reports import execute_report_data as execute_report_data
from salesia.modules.analitica.presentation.routes import (
    analitica_anomalias,
    analitica_bayes,
    analitica_clientes,
    analitica_demanda,
    analitica_models,
    analitica_productos,
    analitica_resumen,
    analitica_sedes,
    analitica_sellers,
    analitica_series_temporales,
    analitica_variables,
    analitica_ventas,
    asistente,
    dashboard,
    datasets_gestion,
    datasets_versiones_construccion,
    distribuciones_frecuencias,
    estadistica_avanzada,
    estadistica_comparacion_grupos,
    estadistica_comparaciones_multiples,
    estadistica_descriptiva,
    estadistica_desviacion,
    estadistica_distribucion_teorica,
    estadistica_efecto,
    estadistica_esperanza,
    estadistica_estabilidad,
    estadistica_intervalos,
    estadistica_varianza,
    experimentos,
    historial,
    insights_evaluacion,
    insights_gestion,
    probabilidad_bayes,
    probabilidad_eventos,
    probabilidad_historial,
    reportes_catalogo,
    reportes_ejecuciones,
    reportes_programacion,
    variables_aleatorias,
)

router = APIRouter(tags=["Motor Estadístico y Analítica"])
router.include_router(estadistica_descriptiva.router)
router.include_router(variables_aleatorias.router)
router.include_router(distribuciones_frecuencias.router)
router.include_router(probabilidad_eventos.router)
router.include_router(probabilidad_bayes.router)
router.include_router(probabilidad_historial.router)
router.include_router(analitica_resumen.router)
router.include_router(analitica_bayes.router)
router.include_router(analitica_variables.router)
router.include_router(datasets_gestion.router)
router.include_router(datasets_versiones_construccion.router)
router.include_router(historial.router)
router.include_router(insights_gestion.router)
router.include_router(insights_evaluacion.router)
router.include_router(asistente.router)
router.include_router(reportes_catalogo.router)
router.include_router(reportes_ejecuciones.router)
router.include_router(reportes_programacion.router)
router.include_router(dashboard.router)
router.include_router(analitica_ventas.router)
router.include_router(analitica_productos.router)
router.include_router(analitica_clientes.router)
router.include_router(analitica_sellers.router)
router.include_router(analitica_sedes.router)
router.include_router(estadistica_avanzada.router)
router.include_router(estadistica_varianza.router)
router.include_router(estadistica_desviacion.router)
router.include_router(estadistica_estabilidad.router)
router.include_router(estadistica_esperanza.router)
router.include_router(estadistica_distribucion_teorica.router)
router.include_router(estadistica_intervalos.router)
router.include_router(estadistica_comparacion_grupos.router)
router.include_router(estadistica_efecto.router)
router.include_router(estadistica_comparaciones_multiples.router)
router.include_router(experimentos.router)
router.include_router(analitica_series_temporales.router)
router.include_router(analitica_demanda.router)
router.include_router(analitica_anomalias.router)
router.include_router(analitica_models.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "post_mean",
            "post_median",
            "post_compare",
            "post_analyze_variable",
            "post_descriptive_summary",
            "post_frequencies",
            "post_distribution",
            "post_weighted_mean",
            "post_outliers",
            "post_probability_events",
            "post_probability_bayes",
            "post_validate_temporal",
            "post_probability_analysis_save",
            "list_probability_analyses",
            "get_probability_analysis",
            "duplicate_probability_scenario",
            "compare_probability_scenarios",
            "post_hypothesis_test",
            "get_operational_live_counts",
            "post_analytics_summary_compat",
            "post_analytics_bayes_compat",
            "get_analytics_variables",
            "create_dataset",
            "list_datasets",
            "get_dataset",
            "create_dataset_version",
            "list_dataset_versions",
            "get_dataset_version",
            "delete_dataset_version",
            "expire_dataset_version",
            "rebuild_dataset",
            "create_analysis",
            "list_analyses",
            "get_analysis",
            "repeat_analysis",
            "cancel_analysis",
            "list_insights",
            "list_insight_rules",
            "post_simulate_insight_rule",
            "evaluate_insights",
            "get_insight_detail",
            "get_insight_evidence",
            "update_insight_status",
            "add_insight_feedback",
            "prepare_insight_action",
            "bulk_insight_actions",
            "bulk_read_insights",
            "post_ai_query",
            "post_simulate_action",
            "post_emergency_pause",
            "post_ai_resume",
            "list_reports",
            "get_report_preview",
            "trigger_report_run",
            "list_report_runs",
            "get_report_run_status",
            "cancel_report_run",
            "retry_report_run",
            "download_report_run",
            "compare_reports",
            "create_report_schedule",
            "execute_report_schedule",
            "list_report_schedules",
            "delete_report_schedule",
            "get_report_branding",
            "get_dashboard_summary",
            "get_sales_analytics",
            "get_product_analytics",
            "get_customer_analytics",
            "get_seller_analytics",
            "get_branch_analytics",
            "post_advanced_statistics",
            "post_smoothed_bayes",
            "extract_operational_dataset",
            "post_variance",
            "post_stdev",
            "post_numerical_stability",
            "post_mathematical_expectation",
            "post_theoretical_distribution",
            "post_confidence_interval",
            "post_preregister_hypothesis",
            "post_groups_test",
            "post_effect_size",
            "post_multiple_comparisons",
            "post_dataset_sample",
            "post_ab_test",
            "post_time_series",
            "post_demand_forecast",
            "post_anomaly_detection",
            "post_model_registration",
            "get_models_list",
            "get_model_by_id",
            "post_model_monitoring",
        )
    )
}
router.routes.sort(key=lambda route: _router_order.get(route.name, len(_router_order)))
post_mean = estadistica_descriptiva.post_mean
post_median = estadistica_descriptiva.post_median
post_compare = estadistica_descriptiva.post_compare
post_analyze_variable = variables_aleatorias.post_analyze_variable
post_descriptive_summary = estadistica_descriptiva.post_descriptive_summary
post_frequencies = distribuciones_frecuencias.post_frequencies
post_distribution = distribuciones_frecuencias.post_distribution
post_weighted_mean = estadistica_descriptiva.post_weighted_mean
post_outliers = distribuciones_frecuencias.post_outliers
post_probability_events = probabilidad_eventos.post_probability_events
post_probability_bayes = probabilidad_bayes.post_probability_bayes
post_validate_temporal = probabilidad_eventos.post_validate_temporal
post_probability_analysis_save = probabilidad_historial.post_probability_analysis_save
list_probability_analyses = probabilidad_historial.list_probability_analyses
get_probability_analysis = probabilidad_historial.get_probability_analysis
duplicate_probability_scenario = probabilidad_historial.duplicate_probability_scenario
compare_probability_scenarios = probabilidad_eventos.compare_probability_scenarios
post_hypothesis_test = probabilidad_eventos.post_hypothesis_test
get_operational_live_counts = probabilidad_eventos.get_operational_live_counts
post_analytics_summary_compat = analitica_resumen.post_analytics_summary_compat
post_analytics_bayes_compat = analitica_bayes.post_analytics_bayes_compat
get_analytics_variables = analitica_variables.get_analytics_variables
create_dataset = datasets_gestion.create_dataset
list_datasets = datasets_gestion.list_datasets
get_dataset = datasets_gestion.get_dataset
create_dataset_version = datasets_versiones_construccion.create_dataset_version
list_dataset_versions = datasets_versiones_construccion.list_dataset_versions
get_dataset_version = datasets_versiones_construccion.get_dataset_version
delete_dataset_version = datasets_versiones_construccion.delete_dataset_version
expire_dataset_version = datasets_gestion.expire_dataset_version
rebuild_dataset = datasets_versiones_construccion.rebuild_dataset
create_analysis = historial.create_analysis
list_analyses = historial.list_analyses
get_analysis = historial.get_analysis
repeat_analysis = historial.repeat_analysis
cancel_analysis = historial.cancel_analysis
list_insights = insights_gestion.list_insights
list_insight_rules = insights_evaluacion.list_insight_rules
post_simulate_insight_rule = insights_evaluacion.post_simulate_insight_rule
evaluate_insights = insights_evaluacion.evaluate_insights
get_insight_detail = insights_gestion.get_insight_detail
get_insight_evidence = insights_gestion.get_insight_evidence
update_insight_status = insights_gestion.update_insight_status
add_insight_feedback = insights_gestion.add_insight_feedback
prepare_insight_action = insights_gestion.prepare_insight_action
bulk_insight_actions = insights_gestion.bulk_insight_actions
bulk_read_insights = insights_gestion.bulk_read_insights
post_ai_query = asistente.post_ai_query
post_simulate_action = asistente.post_simulate_action
post_emergency_pause = asistente.post_emergency_pause
post_ai_resume = asistente.post_ai_resume
list_reports = reportes_catalogo.list_reports
get_report_preview = reportes_catalogo.get_report_preview
trigger_report_run = reportes_ejecuciones.trigger_report_run
list_report_runs = reportes_ejecuciones.list_report_runs
get_report_run_status = reportes_ejecuciones.get_report_run_status
cancel_report_run = reportes_ejecuciones.cancel_report_run
retry_report_run = reportes_ejecuciones.retry_report_run
download_report_run = reportes_ejecuciones.download_report_run
compare_reports = reportes_catalogo.compare_reports
create_report_schedule = reportes_programacion.create_report_schedule
execute_report_schedule = reportes_programacion.execute_report_schedule
list_report_schedules = reportes_programacion.list_report_schedules
delete_report_schedule = reportes_programacion.delete_report_schedule
get_report_branding = reportes_catalogo.get_report_branding
get_dashboard_summary = dashboard.get_dashboard_summary
get_sales_analytics = analitica_ventas.get_sales_analytics
get_product_analytics = analitica_productos.get_product_analytics
get_customer_analytics = analitica_clientes.get_customer_analytics
get_seller_analytics = analitica_sellers.get_seller_analytics
get_branch_analytics = analitica_sedes.get_branch_analytics
post_advanced_statistics = estadistica_avanzada.post_advanced_statistics
post_smoothed_bayes = probabilidad_bayes.post_smoothed_bayes
extract_operational_dataset = datasets_versiones_construccion.extract_operational_dataset
post_variance = estadistica_varianza.post_variance
post_stdev = estadistica_desviacion.post_stdev
post_numerical_stability = estadistica_estabilidad.post_numerical_stability
post_mathematical_expectation = estadistica_esperanza.post_mathematical_expectation
post_theoretical_distribution = estadistica_distribucion_teorica.post_theoretical_distribution
post_confidence_interval = estadistica_intervalos.post_confidence_interval
post_preregister_hypothesis = probabilidad_eventos.post_preregister_hypothesis
post_groups_test = estadistica_comparacion_grupos.post_groups_test
post_effect_size = estadistica_efecto.post_effect_size
post_multiple_comparisons = estadistica_comparaciones_multiples.post_multiple_comparisons
post_dataset_sample = datasets_gestion.post_dataset_sample
post_ab_test = experimentos.post_ab_test
post_time_series = analitica_series_temporales.post_time_series
post_demand_forecast = analitica_demanda.post_demand_forecast
post_anomaly_detection = analitica_anomalias.post_anomaly_detection
post_model_registration = analitica_models.post_model_registration
get_models_list = analitica_models.get_models_list
get_model_by_id = analitica_models.get_model_by_id
post_model_monitoring = analitica_models.post_model_monitoring

from salesia.modules.analitica.presentation.routes.perspectivas_operacion import router as operating_perspective_router

router.include_router(operating_perspective_router)
