import * as transporte from "../api/ImportsWorkspaceTab";
import { useEffect, useMemo, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";
import { apiClient } from "../../../api/client";
import { clearDraft, readDraft, useUnsavedChanges, writeDraft } from "../../../ui/drafts";
import { RowErrorItem } from "../types/ImportsWorkspaceTab";
import { ImportJobResponse } from "../types/ImportsWorkspaceTab";
import { ImportHistoryItem } from "../types/ImportsWorkspaceTab";
import { Inspection } from "../types/ImportsWorkspaceTab";
import { ImportsWorkspaceTabProps } from "../types/ImportsWorkspaceTab";
import { templates } from "../support/ImportsWorkspaceTab";

export function useImportsWorkspaceTab({ canWrite = true, permissions }: ImportsWorkspaceTabProps) {
  const savedDraft = useMemo(() => readDraft("salesia_import_draft_v2", { currentStep: 1, targetEntity: "products" as "customers" | "products" | "inventory_adjustments", job: null as ImportJobResponse | null, progressPct: 0 }), []);

  const [currentStep, setCurrentStep] = useState(savedDraft.currentStep);

  const [targetEntity, setTargetEntity] = useState<"customers" | "products" | "inventory_adjustments">(savedDraft.targetEntity);

  const [file, setFile] = useState<File | null>(null);

  const [staging, setStaging] = useState(false);

  const [executing, setExecuting] = useState(false);

  const [progressPct, setProgressPct] = useState(savedDraft.progressPct);

  const [job, setJob] = useState<ImportJobResponse | null>(savedDraft.job);

  const [attachmentId, setAttachmentId] = useState(savedDraft.job?.result?.attachment_id || "");

  const [inspection, setInspection] = useState<Inspection | null>(null);

  const [mapping, setMapping] = useState<Record<string, string>>({});

  const [corrections, setCorrections] = useState<Record<string, Record<string, string>>>({});

  const [history, setHistory] = useState<ImportHistoryItem[]>([]);

  const [mappingName, setMappingName] = useState("");

  const [savedMappings, setSavedMappings] = useState<Record<string, Record<string, string>>>(() => readDraft("salesia_import_mappings", {}));

  const toast = useToast();

  const targetPermissions = {
    customers: !permissions || permissions.includes("customers:write"),
    products: !permissions || permissions.includes("products:write"),
    inventory_adjustments: !permissions || permissions.includes("inventory:write")
  };

  const effectiveCanWrite = canWrite && Object.values(targetPermissions).some(Boolean);

  useUnsavedChanges(Boolean(file || job) && job?.status !== "completed");

  useEffect(() => { writeDraft("salesia_import_draft_v2", { currentStep, targetEntity, job, progressPct }); }, [currentStep, targetEntity, job, progressPct]);

  useEffect(() => { transporte.solicitarDatos().then(result => setHistory(result.items || [])).catch(() => undefined); }, [job?.status]);

  useEffect(() => {
    if (targetPermissions[targetEntity]) return;
    const firstAllowed = (Object.keys(targetPermissions) as Array<keyof typeof targetPermissions>).find((key) => targetPermissions[key]);
    if (firstAllowed) setTargetEntity(firstAllowed);
  }, [permissions, targetEntity]);

  const detectedColumns = useMemo(() => {
    const preview = job?.result?.preview?.[0];
    return preview ? Object.keys(preview) : [];
  }, [job]);

  const rowErrors: RowErrorItem[] = (job?.result?.row_errors || []).map((error) => ({
    row_number: error.row,
    field: error.column,
    rejected_value: "",
    reason: error.error
  }));

  const handleDownloadTemplate = () => {
    const blob = new Blob([templates[targetEntity]], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `plantilla_importacion_${targetEntity}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Plantilla descargada", "La plantilla contiene las columnas exactas requeridas por el importador.");
  };

  const inspectFile = async () => {
    if (!file) {
      toast.warning("Selecciona un archivo", "Debes elegir un archivo CSV antes de validar.");
      return;
    }
    setStaging(true);
    setJob(null);
    try {
      const intent = await transporte.solicitarInspectFile({ file });
      await apiClient.request(intent.upload_url, { method: "PUT", headers: { "Content-Type": "text/csv", "X-Upload-Token": intent.upload_token }, body: await file.arrayBuffer() });
      await transporte.solicitarInspectFile2({ intent });
      setAttachmentId(intent.attachment_id);
      const inspected = await transporte.solicitarInspectFile3({ targetEntity, intent });
      setInspection(inspected);
      setMapping(Object.fromEntries(templates[targetEntity].split("\r\n")[0].split(",").filter(column => inspected.columns.includes(column)).map(column => [column, column])));
      setCurrentStep(3);
    } catch (failure: unknown) {
      toast.error("No se pudo leer el archivo", String((failure as { detail?: string }).detail || "Revisa que el contenido sea un archivo CSV válido."));
    } finally { setStaging(false); }
  };

  const stageImport = async (correcting = false) => {
    const attachment = correcting ? job?.result?.attachment_id : attachmentId;
    if (!attachment) return;
    setStaging(true);
    try {
      const staged = await transporte.solicitarStageImport({ targetEntity, attachment, correcting, job, mapping, inspection, corrections });
      setJob(staged);
      setProgressPct(0);
      setCurrentStep(4);
      toast.info("Validación terminada", `${staged.result?.valid_rows || 0} filas válidas y ${staged.result?.invalid_rows || 0} filas observadas.`);
    } catch (failure: unknown) {
      toast.error("No se pudo validar la importación", String((failure as { detail?: string }).detail || failure));
    } finally {
      setStaging(false);
    }
  };

  const waitForCompletion = async (jobId: string) => {
    for (let attempt = 0;attempt < 120;attempt += 1) {
      const current = await transporte.solicitarWaitForCompletion({ jobId });
      setJob(current);
      setProgressPct(current.progress_pct || 0);
      if (current.status === "completed") return current;
      if (current.status === "failed" || current.status === "cancelled") throw new Error(`La importación terminó con estado ${current.status}.`);
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
    throw new Error("La importación continúa en proceso. Consulta nuevamente el estado del trabajo.");
  };

  const executeImport = async () => {
    if (!job) return;
    if (job.result?.is_duplicate_file) {
      toast.warning("Archivo ya procesado", "Este mismo contenido ya aparece en una importación completada.");
      return;
    }
    setExecuting(true);
    try {
      await transporte.solicitarExecuteImport({ job });
      const completed = await waitForCompletion(job.job_id);
      toast.success("Importación completada", `${completed.result?.processed_rows ?? completed.result?.imported ?? completed.result?.valid_rows ?? 0} registros fueron procesados por el worker.`);
    } catch (failure: unknown) {
      toast.error("La importación no se completó", String((failure as { detail?: string }).detail || (failure as Error).message || failure));
    } finally {
      setExecuting(false);
    }
  };

  const reset = () => {
    setCurrentStep(1);
    setFile(null);
    setJob(null);
    setProgressPct(0);
    setAttachmentId("");
    setInspection(null);
    setMapping({});
    setCorrections({});
    clearDraft("salesia_import_draft_v2");
  };
  return { currentStep, setCurrentStep, targetEntity, setTargetEntity, file, setFile, staging, executing, progressPct, setProgressPct, job, setJob, setAttachmentId, inspection, setInspection, mapping, setMapping, corrections, setCorrections, history, mappingName, setMappingName, savedMappings, setSavedMappings, toast, targetPermissions, effectiveCanWrite, detectedColumns, rowErrors, handleDownloadTemplate, inspectFile, stageImport, executeImport, reset };
}
