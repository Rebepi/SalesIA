import * as transporte from "../api/AuditWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { useEffect, useState } from "react";

import { useToast } from "../../../ui/toast/ToastContext";
import { AuditLogEntry } from "../types/AuditWorkspaceTab";
import { AuditWorkspaceTabProps } from "../types/AuditWorkspaceTab";

export function useAuditWorkspaceTab(_props: AuditWorkspaceTabProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);

  const [loading, setLoading] = useState(false);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [search, setSearch] = useState("");

  const [entityFilter, setEntityFilter] = useState("all");

  const [selectedDiff, setSelectedDiff] = useState<AuditLogEntry | null>(null);

  const [integrityStatus, setIntegrityStatus] = useState<string | null>(null);

  const [integrityTone, setIntegrityTone] = useState<"success" | "warning" | "error">("success");

  const toast = useToast();

  useEffect(() => {
    let unmounted = false;
    setLoading(true);
    setLoadError(null);
    requestAllPages<{ items: AuditLogEntry[] }>("/api/v1/audit/logs?limit=50", "cursor")
      .then((res) => {
        if (!unmounted) setLogs(res?.items || []);
      })
      .catch((failure: unknown) => {
        if (!unmounted) setLoadError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (!unmounted) setLoading(false);
      });

    return () => {
      unmounted = true;
    };
  }, []);

  const handleVerifyIntegrity = async () => {
    try {
      const result = await transporte.solicitarHandleVerifyIntegrity();
      if (!result.is_valid) {
        const detail = `${result.reason || "La cadena no coincide"}${result.broken_at_id ? ` en ${result.broken_at_id}` : ""}.`;
        setIntegrityStatus(detail);
        setIntegrityTone("error");
        toast.error("Integridad comprometida", detail);
        return;
      }
      if ((result.legacy_unsealed_count || 0) > 0) {
        const detail = `${result.verified_count} registros sellados son válidos y ${result.legacy_unsealed_count} registros históricos no tienen sello.`;
        setIntegrityStatus(detail);
        setIntegrityTone("warning");
        toast.warning("Verificación con registros heredados", detail);
        return;
      }
      const detail = `${result.verified_count} registros verificados sin alteraciones.`;
      setIntegrityStatus(detail);
      setIntegrityTone("success");
      toast.success("Integridad verificada", detail);
    } catch (failure: unknown) {
      const detail = String((failure as { detail?: string }).detail || failure);
      setIntegrityStatus(`No se pudo verificar la cadena: ${detail}`);
      setIntegrityTone("error");
      toast.error("Verificación fallida", detail);
    }
  };

  const handleExport = async () => {
    try {
      const exported = await transporte.solicitarHandleExport();
      const blob = new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `auditoria-${exported.exported_at.replace(/[:.]/g, "-")}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      toast.success("Exportación completada", `Archivo sellado con ${exported.cryptographic_seal}.`);
    } catch (failure: unknown) {
      toast.error("No se pudo exportar la auditoría", String((failure as { detail?: string }).detail || failure));
    }
  };

  const filteredLogs = logs.filter((l) => {
    const matchesEntity = entityFilter === "all" || l.entity_type.toLowerCase() === entityFilter.toLowerCase();
    const matchesSearch =
      l.actor_email.toLowerCase().includes(search.toLowerCase()) ||
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.trace_id.toLowerCase().includes(search.toLowerCase()) ||
      l.entity_id.toLowerCase().includes(search.toLowerCase());
    return matchesEntity && matchesSearch;
  });
  return { loading, loadError, search, setSearch, entityFilter, setEntityFilter, selectedDiff, setSelectedDiff, integrityStatus, integrityTone, handleVerifyIntegrity, handleExport, filteredLogs };
}
