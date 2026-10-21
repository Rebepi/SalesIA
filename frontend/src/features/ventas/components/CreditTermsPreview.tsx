import { useEffect, useState } from "react";
import { apiClient } from "../../../api/client";

type Preview = { at: string; timezone: string; basis: string; roll: string; version: number; companyVersion: number; configured: boolean };
const rolls: Record<string, string> = { none: "Se conserva la fecha", next: "Siguiente día hábil", previous: "Día hábil anterior", modified_next: "Siguiente hábil, o anterior si cambia el mes" };

export function CreditTermsPreview({ branchId, days }: { branchId?: string; days: number }) {
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setPreview(null); setError("");
    const start = new Date();
    void apiClient.request<{ configured: boolean; timezone: string; version: number; company_version: number }>(`/api/v1/organization/operating-calendar${branchId ? `?branch_id=${branchId}` : ""}`, { signal: controller.signal }).then(async calendar => {
      if (controller.signal.aborted) return;
      if (!calendar.configured) {
        setPreview({ at: new Date(start.getTime() + days * 86400000).toISOString(), timezone: calendar.timezone, basis: "calendar", roll: "none", version: calendar.version, companyVersion: calendar.company_version, configured: false });
        return;
      }
      const result = await apiClient.request<{ at: string; basis: string; roll: string }>("/api/v1/organization/operating-calendar/calculate", { method: "POST", signal: controller.signal, body: JSON.stringify({ branch_id: branchId || null, start_at: start.toISOString(), days, purpose: "payment", respect_cutoff: false }) });
      if (!controller.signal.aborted) setPreview({ ...result, timezone: calendar.timezone, version: calendar.version, companyVersion: calendar.company_version, configured: true });
    }).catch(() => { if (!controller.signal.aborted) setError("No se pudo consultar el vencimiento estimado. La confirmación aplicará las reglas vigentes."); });
    return () => controller.abort();
  }, [branchId, days]);
  return <div className="space-y-1 text-[11px]">{error ? <p role="alert">{error}</p> : preview ? <><p>Vencimiento estimado: <strong>{new Date(preview.at).toLocaleString("es-PE", { timeZone: preview.timezone })}</strong> · {preview.timezone}</p><p>{days} días {preview.basis === "business" ? "hábiles" : "calendario"} · {rolls[preview.roll]}</p><p>{preview.configured ? `Calendario de sede ${preview.version} / empresa ${preview.companyVersion}.` : "Se conserva el cómputo de días transcurridos hasta configurar un calendario."} La fecha definitiva se fija al confirmar. Las cuotas se pactan desde Cuentas por cobrar.</p></> : <p role="status">Consultando condiciones de vencimiento…</p>}</div>;
}
