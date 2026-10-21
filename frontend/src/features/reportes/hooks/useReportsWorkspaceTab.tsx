import * as transporte from "../api/ReportsWorkspaceTab";
import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { ReportScheduleConfig } from "../components/ReportScheduleBuilder";
import { readDraft, writeDraft } from "../../../ui/drafts";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { ReportTemplate } from "../types/ReportsWorkspaceTab";
import { ReportRunItem } from "../types/ReportsWorkspaceTab";
import { ReportScheduleItem } from "../types/ReportsWorkspaceTab";
import { ReportPreviewData } from "../types/ReportsWorkspaceTab";
import { ReportComparisonResult } from "../types/ReportsWorkspaceTab";
import { CorporateBranding } from "../types/ReportsWorkspaceTab";


export function useReportsWorkspaceTab(_props: {
  canExport?: boolean;
}) {
  const toast = useToast();

  const { confirm, ConfirmDialogNode } = useConfirm();

  const [activeTab, setActiveTab] = useState<"catalog" | "runs" | "schedules" | "compare">("catalog");

  const [templates, setTemplates] = useState<ReportTemplate[]>([]);

  const [runs, setRuns] = useState<ReportRunItem[]>([]);

  const [schedules, setSchedules] = useState<ReportScheduleItem[]>([]);

  const [branding, setBranding] = useState<CorporateBranding | null>(null);

  const [loading, setLoading] = useState(false);

  const [catalogSearch, setCatalogSearch] = useState("");

  const [selectedArea, setSelectedArea] = useState<string>("all");

  const [previewTemplate, setPreviewTemplate] = useState<ReportTemplate | null>(null);

  const [previewData, setPreviewData] = useState<ReportPreviewData | null>(null);

  const [loadingPreview, setLoadingPreview] = useState(false);

  const [launchModalTemplate, setLaunchModalTemplate] = useState<ReportTemplate | null>(null);

  const [defaultCurrency, setDefaultCurrency] = useState<string>("USD");

  const [launchFormat, setLaunchFormat] = useState<string>("pdf");

  const [launchCurrency, setLaunchCurrency] = useState<string>("USD");

  const [launchStartDate, setLaunchStartDate] = useState<string>("");

  const [launchEndDate, setLaunchEndDate] = useState<string>("");

  const [launchStatus, setLaunchStatus] = useState<string>("confirmed");

  const [launching, setLaunching] = useState(false);

  const [createScheduleModal, setCreateScheduleModal] = useState(false);

  const [schedTemplateCode, setSchedTemplateCode] = useState<string>("REP_SALES_DETAIL");

  const [schedConfig, setSchedConfig] = useState<ReportScheduleConfig>({ frequency: "weekly", hour: 8, minute: 0, weekday: 1, day: 1, start_date: new Intl.DateTimeFormat("en-CA", { timeZone: "America/Lima" }).format(new Date()) });

  const [schedTimezone, setSchedTimezone] = useState<string>("America/Lima");

  const [schedFormat, setSchedFormat] = useState<string>("xlsx");

  const [schedEmails, setSchedEmails] = useState<string>("");

  const [creatingSchedule, setCreatingSchedule] = useState(false);

  const [compareRunA, setCompareRunA] = useState<string>("");

  const [compareRunB, setCompareRunB] = useState<string>("");

  const [comparisonResult, setComparisonResult] = useState<ReportComparisonResult | null>(null);

  const [comparing, setComparing] = useState(false);

  const [favoriteTemplates, setFavoriteTemplates] = useState<string[]>(() => readDraft("salesia_report_favorites", { codes: [] as string[] }).codes);

  const [onlyFavorites, setOnlyFavorites] = useState(false);

  const runStatuses = useRef<Record<string, string>>({});

  const [printableRun, setPrintableRun] = useState<ReportRunItem | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tplData, runsData, schedData, brandData, companyData] = await Promise.all([
        transporte.solicitarLoadData(),
        transporte.solicitarLoadData2(),
        transporte.solicitarLoadData3(),
        transporte.solicitarLoadData4().catch(() => null),
        transporte.solicitarLoadData5()
      ]);
      setTemplates(tplData.items || []);
      setRuns(runsData.items || []);
      setSchedules(schedData.items || []);
      if (brandData) setBranding(brandData);
      setDefaultCurrency(companyData.base_currency);
      setLaunchCurrency(companyData.base_currency);
    } catch (err: unknown) {
      toast.error("Error al cargar reportes", String((err as { detail?: string }).detail || err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    runStatuses.current = Object.fromEntries(runs.map(run => [run.run_id, run.status]));
    if (!runs.some(run => run.status === "queued" || run.status === "processing")) return;
    let cancelled = false;
    const timer = window.setInterval(async () => {
      try {
        const result = await transporte.solicitarDatos();
        if (cancelled) return;
        for (const run of result.items || []) {
          const previous = runStatuses.current[run.run_id];
          if ((previous === "queued" || previous === "processing") && run.status === "completed") toast.success("Reporte listo", "La generación finalizó. Ya puedes descargar el archivo.");
          if ((previous === "queued" || previous === "processing") && run.status === "failed") toast.error("No se pudo generar el reporte", "Revisa los parámetros y utiliza Reintentar en el historial.");
        }
        setRuns(result.items || []);
      } catch { if (!cancelled) toast.warning("Estado pendiente de actualizar", "La conexión se interrumpió. Se intentará nuevamente."); }
    }, 4000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [runs]);

  const handleOpenPreview = async (template: ReportTemplate) => {
    setPreviewTemplate(template);
    setLoadingPreview(true);
    try {
      const data = await transporte.solicitarHandleOpenPreview({ template });
      setPreviewData(data);
    } catch (err: unknown) {
      toast.error("Error en vista previa", String((err as { detail?: string }).detail || err));
      setPreviewTemplate(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleOpenLaunch = (template: ReportTemplate) => {
    setLaunchModalTemplate(template);
    const saved = readDraft(`salesia_report_parameters_${template.code}`, { format: template.allowed_formats[0] || "pdf", currency: defaultCurrency, status: template.status_filter_support[0] || "confirmed", start: "", end: "" });
    setLaunchFormat(saved.format);
    setLaunchCurrency(saved.currency);
    setLaunchStatus(saved.status);
    setLaunchStartDate(saved.start);
    setLaunchEndDate(saved.end);
  };

  const handleLaunchReport = async () => {
    if (!launchModalTemplate) return;
    if (launchStartDate && launchEndDate && launchEndDate < launchStartDate) { toast.warning("Periodo inválido", "La fecha final debe ser igual o posterior a la inicial."); return; }
    writeDraft(`salesia_report_parameters_${launchModalTemplate.code}`, { format: launchFormat, currency: launchCurrency, status: launchStatus, start: launchStartDate, end: launchEndDate });
    setLaunching(true);
    try {
      const payload: Record<string, unknown> = {
        report_type: launchModalTemplate.code,
        format: launchFormat,
        async_execution: true,
        currency: launchCurrency,
        parameters: {
          start_date: launchStartDate || undefined,
          end_date: launchEndDate || undefined,
          status: launchStatus,
          currency: launchCurrency
        }
      };
      const run = await transporte.solicitarHandleLaunchReport({ payload });
      toast.success("Generación de reporte iniciada", `Job ${run.run_id} creado con estado ${run.status}.`);
      setLaunchModalTemplate(null);
      await loadData();
      setActiveTab("runs");
    } catch (err: unknown) {
      toast.error("No se pudo iniciar reporte", String((err as { detail?: string }).detail || err));
    } finally {
      setLaunching(false);
    }
  };

  const handleDownloadRun = async (run: ReportRunItem) => {
    try {
      const { blob, filename } = await apiClient.downloadBlob(`/api/v1/report-runs/${run.run_id}/download`);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(anchor);
      toast.success("Descarga completada", `Archivo ${filename} descargado exitosamente.`);
    } catch (err: unknown) {
      const status = (err as { status?: number }).status;
      if (status === 410) {
        toast.error("Archivo caducado", "El enlace o reporte ha superado su tiempo de vida de 15 minutos.");
      } else if (status === 403) {
        toast.error("Acceso revocado", "El usuario está suspendido o carece de permisos para descargar el reporte.");
      } else if (status === 409) {
        toast.error("Fallo de integridad", "El sello SHA-256 no coincide con el archivo almacenado.");
      } else {
        toast.error("Error al descargar", String((err as { detail?: string }).detail || err));
      }
    }
  };

  const handleCancelRun = async (runId: string) => {
    try {
      await transporte.solicitarHandleCancelRun({ runId });
      toast.info("Generación cancelada", `El job ${runId} fue cancelado exitosamente.`);
      await loadData();
    } catch (err: unknown) {
      toast.error("No se pudo cancelar el reporte", String((err as { detail?: string }).detail || err));
    }
  };

  const handleRetryRun = async (runId: string) => {
    try {
      const newRun = await transporte.solicitarHandleRetryRun({ runId });
      toast.success("Reintento programado", `Nueva ejecución generada: ${newRun.run_id}`);
      await loadData();
    } catch (err: unknown) {
      toast.error("No se pudo reintentar el reporte", String((err as { detail?: string }).detail || err));
    }
  };

  const handleCreateSchedule = async () => {
    setCreatingSchedule(true);
    try {
      const emailsList = Array.from(new Set(schedEmails.split(/[;,\n]/).map(email => email.trim().toLowerCase()).filter(Boolean)));
      if (emailsList.some(email => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) throw { detail: "Indica correos válidos de miembros de la empresa. Sin destinatarios, el reporte queda para su responsable." };
      if (!schedConfig.start_date || !Number.isFinite(schedConfig.hour) || !Number.isFinite(schedConfig.minute)) throw { detail: "Completa la fecha de inicio y la hora." };
      await transporte.solicitarHandleCreateSchedule({ schedTemplateCode, schedConfig, schedTimezone, schedFormat, emailsList });
      toast.success("Programación creada", "La frecuencia, zona horaria y destinatarios quedaron registrados.");
      setCreateScheduleModal(false);
      await loadData();
    } catch (err: unknown) {
      toast.error("Error al crear programación", String((err as { detail?: string }).detail || err));
    } finally {
      setCreatingSchedule(false);
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!await confirm({ title: "¿Eliminar programación?", text: "La programación dejará de ejecutarse. Los reportes ya generados se conservarán.", danger: true, confirmLabel: "Eliminar" })) return;
    try {
      await transporte.solicitarHandleDeleteSchedule({ scheduleId });
      toast.info("Programación eliminada", `La programación ${scheduleId} fue removida.`);
      await loadData();
    } catch (err: unknown) {
      toast.error("No se pudo eliminar la programación", String((err as { detail?: string }).detail || err));
    }
  };

  const handleExecuteScheduleNow = async (scheduleId: string) => {
    try {
      const run = await transporte.solicitarHandleExecuteScheduleNow({ scheduleId });
      toast.success("Ejecución manual iniciada", `Se inició la ejecución ${run.run_id}`);
      await loadData();
      setActiveTab("runs");
    } catch (err: unknown) {
      toast.error("Error al ejecutar schedule", String((err as { detail?: string }).detail || err));
    }
  };

  const handleCompareRuns = async () => {
    if (!compareRunA || !compareRunB) {
      toast.warning("Selecciona dos ejecuciones", "Debes seleccionar dos ejecuciones para comparar.");
      return;
    }
    setComparing(true);
    try {
      const result = await transporte.solicitarHandleCompareRuns({ compareRunA, compareRunB });
      setComparisonResult(result);
      toast.success("Comparación calculada", "Se calcularon las deltas de filas y cortes.");
    } catch (err: unknown) {
      toast.error("Error en comparación", String((err as { detail?: string }).detail || err));
    } finally {
      setComparing(false);
    }
  };

  const areas = [
    { key: "all", label: "Todas las áreas" },
    { key: "commercial", label: "Ventas" },
    { key: "analytics", label: "Analítica" },
    { key: "crm", label: "Clientes" },
    { key: "logistics", label: "Inventario" },
    { key: "finance", label: "Finanzas" }
  ];

  const filteredTemplates = templates.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
      t.code.toLowerCase().includes(catalogSearch.toLowerCase()) ||
      t.objective.toLowerCase().includes(catalogSearch.toLowerCase());
    const matchesArea = selectedArea === "all" || t.area.toLowerCase() === selectedArea.toLowerCase();
    return matchesSearch && matchesArea;
  });

  const isExpired = (expiresAt: string | null) => {
    if (!expiresAt) return false;
    return new Date(expiresAt).getTime() < Date.now();
  };
  return { ConfirmDialogNode, activeTab, setActiveTab, templates, runs, schedules, branding, loading, catalogSearch, setCatalogSearch, selectedArea, setSelectedArea, previewTemplate, setPreviewTemplate, previewData, loadingPreview, launchModalTemplate, setLaunchModalTemplate, launchFormat, setLaunchFormat, launchCurrency, setLaunchCurrency, launchStartDate, setLaunchStartDate, launchEndDate, setLaunchEndDate, launchStatus, setLaunchStatus, launching, createScheduleModal, setCreateScheduleModal, schedTemplateCode, setSchedTemplateCode, schedConfig, setSchedConfig, schedTimezone, setSchedTimezone, schedFormat, setSchedFormat, schedEmails, setSchedEmails, creatingSchedule, compareRunA, setCompareRunA, compareRunB, setCompareRunB, comparisonResult, comparing, favoriteTemplates, setFavoriteTemplates, onlyFavorites, setOnlyFavorites, printableRun, setPrintableRun, loadData, handleOpenPreview, handleOpenLaunch, handleLaunchReport, handleDownloadRun, handleCancelRun, handleRetryRun, handleCreateSchedule, handleDeleteSchedule, handleExecuteScheduleNow, handleCompareRuns, areas, filteredTemplates, isExpired };
}
