import * as transporte from "../api/DataQualityPanel";
import { useEffect, useState } from "react";

import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { DatasetVersionItem } from "../types/DataQualityPanel";
import { DatasetVersionDetail } from "../types/DataQualityPanel";
import { DatasetItem } from "../types/DataQualityPanel";
import { DataQualityPanelProps } from "../types/DataQualityPanel";

export function useDataQualityPanel({ datasetId: initialDatasetId, onVersionCreated, canCalculate = true }: DataQualityPanelProps) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [datasets, setDatasets] = useState<DatasetItem[]>([]);

  const [activeDatasetId, setActiveDatasetId] = useState<string>(initialDatasetId || "");

  const [versions, setVersions] = useState<DatasetVersionItem[]>([]);

  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const [detail, setDetail] = useState<DatasetVersionDetail | null>(null);

  const [loading, setLoading] = useState(false);

  const [actionLoading, setActionLoading] = useState(false);

  const [statusMessage, setStatusMessage] = useState<string>("");

  const [errorMessage, setErrorMessage] = useState<string>("");

  const [rebuildNote, setRebuildNote] = useState<string>("");

  const [copiedHash, setCopiedHash] = useState(false);

  useEffect(() => {
    let unmounted = false;
    transporte.solicitarDatos()
      .then((response) => {
        if (unmounted) return;
        const items = response.items || [];
        setDatasets(items || []);
        if (!activeDatasetId && items && items.length > 0) {
          setActiveDatasetId(items[0].id);
        }
      })
      .catch((err) => {
        if (unmounted) return;
        const msg = typeof err?.detail === "string" ? err.detail : "No se pudieron listar los datasets.";
        setErrorMessage(msg);
      });
    return () => {
      unmounted = true;
    };
  }, []);

  useEffect(() => {
    if (!activeDatasetId) {
      setVersions([]);
      setDetail(null);
      return;
    }
    let unmounted = false;
    setLoading(true);
    setErrorMessage("");
    transporte.solicitarDatos2({ activeDatasetId })
      .then((response) => {
        if (unmounted) return;
        const verList = (response.items || []).map((item) => ({ ...item, sha256_hash: item.sha256_hash || item.data_hash || "", completeness_pct: item.completeness_pct ?? 0 }));
        setVersions(verList || []);
        if (verList && verList.length > 0) {
          const latest = verList[verList.length - 1].version;
          setSelectedVersion(latest);
        } else {
          setSelectedVersion(null);
          setDetail(null);
        }
      })
      .catch((err) => {
        if (unmounted) return;
        const msg = typeof err?.detail === "string" ? err.detail : "Error al cargar versiones del dataset.";
        setErrorMessage(msg);
      })
      .finally(() => {
        if (!unmounted) setLoading(false);
      });
    return () => {
      unmounted = true;
    };
  }, [activeDatasetId]);

  useEffect(() => {
    if (!activeDatasetId || selectedVersion === null) {
      return;
    }
    let unmounted = false;
    setLoading(true);
    transporte.solicitarDatos3({ activeDatasetId, selectedVersion })
      .then((res) => {
        if (unmounted) return;
        setDetail(res);
      })
      .catch((err) => {
        if (unmounted) return;
        const msg = typeof err?.detail === "string" ? err.detail : "Error al cargar detalle de versión.";
        setErrorMessage(msg);
      })
      .finally(() => {
        if (!unmounted) setLoading(false);
      });
    return () => {
      unmounted = true;
    };
  }, [activeDatasetId, selectedVersion]);

  async function handleCreateOperationalDataset() {
    if (!canCalculate) return;
    setActionLoading(true);
    setStatusMessage("");
    setErrorMessage("");
    try {
      const created = await transporte.solicitarHandleCreateOperationalDataset();
      const firstVersion = await transporte.solicitarHandleCreateOperationalDataset2({ created });
      setStatusMessage(`Dataset creado con su versión inicial v${firstVersion.version}. Registros: ${firstVersion.row_count}.`);
      const updatedList = await transporte.solicitarHandleCreateOperationalDataset3();
      setDatasets(updatedList.items || []);
      setActiveDatasetId(created.id);
      setVersions([{ version: firstVersion.version, created_at: firstVersion.created_at, row_count: firstVersion.row_count, sha256_hash: firstVersion.sha256_hash, completeness_pct: firstVersion.quality_report.completeness_pct, status: firstVersion.status }]);
      setSelectedVersion(firstVersion.version);
      setDetail(firstVersion);
    } catch (err: any) {
      setErrorMessage(typeof err?.detail === "string" ? err.detail : "No se pudo crear el dataset.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleGenerateNewVersionAfterCorrection() {
    if (!activeDatasetId || !canCalculate) return;
    setActionLoading(true);
    setStatusMessage("");
    setErrorMessage("");
    setRebuildNote("");
    try {
      const response = await transporte.solicitarHandleGenerateNewVersionAfterCorrection({ activeDatasetId });
      setStatusMessage(`Nueva versión v${response.version} generada exitosamente. Registros: ${response.row_count}. La versión anterior permanece intacta en el historial.`);
      const verResponse = await transporte.solicitarHandleGenerateNewVersionAfterCorrection2({ activeDatasetId });
      const verList = (verResponse.items || []).map((item) => ({ ...item, sha256_hash: item.sha256_hash || item.data_hash || "", completeness_pct: item.completeness_pct ?? 0 }));
      setVersions(verList);
      setSelectedVersion(response.version);
      setDetail(response);
      if (onVersionCreated) {
        onVersionCreated(response.version);
      }
    } catch (err: any) {
      setErrorMessage(typeof err?.detail === "string" ? err.detail : "Error al generar nueva versión tras corrección.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRebuildProjection() {
    if (!activeDatasetId || !canCalculate) return;
    const confirmed = await confirm({ title: "¿Reconstruir proyección?", text: "Se validarán métricas y se publicará una nueva versión.", confirmLabel: "Reconstruir" });
    if (!confirmed) return;
    setActionLoading(true);
    setStatusMessage("");
    setErrorMessage("");
    try {
      const result = await transporte.solicitarHandleRebuildProjection({ activeDatasetId });
      setRebuildNote(`Reconstrucción exitosa. Proyección v${result.new_version} publicada tras validar métricas (filas previas: ${result.metrics_comparison.previous_row_count}, nuevas: ${result.metrics_comparison.new_row_count}).`);
      const verResponse = await transporte.solicitarHandleRebuildProjection2({ activeDatasetId });
      const verList = (verResponse.items || []).map((item) => ({ ...item, sha256_hash: item.sha256_hash || item.data_hash || "", completeness_pct: item.completeness_pct ?? 0 }));
      setVersions(verList);
      setSelectedVersion(result.new_version);
    } catch (err: any) {
      setErrorMessage(typeof err?.detail === "string" ? err.detail : "Error al reconstruir proyección.");
    } finally {
      setActionLoading(false);
    }
  }

  const q = detail?.quality_report;

  const isZeroRows = !detail || detail.row_count === 0 || (q && q.used === 0);

  const completenessDisplay = isZeroRows ? "N/A" : `${q?.completeness_pct ?? 0}%`;

  const completenessVal = q?.completeness_pct ?? 0;

  const completenessColor = isZeroRows
    ? "bg-slate-400 text-slate-500"
    : completenessVal >= 90
      ? "bg-emerald-600 text-emerald-700"
      : completenessVal >= 70
        ? "bg-amber-500 text-amber-700"
        : "bg-rose-600 text-rose-700";
  return { ConfirmDialogNode, datasets, activeDatasetId, setActiveDatasetId, versions, selectedVersion, setSelectedVersion, detail, loading, actionLoading, statusMessage, errorMessage, rebuildNote, copiedHash, setCopiedHash, handleCreateOperationalDataset, handleGenerateNewVersionAfterCorrection, handleRebuildProjection, q, isZeroRows, completenessDisplay, completenessVal, completenessColor };
}
