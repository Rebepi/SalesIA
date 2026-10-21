import { ModalSurface } from "../../../ui/components/ModalSurface";
import { FormEvent, useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { TransferItem } from "./InventoryWorkspaceTab";

interface Product { id: string; name: string; sku: string; barcode?: string; unit_cost?: string | number }
interface Warehouse { warehouse_id: string; name: string; code: string }
const inputClass = "w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs dark:border-slate-700 dark:bg-slate-950";

export function InventoryTransferDialog({ transfer, products, warehouses, sourceId = "", productId = "", onClose, onSaved }: { transfer?: TransferItem; products: Product[]; warehouses: Warehouse[]; sourceId?: string; productId?: string; onClose: () => void; onSaved: () => void }) {
  const [source, setSource] = useState(sourceId);
  const [destination, setDestination] = useState("");
  const [lines, setLines] = useState([{ product_id: productId, quantity: "1" }]);
  const [receipts, setReceipts] = useState<Record<string, { quantity_received: string; quantity_damaged: string }>>({});
  const [scan, setScan] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const toast = useToast();
  const name = (id: string) => { const product = products.find(item => item.id === id); return product ? `${product.sku} · ${product.name}` : "Producto no disponible"; };

  async function scanProduct() {
    let product = products.find(item => item.sku.toLowerCase() === scan.trim().toLowerCase() || item.barcode === scan.trim());
    if (!product && scan.trim()) {
      try {
        const result = await apiClient.request<{ items: Product[] }>(`/api/v1/products?search=${encodeURIComponent(scan.trim())}&limit=20`);
        product = result.items.find(item => item.sku.toLowerCase() === scan.trim().toLowerCase() || item.barcode === scan.trim());
      } catch { setError("No se pudo buscar el producto. Intenta nuevamente."); return; }
    }
    if (!product) { setError("No se encontró el SKU o código de barras. Busca el producto en el selector."); return; }
    if (transfer) {
      const line = transfer.lines.find(item => item.product_id === product.id);
      const pending = line ? Number(line.quantity) - Number(line.processed_quantity) - Number(line.damaged_quantity) : 0;
      const previous = receipts[product.id] || { quantity_received: "0", quantity_damaged: "0" };
      if (!line || Number(previous.quantity_received) + Number(previous.quantity_damaged) + 1 > pending) { setError("El artículo no pertenece a la transferencia o ya completó su saldo pendiente."); return; }
      setReceipts(items => ({ ...items, [product.id]: { ...previous, quantity_received: String(Number(previous.quantity_received) + 1) } }));
    } else setLines(items => items.some(item => item.product_id === product.id) ? items.map(item => item.product_id === product.id ? { ...item, quantity: String(Number(item.quantity) + 1) } : item) : [...items.filter(item => item.product_id), { product_id: product.id, quantity: "1" }]);
    setScan("");
    setError("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    let payload: Record<string, unknown>;
    if (transfer) {
      const items = Object.entries(receipts).filter(([, item]) => Number(item.quantity_received) + Number(item.quantity_damaged) > 0).map(([product_id, item]) => ({ product_id, ...item }));
      if (!items.length) { setError("Registra por lo menos una cantidad recibida o dañada."); return; }
      for (const item of items) {
        const line = transfer.lines.find(line => line.product_id === item.product_id);
        if (!line || Number(item.quantity_received) + Number(item.quantity_damaged) > Number(line.quantity) - Number(line.processed_quantity) - Number(line.damaged_quantity)) { setError("Las cantidades recibidas y dañadas superan el saldo pendiente."); return; }
      }
      payload = { items, notes: String(form.get("notes") || "") };
    } else {
      if (!source || !destination || source === destination) { setError("Selecciona almacenes de origen y destino distintos."); return; }
      if (lines.some(line => !line.product_id || Number(line.quantity) <= 0) || new Set(lines.map(line => line.product_id)).size !== lines.length) { setError("Completa los artículos y las cantidades positivas sin repetir productos."); return; }
      payload = { source_warehouse_id: source, destination_warehouse_id: destination, notes: String(form.get("notes") || ""), items: lines.map(line => ({ ...line, unit_cost: String(products.find(product => product.id === line.product_id)?.unit_cost || "0") })) };
    }
    setBusy(true);
    setError("");
    try {
      await apiClient.request(transfer ? `/api/v1/inventory/transfers/${transfer.id}/receive` : "/api/v1/inventory/transfers", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload) });
      toast.success(transfer ? "Recepción registrada" : "Transferencia creada", transfer ? "Se actualizaron las cantidades de cada artículo. Los daños quedaron en cuarentena y los pendientes siguen en tránsito." : "Todos los artículos quedaron registrados para despacho.");
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo registrar la operación. Revisa los saldos y vuelve a intentar.")); }
    finally { setBusy(false); }
  }

  return <ModalSurface labelledBy="transfer-title" onClose={onClose} blocked={busy}><section className="app-modal-panel max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><header className="mb-4 flex justify-between"><h3 id="transfer-title" className="font-bold">{transfer ? `Recepción de ${transfer.document_number}` : "Transferencia de varios artículos"}</h3><button type="button" aria-label="Cerrar transferencia" disabled={busy} onClick={onClose}><X className="h-5 w-5" /></button></header><form onSubmit={submit} className="space-y-4">
    {!transfer && <div className="grid gap-3 sm:grid-cols-2">{[["Almacén origen", source, setSource], ["Almacén destino", destination, setDestination]].map(([label, value, setter]) => <label key={String(label)} className="text-xs font-semibold">{String(label)}<CustomSelect remote={{ resource: "warehouses" }} searchable value={String(value)} onChange={event => (setter as (value: string) => void)(event.target.value)} required className={`${inputClass} mt-1`}><option value="">Seleccionar almacén</option>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.code} · {item.name}</option>)}</CustomSelect></label>)}</div>}
    <div className="flex items-end gap-2"><label className="flex-1 text-xs font-semibold">Escanear SKU o código de barras<input value={scan} onChange={event => setScan(event.target.value)} onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); scanProduct(); } }} className={`${inputClass} mt-1`} /></label><button type="button" onClick={scanProduct} className="rounded-xl border p-2.5 text-xs">Agregar escaneo</button></div>
    {transfer ? <div className="space-y-3">{transfer.lines.map(line => { const pending = Number(line.quantity) - Number(line.processed_quantity) - Number(line.damaged_quantity); return <fieldset key={line.product_id} disabled={pending <= 0 || busy} className="rounded-xl border p-3"><legend className="px-1 text-xs font-bold">{name(line.product_id)} · Pendiente: {pending}</legend><div className="grid gap-3 sm:grid-cols-2">{([['quantity_received', 'Cantidad conforme'], ['quantity_damaged', 'Cantidad dañada']] as const).map(([key, label]) => <label key={key} className="text-xs">{label}<input type="number" min="0" max={pending} step="0.000001" value={receipts[line.product_id]?.[key] || "0"} onChange={event => setReceipts(previous => ({ ...previous, [line.product_id]: { ...(previous[line.product_id] || { quantity_received: "0", quantity_damaged: "0" }), [key]: event.target.value } }))} className={`${inputClass} mt-1`} /></label>)}</div></fieldset>; })}<p className="text-xs text-slate-500">Los faltantes permanecen pendientes para una recepción posterior. Los artículos adicionales requieren una transferencia independiente.</p></div> : <div className="space-y-3">{lines.map((line, index) => <div key={index} className="grid grid-cols-[1fr_100px_auto] items-end gap-2"><label className="text-xs">Producto<CustomSelect remote={{ resource: "products" }} searchable value={line.product_id} onChange={event => setLines(previous => previous.map((item, row) => row === index ? { ...item, product_id: event.target.value } : item))} required className={`${inputClass} mt-1`}><option value="">Seleccionar producto</option>{products.map(item => <option key={item.id} value={item.id}>{item.sku} · {item.name}</option>)}</CustomSelect></label><label className="text-xs">Cantidad<input type="number" min="0.000001" step="0.000001" required value={line.quantity} onChange={event => setLines(previous => previous.map((item, row) => row === index ? { ...item, quantity: event.target.value } : item))} className={`${inputClass} mt-1`} /></label><button type="button" aria-label={`Quitar artículo ${index + 1}`} disabled={lines.length === 1} onClick={() => setLines(previous => previous.filter((_, row) => row !== index))} className="p-2.5 disabled:opacity-30"><X className="h-4 w-4" /></button></div>)}<button type="button" onClick={() => setLines(previous => [...previous, { product_id: "", quantity: "1" }])} className="text-xs font-bold text-teal-700">Agregar artículo</button></div>}
    <label className="block text-xs font-semibold">Observaciones de la operación<textarea name="notes" maxLength={2000} className={`${inputClass} mt-1`} /></label>{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<footer className="flex justify-end gap-2 border-t pt-4"><button type="button" onClick={onClose} disabled={busy} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? "Guardando…" : transfer ? "Confirmar recepción" : "Crear transferencia"}</button></footer>
  </form></section></ModalSurface>;
}
