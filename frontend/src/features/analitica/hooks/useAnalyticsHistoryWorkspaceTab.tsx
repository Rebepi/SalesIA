import * as transporte from "../api/AnalyticsHistoryWorkspaceTab";
import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";
import type { AnalyticsExecutionRun, AnalysisApiRecord, AnalyticsHistoryWorkspaceTabProps } from "../types/AnalyticsHistoryWorkspaceTab";
import { toExecutionRun } from "../support/AnalyticsHistoryWorkspaceTab";

function message(cause: unknown) {
  const detail = (cause as { detail?: unknown })?.detail;
  return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo completar la operación.";
}
export function useAnalyticsHistoryWorkspaceTab({ canWrite = true }: AnalyticsHistoryWorkspaceTabProps) {
  const [runs, setRuns] = useState<AnalyticsExecutionRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [selectedRuns, setSelectedRuns] = useState<AnalyticsExecutionRun[]>([]);
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [repeatingId, setRepeatingId] = useState<string | null>(null);
  const repeatLock = useRef(false);
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("");
  const [detailRun, setDetailRun] = useState<AnalyticsExecutionRun | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const detailController = useRef<AbortController | null>(null);
  useEffect(() => () => detailController.current?.abort(), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    const query = new URLSearchParams({ limit: String(pageSize), offset: String(page * pageSize) });
    if (status) query.set("status_filter", status);
    void apiClient.request<{ items: AnalysisApiRecord[]; count: number }>(`/api/v1/analyses?${query}`, { signal: controller.signal }).then(response => {
      if (controller.signal.aborted) return;
      const total = response.count || 0;
      const lastPage = Math.max(0, Math.ceil(total / pageSize) - 1);
      if (page > lastPage) { setPage(lastPage); return; }
      setRuns(response.items.map(toExecutionRun)); setTotal(total);
    }).catch(cause => { if (!controller.signal.aborted) { setError(message(cause)); setRuns([]); } }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [page, pageSize, status, revision]);
  async function handleRepeatRun(original: AnalyticsExecutionRun) {
    if (!canWrite || repeatLock.current || !original.is_reproducible) return;
    repeatLock.current = true; setRepeatingId(original.id); setActionError(""); setNotice("");
    try {
      const repeated = toExecutionRun(await transporte.solicitarHandleRepeatRun({ original }));
      setNotice(`Se creó «${repeated.code}» sobre la versión ${repeated.dataset_version}. La ejecución original se conserva.`);
      detailController.current?.abort(); setDetailLoading(false); setDetailError(""); setStatus(""); setPage(0); setRevision(value => value + 1); setDetailRun(repeated);
    } catch (cause) { setActionError(message(cause)); }
    finally { repeatLock.current = false; setRepeatingId(null); }
  }
  function toggleSelectForCompare(id: string) {
    const run = runs.find(item => item.id === id);
    if (!run) return;
    setSelectedRuns(previous => previous.some(item => item.id === id) ? previous.filter(item => item.id !== id) : previous.length < 2 ? [...previous, run] : previous);
  }
  async function showDetail(run: AnalyticsExecutionRun) {
    detailController.current?.abort();
    const controller = new AbortController(); detailController.current = controller;
    setDetailRun(run); setDetailLoading(true); setDetailError("");
    try {
      const record = await apiClient.request<AnalysisApiRecord>(`/api/v1/analyses/${run.id}`, { signal: controller.signal });
      if (!controller.signal.aborted) setDetailRun(toExecutionRun(record));
    } catch (cause) { if (!controller.signal.aborted) setDetailError(message(cause)); }
    finally { if (!controller.signal.aborted) setDetailLoading(false); }
  }
  function closeDetail() { detailController.current?.abort(); setDetailRun(null); setDetailLoading(false); setDetailError(""); }
  return { runs, loading, error, actionError, notice, selectedForCompare: selectedRuns.map(run => run.id), compareModalOpen, setCompareModalOpen, repeatingId, handleRepeatRun, toggleSelectForCompare, runA: selectedRuns[0], runB: selectedRuns[1], clearSelection: () => setSelectedRuns([]), refresh: () => setRevision(value => value + 1), page, setPage, pageSize, setPageSize, total, status, setStatus, detailRun, detailLoading, detailError, showDetail, closeDetail };
}
