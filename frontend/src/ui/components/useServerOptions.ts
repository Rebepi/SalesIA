import { useEffect, useState } from "react";
import { apiClient } from "../../api/client";

export type ServerOption = { value: string; label: string };
export type ServerSelectSource = { resource: string; branch_id?: string; warehouse_id?: string; exclude_id?: string; exclude_subtree?: string; active_only?: boolean };

export function useServerOptions(source: ServerSelectSource | undefined, open: boolean, search: string, value: string) {
  const [rows, setRows] = useState<ServerOption[]>([]);
  const [selections, setSelections] = useState<ServerOption[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const scope = JSON.stringify(source);
  useEffect(() => { setOffset(0); setRows([]); setHasMore(false); }, [scope, search, open]);
  useEffect(() => {
    if (!source || !value) { setSelections([]); return; }
    const controller = new AbortController();
    const params = new URLSearchParams({ [source.resource === "teams" ? "selected_value" : "ids"]: value, limit: "50" });
    for (const [key, item] of Object.entries(source)) if (key !== "resource" && item !== undefined && item !== "") params.set(key, String(item));
    void apiClient.request<{ items: ServerOption[] }>(`/api/v1/selector-options/${source.resource}?${params}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setSelections(result.items); }).catch(() => { if (!controller.signal.aborted) setSelections([]); });
    return () => controller.abort();
  }, [scope, value]);
  useEffect(() => {
    if (!source || !open) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = window.setTimeout(async () => {
      const params = new URLSearchParams({ search, limit: "20", offset: String(offset) });
      for (const [key, item] of Object.entries(source)) if (key !== "resource" && item !== undefined && item !== "") params.set(key, String(item));
      try {
        const result = await apiClient.request<{ items: ServerOption[]; has_more: boolean }>(`/api/v1/selector-options/${source.resource}?${params}`, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setRows(previous => offset === 0 ? result.items : [...previous, ...result.items.filter(item => !previous.some(row => row.value === item.value))]);
        setHasMore(result.has_more);
      } catch {
        if (!controller.signal.aborted) setError("No se pudieron cargar las opciones.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [scope, open, search, offset]);
  return { rows, selections, chosen: selections[0], hasMore, loading, error, loadMore: () => setOffset(previous => previous + 20) };
}
