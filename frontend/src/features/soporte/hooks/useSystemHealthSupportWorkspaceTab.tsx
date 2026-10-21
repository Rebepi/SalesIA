import * as transporte from "../api/SystemHealthSupportWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { SystemServiceStatus } from "../types/SystemHealthSupportWorkspaceTab";
import { FailedJobItem } from "../types/SystemHealthSupportWorkspaceTab";
import { SystemHealthSupportWorkspaceTabProps } from "../types/SystemHealthSupportWorkspaceTab";

export function useSystemHealthSupportWorkspaceTab({ isTechAdmin = false }: SystemHealthSupportWorkspaceTabProps) {
  const [services, setServices] = useState<SystemServiceStatus[]>([]);

  const [failedJobs, setFailedJobs] = useState<FailedJobItem[]>([]);

  const [loading, setLoading] = useState(true);

  const [loadError, setLoadError] = useState<string | null>(null);

  const toast = useToast();

  useEffect(() => {
    let active = true;
    setLoading(true);
    const load = async () => {
      const started = performance.now();
      try {
        const live = await transporte.solicitarLoad();
        const apiLatency = Math.max(1, Math.round(performance.now() - started));
        const readyStarted = performance.now();
        const ready = await transporte.solicitarLoad2();
        const databaseLatency = Math.max(1, Math.round(performance.now() - readyStarted));
        let status: { status: string; pending_jobs: number; failed_jobs: number; outbox_backlog: number } | null = null;
        let availabilityTarget = "No disponible";
        let jobs: Array<{ job_id: string; job_type: string; result: unknown; attempts: number; created_at: string; status: string }> = [];
        if (isTechAdmin) {
          const [statusResponse, metricsResponse, jobsResponse] = await Promise.all([
            transporte.solicitarLoad3(),
            transporte.solicitarLoad4(),
            requestAllPages<{ items: Array<{ job_id: string; job_type: string; result: unknown; attempts: number; created_at: string; status: string }> }>("/api/v1/operations/jobs?status=failed&limit=100")
          ]);
          status = statusResponse;
          availabilityTarget = `${Number(metricsResponse.slo_targets.availability_target) * 100}%`;
          jobs = jobsResponse.items || [];
        }
        if (!active) return;
        const visibleServices: SystemServiceStatus[] = [
          { name: "API Backend FastAPI", status: live.status === "ok" ? "healthy" : "down", latency_ms: apiLatency, version: live.version, uptime_pct: availabilityTarget, details: `Entorno ${live.environment}. Respuesta de vitalidad confirmada.` },
          { name: "Base de Datos PostgreSQL", status: ready.database === "connected" ? "healthy" : "down", latency_ms: databaseLatency, version: ready.database, uptime_pct: availabilityTarget, details: `Estado de preparación: ${ready.status}.` }
        ];
        if (status) visibleServices.push({ name: "Colas y outbox", status: status.status === "degraded" ? "degraded" : status.status === "maintenance" ? "down" : "healthy", latency_ms: 0, version: "Estado operativo", uptime_pct: availabilityTarget, details: `${status.pending_jobs} trabajos pendientes, ${status.failed_jobs} fallidos y ${status.outbox_backlog} eventos en outbox.` });
        setServices(visibleServices);
        setFailedJobs(jobs.map((job) => ({ id: job.job_id, task_name: job.job_type, trace_id: job.job_id, error_message: typeof job.result === "string" ? job.result : JSON.stringify(job.result || "Sin detalle de error"), retry_count: job.attempts, created_at: job.created_at, status: "failed" })));
        setLoadError(null);
      } catch (failure: unknown) {
        if (active) setLoadError(String((failure as { detail?: string }).detail || failure));
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; };
  }, [isTechAdmin]);

  const handleRetryJob = async (jobId: string) => {
    try {
      await transporte.solicitarHandleRetryJob({ jobId });
      setFailedJobs((prev) => prev.map((job) => job.id === jobId ? { ...job, status: "retrying" } : job));
      toast.success("Tarea encolada para reintento", `La tarea ${jobId} volvió a la cola operativa.`);
    } catch (failure: unknown) {
      toast.error("No se pudo reintentar la tarea", String((failure as { detail?: string }).detail || failure));
    }
  };

  const handleDownloadDiagnostic = () => {
    const report = {
      services: services.map((s) => ({
        name: s.name,
        status: s.status,
        latency_ms: s.latency_ms,
        version: s.version
      })),
      scope: isTechAdmin ? "operational" : "public",
      failed_jobs: isTechAdmin ? failedJobs.map((job) => ({ id: job.id, task_name: job.task_name, trace_id: job.trace_id, retry_count: job.retry_count, created_at: job.created_at, status: job.status })) : [],
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diagnostico-soporte-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Informe descargado", "Diagnóstico del sistema generado.");
  };
  return { services, failedJobs, loading, loadError, handleRetryJob, handleDownloadDiagnostic };
}
