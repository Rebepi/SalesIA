import os
from celery import Celery
from salesia.shared.infrastructure.config import settings

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

broker_url = getattr(settings, "celery_broker_url", "redis://localhost:6379/0")
result_backend = getattr(settings, "celery_result_backend", "redis://localhost:6379/1")

celery_app = Celery("salesia_enterprise", broker=broker_url, backend=result_backend)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=512000,
    task_routes={
        "salesia.modules.analitica.tasks.*": {"queue": "cpu_intensive"},
        "salesia.modules.operaciones.tasks.*": {"queue": "io_bound"},
        "salesia.modules.reports.tasks.*": {"queue": "io_bound"},
        "salesia.modules.auditoria.tasks.*": {"queue": "io_bound"}
    }
)
