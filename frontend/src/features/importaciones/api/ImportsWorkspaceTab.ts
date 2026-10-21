import { apiClient } from "../../../api/client";
import { ImportJobResponse } from "../types/ImportsWorkspaceTab";
import { ImportHistoryItem } from "../types/ImportsWorkspaceTab";
import { Inspection } from "../types/ImportsWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ items: ImportHistoryItem[] }>("/api/v1/imports");
}

export function solicitarInspectFile({ file }: { file: File }) {
  return apiClient.request<{ attachment_id: string; upload_url: string; upload_token: string }>("/api/v1/attachments/upload-intents", {
    method: "POST",
    body: JSON.stringify({ file_name: file.name, mime_type: "text/csv", file_size_bytes: file.size, related_entity_type: "import", related_entity_id: null })
  });
}

export function solicitarInspectFile2({ intent }: { intent: { attachment_id: string; upload_url: string; upload_token: string; } }) {
  return apiClient.request(`/api/v1/attachments/${intent.attachment_id}/complete`, { method: "POST", body: JSON.stringify({}) });
}

export function solicitarInspectFile3({ targetEntity, intent }: { targetEntity: "customers" | "products" | "inventory_adjustments"; intent: { attachment_id: string; upload_url: string; upload_token: string; } }) {
  return apiClient.request<Inspection>("/api/v1/imports/inspect", { method: "POST", body: JSON.stringify({ target_entity: targetEntity, attachment_id: intent.attachment_id }) });
}

export function solicitarStageImport({ targetEntity, attachment, correcting, job, mapping, inspection, corrections }: { targetEntity: "customers" | "products" | "inventory_adjustments"; attachment: string; correcting: boolean; job: ImportJobResponse | null; mapping: Record<string, string>; inspection: Inspection | null; corrections: Record<string, Record<string, string>> }) {
  return apiClient.request<ImportJobResponse>("/api/v1/imports", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ target_entity: targetEntity, attachment_id: attachment, column_mapping: correcting ? job?.result?.column_mapping || {} : mapping, delimiter: correcting ? job?.result?.detected?.delimiter : inspection?.delimiter, encoding: correcting ? job?.result?.detected?.encoding : inspection?.encoding, corrections: correcting ? { ...job?.result?.corrections, ...corrections } : {}, source_import_id: correcting ? job?.job_id : undefined }) });
}

export function solicitarWaitForCompletion({ jobId }: { jobId: string }) {
  return apiClient.request<ImportJobResponse>(`/api/v1/jobs/${jobId}`);
}

export function solicitarExecuteImport({ job }: { job: ImportJobResponse }) {
  return apiClient.request(`/api/v1/imports/${job.job_id}/commit`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
}
