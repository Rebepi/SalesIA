import { apiClient } from "../../../api/client";
import { DatasetVersionItem } from "../types/DataQualityPanel";
import { DatasetVersionDetail } from "../types/DataQualityPanel";
import { DatasetItem } from "../types/DataQualityPanel";

export function solicitarDatos() {
  return apiClient.request<{ items: DatasetItem[] }>("/api/v1/datasets");
}

export function solicitarDatos2({ activeDatasetId }: { activeDatasetId: string }) {
  return apiClient.request<{ items: Array<DatasetVersionItem & { data_hash?: string }> }>(`/api/v1/datasets/${activeDatasetId}/versions`);
}

export function solicitarDatos3({ activeDatasetId, selectedVersion }: { activeDatasetId: string; selectedVersion: number }) {
  return apiClient.request<DatasetVersionDetail>(`/api/v1/datasets/${activeDatasetId}/versions/${selectedVersion}`);
}

export function solicitarHandleCreateOperationalDataset() {
  return apiClient.request<{ id: string; name: string; active_version: number }>("/api/v1/datasets", {
    method: "POST",
    body: JSON.stringify({
      name: "Ventas Operacionales Base",
      grain: "ticket",
      source_entity: "sales",
      description: "Dataset generado automaticamente a partir de ventas operacionales de la empresa",
      variables: [
        { name: "id", nature: "identifier", scale: "nominal", is_nullable: false },
        { name: "total_amount", nature: "metric", scale: "ratio", unit: "currency", is_nullable: false },
        { name: "status", nature: "dimension", scale: "nominal", is_nullable: false },
        { name: "customer_id", nature: "dimension", scale: "nominal", is_nullable: true },
        { name: "issued_at", nature: "timestamp", scale: "interval", is_nullable: false }
      ]
    })
  });
}

export function solicitarHandleCreateOperationalDataset2({ created }: { created: { id: string; name: string; active_version: number; } }) {
  return apiClient.request<DatasetVersionDetail>(`/api/v1/datasets/${created.id}/versions`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function solicitarHandleCreateOperationalDataset3() {
  return apiClient.request<{ items: DatasetItem[] }>("/api/v1/datasets");
}

export function solicitarHandleGenerateNewVersionAfterCorrection({ activeDatasetId }: { activeDatasetId: string }) {
  return apiClient.request<DatasetVersionDetail>(`/api/v1/datasets/${activeDatasetId}/versions`, {
    method: "POST",
    body: JSON.stringify({ parameters: { reason: "source_data_corrected" } })
  });
}

export function solicitarHandleGenerateNewVersionAfterCorrection2({ activeDatasetId }: { activeDatasetId: string }) {
  return apiClient.request<{ items: Array<DatasetVersionItem & { data_hash?: string }> }>(`/api/v1/datasets/${activeDatasetId}/versions`);
}

export function solicitarHandleRebuildProjection({ activeDatasetId }: { activeDatasetId: string }) {
  return apiClient.request<{
    message: string;
    rebuilt: boolean;
    dataset_id: string;
    previous_version: number;
    new_version: number;
    metrics_comparison: {
      previous_row_count: number;
      new_row_count: number;
      previous_hash: string;
      new_hash: string;
    };
  }>(`/api/v1/datasets/${activeDatasetId}/rebuild`, {
    method: "POST"
  });
}

export function solicitarHandleRebuildProjection2({ activeDatasetId }: { activeDatasetId: string }) {
  return apiClient.request<{ items: Array<DatasetVersionItem & { data_hash?: string }> }>(`/api/v1/datasets/${activeDatasetId}/versions`);
}
