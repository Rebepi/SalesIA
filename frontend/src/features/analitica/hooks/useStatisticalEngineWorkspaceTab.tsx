import * as transporte from "../api/StatisticalEngineWorkspaceTab";
import { useEffect, useMemo, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { StatisticalDataset } from "../types/StatisticalEngineWorkspaceTab";
import { StatisticalCalculationResult } from "../types/StatisticalEngineWorkspaceTab";
import { StatisticalEngineWorkspaceTabProps } from "../types/StatisticalEngineWorkspaceTab";
import { problemMessage } from "../support/StatisticalEngineWorkspaceTab";

export function useStatisticalEngineWorkspaceTab({ canWrite = true }: StatisticalEngineWorkspaceTabProps) {
  const [datasets, setDatasets] = useState<StatisticalDataset[]>([]);

  const [discoveredVariables, setDiscoveredVariables] = useState<Array<{ name: string; label: string }>>([]);

  const [selectedDatasetId, setSelectedDatasetId] = useState("");

  const [selectedVariable, setSelectedVariable] = useState("");

  const [nullPolicy, setNullPolicy] = useState("skip");

  const [precision, setPrecision] = useState(4);

  const [loadingDatasets, setLoadingDatasets] = useState(true);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [result, setResult] = useState<StatisticalCalculationResult | null>(null);

  const toast = useToast();

  const selectedDataset = useMemo(
    () => datasets.find((dataset) => dataset.id === selectedDatasetId) ?? null,
    [datasets, selectedDatasetId]
  );

  const availableVariables = useMemo(() => {
    const declared = (selectedDataset?.variables ?? [])
      .filter((variable) => !variable.nature || variable.nature === "metric" || variable.scale === "ratio" || variable.scale === "interval" || variable.scale?.startsWith("quantitative"))
      .map((variable) => ({
        name: variable.name || variable.variable_name || "",
        label: variable.label || variable.name || variable.variable_name || ""
      }))
      .filter((variable) => variable.name);
    return declared.length > 0 ? declared : discoveredVariables;
  }, [discoveredVariables, selectedDataset]);

  useEffect(() => {
    let active = true;
    const loadDatasets = async () => {
      setLoadingDatasets(true);
      setError("");
      try {
        const response = await transporte.solicitarLoadDatasets();
        if (!active) return;
        const usable = response.items.filter((dataset) => dataset.active_version > 0);
        setDatasets(usable);
        setSelectedDatasetId((current) => current || usable[0]?.id || "");
      } catch (requestError) {
        if (!active) return;
        setError(problemMessage(requestError));
      } finally {
        if (active) setLoadingDatasets(false);
      }
    };
    void loadDatasets();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    if (!selectedDataset) {
      setDiscoveredVariables([]);
      return () => {
        active = false;
      };
    }
    transporte.solicitarDatos({ selectedDataset })
      .then((detail) => {
        if (!active) return;
        const rows = detail.sample || detail.preview_sample || [];
        const keys = rows[0] ? Object.keys(rows[0]).filter((key) => rows.some((row) => row[key] !== null && row[key] !== undefined && row[key] !== "" && Number.isFinite(Number(row[key])))) : [];
        setDiscoveredVariables(keys.map((name) => ({ name, label: name })));
      })
      .catch((requestError) => {
        if (active) setError(problemMessage(requestError));
      });
    return () => {
      active = false;
    };
  }, [selectedDataset]);

  useEffect(() => {
    if (!availableVariables.some((variable) => variable.name === selectedVariable)) {
      setSelectedVariable(availableVariables[0]?.name || "");
    }
    setResult(null);
  }, [availableVariables, selectedDatasetId, selectedVariable]);

  const handleExecute = async () => {
    if (!selectedDataset || !selectedVariable) return;
    setLoading(true);
    setError("");
    try {
      const response = await transporte.solicitarHandleExecute({ selectedDataset, selectedVariable, nullPolicy, precision });
      setResult(response);
      toast.success("Cálculo estadístico finalizado", `n=${response.n}, media=${response.mean}, mediana=${response.median}`);
    } catch (requestError) {
      const message = problemMessage(requestError);
      setError(message);
      toast.error("No se pudo ejecutar el cálculo", message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportMemory = () => {
    if (!result || !selectedDataset) return;
    const memory = {
      dataset: { id: selectedDataset.id, name: selectedDataset.name, version: result.dataset_version },
      variable: selectedVariable,
      null_policy: nullPolicy,
      precision,
      results: result,
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(memory, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `memoria-calculo-${selectedVariable}-${result.algorithm_version}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Memoria exportada", "La memoria incluye el dataset, la versión, los parámetros y el resultado reproducible.");
  };

  const canExecute = canWrite && Boolean(selectedDataset && selectedVariable) && !loading && !loadingDatasets;
  return { datasets, selectedDatasetId, setSelectedDatasetId, selectedVariable, setSelectedVariable, nullPolicy, setNullPolicy, precision, setPrecision, loadingDatasets, loading, error, result, selectedDataset, availableVariables, handleExecute, handleExportMemory, canExecute };
}
