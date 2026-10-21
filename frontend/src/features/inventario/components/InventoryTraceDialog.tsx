import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";
interface Trace { code: string; product_name: string; sku: string; status: string; warehouse?: string; location?: string; expiration_date?: string; coverage: string; truncated: boolean; events: { id: string; date: string; title: string; code?: string; quantity?: string; warehouse?: string; details?: string }[] }
const states: Record<string, string> = { ACTIVE: "Activo", BLOCKED: "Bloqueado", IN_STOCK: "Disponible", IN_QUARANTINE: "En cuarentena", SOLD: "Vendido", REJECTED: "Rechazado", SCRAPPED: "Descartado", RETURNED_TO_SUPPLIER: "Devuelto al proveedor" };
export function inventoryTrackingStatus(value: string) { return states[value] || value; }
export function InventoryTraceDialog({ kind, id, onClose }: { kind: "lot" | "serial"; id: string; onClose: () => void }) {
  const [trace, setTrace] = useState<Trace>();
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setTrace(undefined);
    setError("");
    apiClient.request<Trace>(`/api/v1/inventory/${kind === "lot" ? "lots" : "serials"}/${id}/trace`, { signal: controller.signal }).then(value => { if (!controller.signal.aborted) setTrace(value); }).catch(failure => { if (!controller.signal.aborted) setError(failure?.detail || "No se pudo consultar la trazabilidad. Reintenta la consulta."); });
    return () => controller.abort();
  }, [kind, id, revision]);
  return <ModalSurface labelledBy="inventory-trace-title" onClose={onClose}><section className="app-modal-panel w-[min(720px,94vw)] rounded-2xl bg-white p-5"><header className="flex items-center justify-between gap-3"><h2 id="inventory-trace-title" className="text-lg font-bold">Trazabilidad de {kind === "lot" ? "lote" : "serie"}</h2><button type="button" aria-label="Cerrar trazabilidad" onClick={onClose}><X className="h-5 w-5" /></button></header>{error ? <div role="alert" className="mt-4 rounded-xl bg-rose-50 p-3 text-sm text-rose-800"><p>{error}</p><button className="mt-2 underline" onClick={() => setRevision(value => value + 1)}>Reintentar</button></div> : !trace ? <p role="status" className="p-6 text-sm">Consultando origen y actividad…</p> : <><div className="mt-4 rounded-xl border p-3"><h3 className="font-semibold">{trace.product_name} · {trace.sku}</h3><p className="mt-1 text-sm">{trace.code} · {inventoryTrackingStatus(trace.status)}</p>{trace.warehouse && <p className="text-xs text-slate-500">Almacén de registro: {trace.warehouse}{trace.location ? ` · Ubicación: ${trace.location}` : ""}</p>}{trace.expiration_date && <p className="text-xs text-slate-500">Caducidad: {new Date(trace.expiration_date).toLocaleDateString("es-PE", { timeZone: "UTC" })}</p>}</div><p className="mt-3 text-xs text-slate-500">{trace.coverage}</p>{trace.truncated && <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">Esta vista alcanza las últimas 200 recepciones y 200 acciones. Consulta auditoría para ampliar el periodo.</p>}<ol className="mt-4 space-y-3">{trace.events.map(event => <li key={event.id} className="rounded-xl border p-3"><div className="flex flex-wrap items-center justify-between gap-2"><strong className="text-sm">{event.title}</strong><time className="text-xs text-slate-500">{new Date(event.date).toLocaleString("es-PE", { timeZone: "America/Lima" })}</time></div>{event.quantity && <p className="mt-1 text-xs">Cantidad: {event.quantity}</p>}{event.warehouse && <p className="text-xs text-slate-500">{event.warehouse}</p>}{event.details && <p className="mt-1 text-xs text-slate-600">{event.details}</p>}{event.code && <details className="mt-1 text-[10px] text-slate-500"><summary>Código del evento</summary><code>{event.code}</code></details>}</li>)}</ol></>}</section></ModalSurface>;
}
