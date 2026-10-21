from fastapi import APIRouter

from salesia.modules.operaciones.application.auxiliares.aware import aware as aware
from salesia.modules.operaciones.application.auxiliares.job_response import job_response as job_response
from salesia.modules.operaciones.application.auxiliares.now import now as now
from salesia.modules.operaciones.application.auxiliares.private_root import private_root as private_root
from salesia.modules.operaciones.application.auxiliares.purchase_attachment_access import (
    purchase_attachment_access as purchase_attachment_access,
)
from salesia.modules.operaciones.application.auxiliares.related_exists import related_exists as related_exists
from salesia.modules.operaciones.application.auxiliares.replace_setting import replace_setting as replace_setting
from salesia.modules.operaciones.application.auxiliares.safe_path import safe_path as safe_path
from salesia.modules.operaciones.application.auxiliares.sanitize_html import sanitize_html as sanitize_html
from salesia.modules.operaciones.application.auxiliares.scan_uploaded_file import (
    scan_uploaded_file as scan_uploaded_file,
)
from salesia.modules.operaciones.application.auxiliares.setting_value import setting_value as setting_value
from salesia.modules.operaciones.application.contracts.adjuntos import (
    CompleteAttachmentRequest as CompleteAttachmentRequest,
)
from salesia.modules.operaciones.application.contracts.adjuntos import UploadIntentRequest as UploadIntentRequest
from salesia.modules.operaciones.application.contracts.colaboracion_aprobaciones import (
    ApprovalCreateRequest as ApprovalCreateRequest,
)
from salesia.modules.operaciones.application.contracts.colaboracion_aprobaciones import (
    ApprovalDecideRequest as ApprovalDecideRequest,
)
from salesia.modules.operaciones.application.contracts.colaboracion_comentarios import (
    CommentCreateRequest as CommentCreateRequest,
)
from salesia.modules.operaciones.application.contracts.colaboracion_comentarios import (
    CommentUpdateRequest as CommentUpdateRequest,
)
from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskCreateRequest as TaskCreateRequest
from salesia.modules.operaciones.application.contracts.colaboracion_tareas import TaskUpdateRequest as TaskUpdateRequest
from salesia.modules.operaciones.application.contracts.colaboracion_vistas_guardadas import (
    SavedViewCreateRequest as SavedViewCreateRequest,
)
from salesia.modules.operaciones.application.contracts.colaboracion_vistas_guardadas import (
    SavedViewUpdateRequest as SavedViewUpdateRequest,
)
from salesia.modules.operaciones.application.contracts.importaciones import (
    ImportJobCreateRequest as ImportJobCreateRequest,
)
from salesia.modules.operaciones.application.contracts.integraciones import (
    IntegrationCreateRequest as IntegrationCreateRequest,
)
from salesia.modules.operaciones.application.contracts.integraciones import (
    IntegrationCredentialRequest as IntegrationCredentialRequest,
)
from salesia.modules.operaciones.application.contracts.integraciones import (
    IntegrationModeRequest as IntegrationModeRequest,
)
from salesia.modules.operaciones.application.contracts.notificaciones import (
    NotificationPreferenceRequest as NotificationPreferenceRequest,
)
from salesia.modules.operaciones.application.contracts.notificaciones import (
    NotificationReadRequest as NotificationReadRequest,
)
from salesia.modules.operaciones.application.contracts.operacion_configuracion import SettingRequest as SettingRequest
from salesia.modules.operaciones.application.contracts.operacion_funcionalidades import (
    FeatureToggleRequest as FeatureToggleRequest,
)
from salesia.modules.operaciones.application.contracts.operacion_mantenimiento import (
    OperationalModeRequest as OperationalModeRequest,
)
from salesia.modules.operaciones.application.contracts.operacion_restauracion import (
    RestoreVerifyRequest as RestoreVerifyRequest,
)
from salesia.modules.operaciones.presentation.routes import (
    adjuntos,
    ayuda,
    busqueda,
    colaboracion_aprobaciones,
    colaboracion_comentarios,
    colaboracion_miembros,
    colaboracion_tareas,
    colaboracion_vistas_guardadas,
    eventos,
    importaciones,
    integraciones,
    notificaciones,
    operacion_configuracion,
    operacion_degraded_mode,
    operacion_estado_sistema,
    operacion_funcionalidades,
    operacion_integridad,
    operacion_mantenimiento,
    operacion_metricas,
    operacion_respaldos,
    operacion_restauracion,
    operacion_trabajos,
    trabajos,
)

router = APIRouter(tags=["Operaciones, Trabajos y Auditoría"])
router.include_router(adjuntos.router)
router.include_router(importaciones.router)
router.include_router(trabajos.router)
router.include_router(operacion_trabajos.router)
router.include_router(notificaciones.router)
router.include_router(integraciones.router)
router.include_router(eventos.router)
router.include_router(busqueda.router)
router.include_router(colaboracion_comentarios.router)
router.include_router(colaboracion_miembros.router)
router.include_router(colaboracion_tareas.router)
router.include_router(colaboracion_aprobaciones.router)
router.include_router(colaboracion_vistas_guardadas.router)
router.include_router(ayuda.router)
router.include_router(operacion_configuracion.router)
router.include_router(operacion_funcionalidades.router)
router.include_router(operacion_mantenimiento.router)
router.include_router(operacion_degraded_mode.router)
router.include_router(operacion_estado_sistema.router)
router.include_router(operacion_metricas.router)
router.include_router(operacion_integridad.router)
router.include_router(operacion_respaldos.router)
router.include_router(operacion_restauracion.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "create_upload_intent",
            "upload_attachment_content",
            "complete_attachment_upload",
            "download_attachment",
            "preview_attachment",
            "inspect_import",
            "create_import_job",
            "list_import_jobs",
            "commit_import_job",
            "get_job_status",
            "list_operational_jobs",
            "retry_operational_job",
            "cancel_job",
            "list_notifications",
            "mark_all_notifications_read",
            "mark_notification_read",
            "list_integrations",
            "create_integration",
            "rotate_integration_credential",
            "update_integration_mode",
            "diagnose_integration",
            "get_notification_resource",
            "get_notification_preferences",
            "update_notification_preference",
            "stream_events",
            "unified_search",
            "create_comment",
            "list_comments",
            "update_comment",
            "collaboration_members",
            "create_task",
            "list_tasks",
            "update_task",
            "delete_task",
            "create_approval",
            "list_approvals",
            "decide_approval",
            "create_saved_view",
            "list_saved_views",
            "update_saved_view",
            "delete_saved_view",
            "get_contextual_help",
            "get_operation_settings",
            "set_operation_setting",
            "get_feature_flags",
            "toggle_feature_flag",
            "set_maintenance",
            "set_degraded_mode",
            "get_system_operational_status",
            "get_operational_metrics",
            "check_business_invariants",
            "trigger_backup",
            "get_backup_status",
            "verify_restore_readiness",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
from salesia.modules.operaciones.presentation.routes.expedientes import router as dossier_router

router.include_router(dossier_router)
from salesia.modules.operaciones.presentation.routes.politicas_aprobacion import router as approval_policies_router

router.include_router(approval_policies_router)
from salesia.modules.operaciones.presentation.routes.planificacion import router as task_planning_router

router.include_router(task_planning_router)
create_upload_intent = adjuntos.create_upload_intent
upload_attachment_content = adjuntos.upload_attachment_content
complete_attachment_upload = adjuntos.complete_attachment_upload
download_attachment = adjuntos.download_attachment
preview_attachment = adjuntos.preview_attachment
inspect_import = importaciones.inspect_import
create_import_job = importaciones.create_import_job
list_import_jobs = importaciones.list_import_jobs
commit_import_job = importaciones.commit_import_job
get_job_status = trabajos.get_job_status
list_operational_jobs = operacion_trabajos.list_operational_jobs
retry_operational_job = operacion_trabajos.retry_operational_job
cancel_job = trabajos.cancel_job
list_notifications = notificaciones.list_notifications
mark_all_notifications_read = notificaciones.mark_all_notifications_read
mark_notification_read = notificaciones.mark_notification_read
list_integrations = integraciones.list_integrations
create_integration = integraciones.create_integration
rotate_integration_credential = integraciones.rotate_integration_credential
update_integration_mode = integraciones.update_integration_mode
diagnose_integration = integraciones.diagnose_integration
get_notification_resource = notificaciones.get_notification_resource
get_notification_preferences = notificaciones.get_notification_preferences
update_notification_preference = notificaciones.update_notification_preference
stream_events = eventos.stream_events
unified_search = busqueda.unified_search
create_comment = colaboracion_comentarios.create_comment
list_comments = colaboracion_comentarios.list_comments
update_comment = colaboracion_comentarios.update_comment
collaboration_members = colaboracion_miembros.collaboration_members
create_task = colaboracion_tareas.create_task
list_tasks = colaboracion_tareas.list_tasks
update_task = colaboracion_tareas.update_task
delete_task = colaboracion_tareas.delete_task
create_approval = colaboracion_aprobaciones.create_approval
list_approvals = colaboracion_aprobaciones.list_approvals
decide_approval = colaboracion_aprobaciones.decide_approval
create_saved_view = colaboracion_vistas_guardadas.create_saved_view
list_saved_views = colaboracion_vistas_guardadas.list_saved_views
update_saved_view = colaboracion_vistas_guardadas.update_saved_view
delete_saved_view = colaboracion_vistas_guardadas.delete_saved_view
get_contextual_help = ayuda.get_contextual_help
get_operation_settings = operacion_configuracion.get_operation_settings
set_operation_setting = operacion_configuracion.set_operation_setting
get_feature_flags = operacion_funcionalidades.get_feature_flags
toggle_feature_flag = operacion_funcionalidades.toggle_feature_flag
set_maintenance = operacion_mantenimiento.set_maintenance
set_degraded_mode = operacion_degraded_mode.set_degraded_mode
get_system_operational_status = operacion_estado_sistema.get_system_operational_status
get_operational_metrics = operacion_metricas.get_operational_metrics
check_business_invariants = operacion_integridad.check_business_invariants
trigger_backup = operacion_respaldos.trigger_backup
get_backup_status = operacion_respaldos.get_backup_status
verify_restore_readiness = operacion_restauracion.verify_restore_readiness
