import { useEffect, useState } from "react";
import { listarClientes } from "../api/listadoApi";
import type { Row } from "../types/clientes";
import { message } from "../utils/mensajes";

interface ListadoClientesOptions {
  enabled: boolean;
  page: number;
  pageSize: number;
  search: string;
  revision: number;
  onPageChange: (page: number) => void;
  onErrorReset: (message: string) => void;
}

export function useListadoClientes({ enabled, page, pageSize, search, revision, onPageChange, onErrorReset }: ListadoClientesOptions) {
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    onErrorReset("");
    setRows([]);

    listarClientes(page, pageSize, search, controller.signal).then(result => {
      if (controller.signal.aborted) return;
      const items = Array.isArray(result) ? result : result.items;
      const recordCount = Array.isArray(result) ? items.length : result.total_count ?? result.count ?? items.length;
      const lastPage = Math.max(0, Math.ceil(recordCount / pageSize) - 1);
      setTotal(recordCount);
      if (page > lastPage) {
        onPageChange(lastPage);
        return;
      }
      setRows(items);
    }).catch(failure => {
      if (!controller.signal.aborted) setError(message(failure));
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });

    return () => controller.abort();
  }, [enabled, page, pageSize, search, revision, onPageChange, onErrorReset]);

  return { rows, total, loading, error };
}
