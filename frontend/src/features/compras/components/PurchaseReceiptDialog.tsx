import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { Paperclip, Plus, RefreshCw, ScanLine, Trash2, X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { useToast } from "../../../ui/toast/ToastContext";
import { useUnsavedChanges } from "../../../ui/drafts";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { ModalSurface } from "../../../ui/components/ModalSurface";

type Quality = "accepted" | "quarantine" | "rejected";
interface SourceLine { product_id: string; name: string; sku: string; tracking_mode: string; ordered_quantity: string; received_quantity: string; rejected_quantity: string; pending_quantity: string; unit_cost: string }
interface Lot { lot_code: string; quantity: string; manufacture_date: string; expiration_date: string }
interface Entry { quantity: string; status: Quality; notes: string; location: string; lots: Lot[]; serials: string }
interface Attachment { id: string; file_name: string }
interface Receipt { id: string; status: string; created_at: string; lines: { product_id: string; quantity: string }[]; details: { notes?: string; inspections?: { product_id: string; sku: string; product_name: string; quantity: string; status: string; resolution?: string; notes?: string; lots?: { lot_code: string }[]; serial_numbers?: string[] }[]; attachments?: Attachment[] } }
interface Context { order_id: string; version: number; status: string; warehouse_id: string; warehouse_name: string; supplier_name: string; currency: string; lines: SourceLine[]; locations: { id: string; code: string }[]; receipts: Receipt[] }
const qualityLabel = { accepted: "Aceptado", quarantine: "En cuarentena", rejected: "Rechazado", mixed: "Inspección por artículo" };
const emptyEntry = (): Entry => ({ quantity: "", status: "accepted", notes: "", location: "", lots: [], serials: "" });

export function PurchaseReceiptDialog({ orderId, onClose, onSaved, canWrite = true }: { orderId: string; canWrite?: boolean; onClose: () => void; onSaved: (receiptId: string) => void }) {
  const [context, setContext] = useState<Context>();
  const [entries, setEntries] = useState<Record<string, Entry>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [scan, setScan] = useState("");
  const [scanMessage, setScanMessage] = useState("");
  const [notes, setNotes] = useState("");
  const [difference, setDifference] = useState("");
  const [tolerance, setTolerance] = useState("0");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const key = useRef(crypto.randomUUID());
  const toast = useToast();
  const { confirm, ConfirmDialogNode } = useConfirm();
  const dirty = Object.values(entries).some(item => Number(item.quantity) > 0 || item.notes || item.serials || item.lots.length) || Boolean(notes || attachments.length);
  useUnsavedChanges(dirty);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const result = await apiClient.request<Context>(`/api/v1/purchase-orders/${orderId}/receiving-context`);
      setContext(result);
      setEntries(previous => Object.fromEntries(result.lines.map(line => [line.product_id, previous[line.product_id] || emptyEntry()])));
    } catch (failure: unknown) { setError(message(failure, "No se pudo cargar la orden. Reintenta antes de recibir.")); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [orderId]);

  function message(failure: unknown, fallback: string) { return failure && typeof failure === "object" && "detail" in failure ? String(failure.detail) : fallback; }
  function update(id: string, patch: Partial<Entry>) { setEntries(previous => ({ ...previous, [id]: { ...previous[id], ...patch } })); }
  function updateLot(id: string, index: number, field: keyof Lot, value: string) {
    setEntries(previous => ({ ...previous, [id]: { ...previous[id], lots: previous[id].lots.map((lot, row) => row === index ? { ...lot, [field]: value } : lot) } }));
  }
  function serials(value: string) { return value.split(/[\r\n,;]+/).map(item => item.trim()).filter(Boolean); }
  async function close() {
    if (busy || uploading) return;
    if (dirty && !await confirm({ title: "¿Cerrar la recepción?", text: "Los datos ingresados no se han confirmado. La orden conservará sus saldos actuales.", confirmLabel: "Cerrar recepción" })) return;
    onClose();
  }
  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;
    if (files.length + attachments.length > 20) { setError("Puedes adjuntar hasta veinte archivos por recepción."); return; }
    setUploading(true);
    setError("");
    try {
      for (const file of files) {
        if (!["application/pdf", "image/png", "image/jpeg"].includes(file.type)) throw new Error("Elige archivos PDF, PNG o JPG para documentar la recepción.");
        const intent = await apiClient.request<{ attachment_id: string; upload_url: string; upload_token: string }>("/api/v1/attachments/upload-intents", { method: "POST", body: JSON.stringify({ file_name: file.name, mime_type: file.type, file_size_bytes: file.size, related_entity_type: "purchase_order", related_entity_id: orderId }) });
        await apiClient.request(intent.upload_url, { method: "PUT", headers: { "Content-Type": file.type, "X-Upload-Token": intent.upload_token }, body: await file.arrayBuffer() });
        await apiClient.request(`/api/v1/attachments/${intent.attachment_id}/complete`, { method: "POST", body: "{}" });
        setAttachments(previous => [...previous, { id: intent.attachment_id, file_name: file.name }]);
      }
    } catch (failure: unknown) { setError(message(failure, failure instanceof Error ? failure.message : "No se pudo verificar el adjunto. Los archivos ya verificados se conservaron.")); }
    finally { setUploading(false); }
  }
  async function download(attachment: Attachment) {
    try {
      const result = await apiClient.downloadBlob(`/api/v1/attachments/${attachment.id}/download`);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename || attachment.file_name;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) { toast.error("No se pudo descargar", message(failure, "Revisa tus permisos y vuelve a intentar.")); }
  }
  function scanSku(event: FormEvent) {
    event.preventDefault();
    const line = context?.lines.find(item => item.sku.toLocaleLowerCase() === scan.trim().toLocaleLowerCase());
    if (!line) { setScanMessage("No se encontró ese SKU entre los artículos de la orden."); return; }
    update(line.product_id, { quantity: String(Number(entries[line.product_id].quantity || 0) + 1) });
    setScanMessage(`${line.name}: se agregó una unidad al conteo de recepción.`);
    setScan("");
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!context || !canWrite || busy || loading || uploading) return;
    const selected = context.lines.filter(line => Number(entries[line.product_id]?.quantity) > 0);
    if (!selected.length) { setError("Ingresa la cantidad recibida de al menos un artículo."); return; }
    for (const line of selected) {
      const entry = entries[line.product_id];
      if (Number(entry.quantity) > Number(line.ordered_quantity) * (1 + Number(tolerance) / 100) - Number(line.received_quantity)) { setError(`La cantidad de ${line.sku} supera el saldo y la tolerancia indicada.`); return; }
      if (Number(entry.quantity) > Number(line.pending_quantity) && difference.trim().length < 3) { setError("Explica la diferencia antes de recibir unidades adicionales."); return; }
      if (entry.status !== "accepted" && entry.notes.trim().length < 3) { setError(`Explica el resultado de inspección de ${line.sku}.`); return; }
      if (line.tracking_mode === "LOT" && (!entry.lots.length || entry.lots.some(lot => !lot.lot_code.trim() || Number(lot.quantity) <= 0) || Math.abs(entry.lots.reduce((sum, lot) => sum + Number(lot.quantity), 0) - Number(entry.quantity)) > 0.000001)) { setError(`Los lotes de ${line.sku} deben sumar la cantidad recibida.`); return; }
      if (line.tracking_mode === "SERIAL" && (serials(entry.serials).length !== Number(entry.quantity) || new Set(serials(entry.serials)).size !== serials(entry.serials).length)) { setError(`Ingresa una serie distinta por cada unidad de ${line.sku}.`); return; }
    }
    if (!await confirm({ title: "¿Confirmar recepción?", text: `Se registrarán ${selected.length} artículos. Solo las líneas aceptadas aumentarán el stock disponible; la cuarentena quedará retenida y el rechazo conservará cantidades pendientes de reemplazo.`, confirmLabel: "Registrar recepción" })) return;
    setBusy(true);
    setError("");
    try {
      const result = await apiClient.request<{ id: string }>("/api/v1/goods-receipts", { method: "POST", headers: { "Idempotency-Key": key.current }, body: JSON.stringify({ purchase_order_id: orderId, warehouse_id: context.warehouse_id, order_version: context.version, tolerance_percentage: String(Number(tolerance) / 100), notes: notes || null, difference_reason: difference || null, attachment_ids: attachments.map(item => item.id), items: selected.map(line => { const entry = entries[line.product_id]; return { product_id: line.product_id, quantity: entry.quantity, unit_cost: line.unit_cost, inspection_status: entry.status, inspection_notes: entry.notes || null, location_id: entry.location || null, lots: entry.lots.map(lot => ({ ...lot, manufacture_date: lot.manufacture_date || null, expiration_date: lot.expiration_date || null })), serial_numbers: serials(entry.serials) }; }) }) });
      toast.success("Recepción registrada", "Se actualizaron los saldos y la trazabilidad de los artículos.");
      onSaved(result.id);
    } catch (failure) { setError(message(failure, "No se pudo confirmar la recepción. Revisa los saldos antes de reintentar.")); }
    finally { setBusy(false); }
  }
  return <ModalSurface labelledBy="purchase-receipt-title" onClose={() => void close()} blocked={busy || uploading}>
    <section id="scr-027-receptions-modal" className="app-modal-panel w-[min(1050px,94vw)] rounded-2xl bg-white p-5">
      <header className="flex items-center justify-between gap-3"><div><h2 id="purchase-receipt-title" className="text-lg font-bold">Recepción de compra</h2><p className="text-xs text-slate-500">{context ? `${context.supplier_name} · ${context.warehouse_name} · versión ${context.version}` : "Cargando documento de origen"}</p></div><button disabled={busy || uploading} aria-label="Cerrar recepción" onClick={() => void close()}><X className="h-5 w-5" /></button></header>
      {error && <p role="alert" className="mt-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
      <button type="button" disabled={busy || uploading || loading} onClick={() => void load()} className="mt-3 inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs"><RefreshCw className="h-4 w-4" />Actualizar saldos</button>
      {loading ? <p role="status" className="p-6">Cargando saldos y recepciones anteriores…</p> : context && <>
        <form onSubmit={scanSku} className="mt-4 flex gap-2"><label className="sr-only" htmlFor="receipt-scan">Escanear SKU de la orden</label><input id="receipt-scan" disabled={busy || !canWrite || !["approved", "submitted", "partially_received"].includes(context.status)} value={scan} onChange={event => setScan(event.target.value)} placeholder="Escanear SKU para contar una unidad" className="min-w-0 flex-1 rounded-xl border p-2 text-sm" /><button type="submit" disabled={busy || !canWrite} className="inline-flex items-center gap-1 rounded-xl border px-3 text-xs"><ScanLine className="h-4 w-4" />Contar</button></form><p role="status" className="mt-1 text-xs text-teal-700">{scanMessage}</p>
        <form onSubmit={submit} className="mt-4 space-y-4"><fieldset disabled={busy || uploading || !canWrite || !["approved", "submitted", "partially_received"].includes(context.status)} className="space-y-3">
          {context.lines.map(line => {
            const entry = entries[line.product_id]; if (!entry) return null; return <article key={line.product_id} className="rounded-xl border border-slate-200 p-3"><div className="flex flex-wrap justify-between gap-2"><div><h3 className="text-sm font-bold">{line.name} <span className="font-mono text-xs text-slate-500">{line.sku}</span></h3><p className="text-xs text-slate-500">Pedido {line.ordered_quantity} · Recibido {line.received_quantity} · Rechazado {line.rejected_quantity} · <strong>Pendiente {line.pending_quantity}</strong></p></div><button type="button" onClick={() => update(line.product_id, { quantity: line.pending_quantity })} disabled={Number(line.pending_quantity) <= 0} className="rounded-lg border px-2 py-1 text-xs disabled:opacity-50">Recibir pendiente de {line.sku}</button></div><div className="mt-3 grid gap-3 sm:grid-cols-3"><label className="text-xs">Cantidad recibida<input aria-label={`Cantidad recibida de ${line.sku}`} type="number" min="0" step="any" value={entry.quantity} onChange={event => update(line.product_id, { quantity: event.target.value })} className="mt-1 w-full rounded-lg border p-2" /></label><label className="text-xs">Inspección<CustomSelect aria-label={`Inspección de ${line.sku}`} value={entry.status} onChange={event => update(line.product_id, { status: event.target.value as Quality })} className="mt-1 w-full"><option value="accepted">Aceptado a stock</option><option value="quarantine">En cuarentena</option><option value="rejected">Rechazado</option></CustomSelect></label><label className="text-xs">Ubicación<CustomSelect remote={{ resource: "locations" }} aria-label={`Ubicación de ${line.sku}`} value={entry.location} onChange={event => update(line.product_id, { location: event.target.value })} className="mt-1 w-full"><option value="">Sin ubicación específica</option>{context.locations.map(location => <option key={location.id} value={location.id}>{location.code}</option>)}</CustomSelect></label></div>
              <label className="mt-3 block text-xs">Observaciones de inspección<input aria-label={`Observaciones de ${line.sku}`} required={Number(entry.quantity) > 0 && entry.status !== "accepted"} minLength={entry.status !== "accepted" ? 3 : undefined} maxLength={1000} value={entry.notes} onChange={event => update(line.product_id, { notes: event.target.value })} className="mt-1 w-full rounded-lg border p-2" /></label>
              {line.tracking_mode === "SERIAL" && <label className="mt-3 block text-xs">Series: una por línea, separadas también por coma o punto y coma<textarea aria-label={`Series de ${line.sku}`} rows={3} value={entry.serials} onChange={event => { const values = serials(event.target.value); update(line.product_id, { serials: event.target.value, quantity: values.length ? String(values.length) : entry.quantity }); }} className="mt-1 w-full rounded-lg border p-2 font-mono" /><span>{serials(entry.serials).length} series ingresadas para {entry.quantity || 0} unidades.</span></label>}
              {line.tracking_mode === "LOT" && <div className="mt-3 space-y-2"><button type="button" onClick={() => update(line.product_id, { lots: [...entry.lots, { lot_code: "", quantity: entry.quantity || "", manufacture_date: "", expiration_date: "" }] })} className="inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs"><Plus className="h-3 w-3" />Agregar lote de {line.sku}</button>{entry.lots.map((lot, index) => <div key={index} className="grid gap-2 rounded-lg bg-slate-50 p-2 sm:grid-cols-[minmax(0,1fr)_90px_minmax(0,1fr)_minmax(0,1fr)_auto]">{([['lot_code', 'Código de lote', 'text'], ['quantity', 'Cantidad del lote', 'number'], ['manufacture_date', 'Fabricación', 'date'], ['expiration_date', 'Caducidad', 'date']] as const).map(([field, label, type]) => <label key={field} className="text-xs">{label}<input aria-label={`${label} ${index + 1} de ${line.sku}`} type={type} min={type === "number" ? "0.000001" : undefined} step={type === "number" ? "any" : undefined} value={lot[field]} onInput={type === "date" ? event => updateLot(line.product_id, index, field, event.currentTarget.value) : undefined} onChange={event => updateLot(line.product_id, index, field, event.currentTarget.value)} className="mt-1 min-w-0 w-full rounded border p-2" /></label>)}<button type="button" aria-label={`Quitar lote ${index + 1} de ${line.sku}`} onClick={() => update(line.product_id, { lots: entry.lots.filter((_, row) => row !== index) })}><Trash2 className="h-4 w-4 text-rose-700" /></button></div>)}</div>}
            </article>;
          })}
          <p className="text-xs text-slate-500">Si un mismo artículo requiere resultados de calidad distintos, registra una recepción separada para cada grupo. Las cantidades en blanco no se reciben.</p>
          <div className="grid gap-3 sm:grid-cols-2"><label className="text-xs">Tolerancia adicional (%)<input aria-label="Tolerancia de recepción" type="number" min="0" max="50" step="any" value={tolerance} onChange={event => setTolerance(event.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label><label className="text-xs">Motivo de diferencias<input aria-label="Motivo de diferencias" maxLength={1000} value={difference} onChange={event => setDifference(event.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label></div><label className="block text-xs">Guía, referencia y notas<textarea aria-label="Notas de recepción" maxLength={2000} value={notes} onChange={event => setNotes(event.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label>
          <label className="block text-xs"><span className="inline-flex items-center gap-1"><Paperclip className="h-4 w-4" />Evidencia: PDF, PNG o JPG</span><input aria-label="Adjuntar evidencia de recepción" type="file" accept="application/pdf,image/png,image/jpeg" multiple onChange={event => void upload(event)} className="mt-1 block w-full rounded-lg border p-2" /></label>{uploading && <p role="status">Subiendo y verificando evidencia…</p>}<ul>{attachments.map(item => <li key={item.id} className="flex items-center justify-between gap-2 text-xs"><span>{item.file_name}</span><button type="button" onClick={() => setAttachments(previous => previous.filter(file => file.id !== item.id))}>Quitar adjunto</button></li>)}</ul>
        </fieldset><footer className="flex justify-end gap-2"><button type="button" disabled={busy || uploading} onClick={() => void close()} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy || uploading || !canWrite || !["approved", "submitted", "partially_received"].includes(context.status)} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? "Registrando…" : "Confirmar Recepción"}</button></footer></form>
        <details className="mt-5 rounded-xl border p-3"><summary className="cursor-pointer text-sm font-semibold">Recepciones anteriores ({context.receipts.length})</summary>{context.receipts.map(receipt => <article key={receipt.id} className="mt-3 rounded-lg border p-3 text-xs"><strong>{new Date(receipt.created_at).toLocaleString("es-PE", { timeZone: "America/Lima" })} · {qualityLabel[receipt.status as keyof typeof qualityLabel] || receipt.status}</strong>{receipt.details.inspections?.map(line => <p key={line.product_id} className="mt-1">{line.product_name} · {line.sku} · {line.quantity} · {qualityLabel[line.status as Quality]}{line.resolution === "RESTOCK" ? " · Liberado a stock" : line.resolution === "SCRAP" ? " · Descartado tras inspección" : ""}{line.notes ? ` · ${line.notes}` : ""}{line.lots?.length ? ` · Lotes: ${line.lots.map(lot => lot.lot_code).join(", ")}` : ""}{line.serial_numbers?.length ? ` · Series: ${line.serial_numbers.join(", ")}` : ""}</p>)}{!receipt.details.inspections?.length && receipt.lines.map(line => <p key={line.product_id}>{context.lines.find(item => item.product_id === line.product_id)?.name || "Artículo de la orden"}: {line.quantity}</p>)}{receipt.details.attachments?.map(file => <button key={file.id} type="button" onClick={() => void download(file)} className="mr-3 mt-2 font-semibold text-teal-700 underline">{file.file_name}</button>)}</article>)}{!context.receipts.length && <p className="p-3 text-xs text-slate-500">Esta orden todavía no tiene recepciones.</p>}</details>
      </>}
    </section>{ConfirmDialogNode}
  </ModalSurface>;
}
