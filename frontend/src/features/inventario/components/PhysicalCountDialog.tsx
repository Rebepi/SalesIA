import { ModalSurface } from "../../../ui/components/ModalSurface";
import { useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { CountItem } from "./InventoryWorkspaceTab";

interface Product { id: string; sku: string; name: string; barcode?: string }

export function PhysicalCountDialog({ count, products, onClose, onSaved, canWrite = true }: { canWrite?: boolean; count: CountItem; products: Product[]; onClose: () => void; onSaved: () => void }) {
  const [entries, setEntries] = useState<Record<string, string>>(Object.fromEntries(count.lines.filter(line => line.counted_at).map(line => [line.product_id, line.counted_quantity || "0"])));
  const [scan, setScan] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const readOnly = !canWrite || !["in_progress", "pending_count"].includes(count.status.toLowerCase());
  const complete = count.lines.every(line => entries[line.product_id] !== undefined && entries[line.product_id] !== "");

  function scanProduct() {
    const product = products.find(item => item.sku.toLowerCase() === scan.trim().toLowerCase() || item.barcode === scan.trim());
    if (!product || !count.lines.some(line => line.product_id === product.id)) { setError("El producto escaneado no pertenece a este conteo."); return; }
    setEntries(previous => ({ ...previous, [product.id]: String(Number(previous[product.id] || "0") + 1) }));
    setScan("");
    setError("");
  }

  async function save(submit: boolean) {
    const items = Object.entries(entries).filter(([, value]) => value !== "").map(([product_id, quantity]) => ({ product_id, quantity }));
    if (!items.length || items.some(item => !Number.isFinite(Number(item.quantity)) || Number(item.quantity) < 0)) { setError("Registra cantidades válidas, incluido cero cuando corresponda."); return; }
    setBusy(true);
    try {
      await apiClient.request(`/api/v1/inventory/counts/${count.id}/entries`, { method: "PUT", body: JSON.stringify({ items, submit, version: count.version || 1 }) });
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo guardar el conteo. Actualiza y vuelve a intentar.")); }
    finally { setBusy(false); }
  }

  return <ModalSurface labelledBy="count-title" onClose={onClose} blocked={busy}><section className="app-modal-panel max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><header className="mb-4 flex justify-between"><div><h3 id="count-title" className="font-bold">{count.count_code || "Conteo físico"}</h3><p className="text-xs text-slate-500">{readOnly ? "Revisión de cantidades y diferencias" : "Registra cada producto. Las cantidades sin registrar nunca se consideran cero."}</p></div><button type="button" onClick={onClose} disabled={busy} aria-label="Cerrar conteo"><X className="h-5 w-5" /></button></header>
    {!readOnly && <div className="mb-4 flex items-end gap-2"><label className="flex-1 text-xs font-semibold">Escanear SKU o código de barras<input value={scan} onChange={event => setScan(event.target.value)} onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); scanProduct(); } }} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label><button type="button" onClick={scanProduct} className="rounded-xl border p-2.5 text-xs">Contar una unidad</button></div>}
    <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-2">Producto</th><th className="p-2">Cantidad contada</th>{readOnly && <><th className="p-2">Sistema al corte</th><th className="p-2">Diferencia</th></>}</tr></thead><tbody>{count.lines.map(line => { const product = products.find(item => item.id === line.product_id); return <tr key={line.product_id} className="border-t"><td className="p-2"><strong>{product?.sku || "Producto registrado"}</strong><p>{product?.name || "Consulta el catálogo autorizado"}</p></td><td className="p-2">{readOnly ? line.counted_quantity : <input aria-label={`Cantidad contada de ${product?.sku || "producto"}`} type="number" min="0" step="0.000001" value={entries[line.product_id] ?? ""} placeholder="Sin contar" onChange={event => setEntries(previous => ({ ...previous, [line.product_id]: event.target.value }))} className="w-28 rounded-xl border p-2 dark:bg-slate-950" />}</td>{readOnly && <><td className="p-2">{line.snapshot_system_quantity ?? "Conteo ciego"}</td><td className="p-2">{line.discrepancy_quantity ?? "Pendiente de revisión"}</td></>}</tr>; })}</tbody></table></div>
    {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<footer className="mt-4 flex flex-wrap justify-end gap-2 border-t pt-4"><button type="button" disabled={busy} onClick={onClose} className="rounded-xl border px-4 py-2 text-xs">Cerrar</button>{!readOnly && <><button type="button" disabled={busy} onClick={() => save(false)} className="rounded-xl border px-4 py-2 text-xs">Guardar avance</button><button type="button" disabled={busy || !complete} title={!complete ? "Falta registrar uno o más productos" : "Un usuario distinto deberá aprobar los ajustes"} onClick={() => save(true)} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">Enviar a revisión</button></>}</footer>
  </section></ModalSurface>;
}
