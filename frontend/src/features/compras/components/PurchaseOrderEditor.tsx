import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { clearDraft, readDraft, useUnsavedChanges, writeDraft } from "../../../ui/drafts";
import { useToast } from "../../../ui/toast/ToastContext";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { QuickProductDialog } from "../../catalogo/components/QuickProductDialog";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

interface Product extends Record<string, unknown> { id: string; sku: string; name: string; unit_cost: string; tax_rate?: string }
interface Supplier extends Record<string, unknown> { id: string; legal_name: string; tax_id: string; currency: string; payment_terms_days: number }
interface Line { product: Product; quantity: string; unit_cost: string; discount_percentage: string; tax_rate: string }
interface SupplierCondition { unit_cost: string; minimum_quantity: string; order_multiple: string; lead_time_days: number; supplier_sku: string; currency: string }
interface History { order_id: string; created_at: string; currency: string; unit_cost: string; quantity: string }
export interface PurchaseEditorSource {
  id?: string;
  version?: number;
  warehouse_id: string;
  currency?: string;
  supplier_id?: string;
  lines: { product_id: string; quantity: string; unit_cost: string }[];
}
const draftKey = "salesia_purchase_editor_v3";
const empty = { supplier: undefined as Supplier | undefined, warehouse: "", lines: [] as Line[], currency: "", terms: 30, delivery: "", notes: "", justification: "", priority: "MEDIUM" };

export function PurchaseOrderEditor({ isOpen, mode, source, warehouses, companyCurrency, defaultTaxRate, onCreateSupplier, onClose, onSaved }: {
  isOpen: boolean;
  mode: "order" | "requisition";
  source?: PurchaseEditorSource;
  warehouses: { warehouse_id: string; name: string; code: string }[];
  companyCurrency: string;
  defaultTaxRate: string;
  onCreateSupplier: () => void;
  onClose: () => void;
  onSaved: () => void;
}) {
  const initial = useMemo(() => readDraft(draftKey, empty), []);
  const [form, setForm] = useState(initial);
  const [choice, setChoice] = useState<Product>();
  const [quantity, setQuantity] = useState("1");
  const [cost, setCost] = useState("");
  const [history, setHistory] = useState<History[]>([]);
  const [condition, setCondition] = useState<SupplierCondition | null>(null);
  const [historyError, setHistoryError] = useState("");
  const [busy, setBusy] = useState(false);
  const [hydrating, setHydrating] = useState(false);
  const [sourceReady, setSourceReady] = useState(!source);
  const previousSource = useRef(false);
  const [error, setError] = useState("");
  const [productOpen, setProductOpen] = useState(false);
  const { confirm, ConfirmDialogNode } = useConfirm();
  const key = useRef(crypto.randomUUID());
  const toast = useToast();
  const dirty = form.lines.length > 0 || Boolean(form.supplier || form.notes || choice);
  useUnsavedChanges(isOpen && dirty);

  useEffect(() => {
    if (!isOpen) return;
    setError("");
    key.current = crypto.randomUUID();
    setHydrating(false);
    if (!source) {
      setSourceReady(true);
      if (previousSource.current) setForm(readDraft(draftKey, empty));
      previousSource.current = false;
      return;
    }
    previousSource.current = true;
    setSourceReady(false);
    let active = true;
    setHydrating(true);
    Promise.all([
      Promise.all(source.lines.map(async line => {
        const product = await apiClient.request<Product>(`/api/v1/products/${line.product_id}`);
        return { product, quantity: line.quantity, unit_cost: line.unit_cost, discount_percentage: "0", tax_rate: product.tax_rate ?? defaultTaxRate };
      })),
      source.supplier_id ? apiClient.request<Supplier>(`/api/v1/suppliers/${source.supplier_id}`) : Promise.resolve(undefined)
    ]).then(([lines, supplier]) => {
      if (active) {
        setForm({ ...empty, lines, supplier, warehouse: source.warehouse_id, currency: source.currency || supplier?.currency || companyCurrency, terms: supplier?.payment_terms_days ?? 30 });
        setSourceReady(true);
      }
    }).catch(() => { if (active) setError("No se pudo cargar el origen. Cierra y vuelve a intentar; no se ha creado ningún documento."); }).finally(() => { if (active) setHydrating(false); });
    return () => { active = false; };
  }, [isOpen, source]);

  useEffect(() => {
    if (!isOpen || source || hydrating) return;
    writeDraft(draftKey, form);
  }, [form, isOpen, source, hydrating]);

  useEffect(() => {
    setHistory([]);
    setCondition(null);
    setHistoryError("");
    if (!choice || !form.supplier) return;
    const controller = new AbortController();
    apiClient.request<{ items: History[] }>(`/api/v1/suppliers/${form.supplier.id}/price-history?product_id=${choice.id}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setHistory(result.items || []); }).catch(error => { if (!controller.signal.aborted) setHistoryError(error?.detail || "No se pudo consultar el historial del proveedor."); });
    apiClient.request<{ items: SupplierCondition[] }>(`/api/v1/supplier-products?supplier_id=${form.supplier.id}&product_id=${choice.id}&currency=${encodeURIComponent(form.currency || companyCurrency)}&current_only=true`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setCondition(result.items[0] || null); }).catch(() => { if (!controller.signal.aborted) setCondition(null); });
    return () => controller.abort();
  }, [choice?.id, form.supplier?.id, form.currency, companyCurrency]);

  function addLine() {
    if (!choice || !Number.isFinite(Number(quantity)) || Number(quantity) <= 0 || !Number.isFinite(Number(cost || choice.unit_cost)) || Number(cost || choice.unit_cost) < 0) { setError("Selecciona un producto y una cantidad positiva con costo válido."); return; }
    if (form.lines.some(line => line.product.id === choice.id)) { setError("El producto ya está agregado. Modifica la cantidad en su línea."); return; }
    setForm(previous => ({ ...previous, lines: [...previous.lines, { product: choice, quantity, unit_cost: cost || choice.unit_cost, discount_percentage: "0", tax_rate: choice.tax_rate ?? defaultTaxRate }] }));
    setChoice(undefined);
    setQuantity("1");
    setCost("");
    setError("");
  }

  function changeLine(index: number, field: keyof Omit<Line, "product">, value: string) {
    setForm(previous => ({ ...previous, lines: previous.lines.map((line, row) => row === index ? { ...line, [field]: value } : line) }));
  }

  async function close() {
    if (busy) return;
    if (dirty && !await confirm({ title: "¿Cerrar la compra?", text: source ? "Se cerrará la preparación del documento. El origen conserva su estado." : "El borrador se conservará para continuar después.", confirmLabel: "Cerrar" })) return;
    onClose();
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || hydrating || !sourceReady) return;
    if (!form.lines.length || !form.warehouse || (mode === "order" && !form.supplier)) { setError("Selecciona almacén, agrega al menos una línea y elige proveedor para la orden."); return; }
    if (!await confirm({ title: mode === "order" ? "¿Crear orden de compra?" : "¿Crear requisición?", text: `Se enviarán ${form.lines.length} líneas para aprobación. ${source?.id ? "La requisición quedará vinculada y no podrá convertirse otra vez." : "El inventario se actualizará al recibir la compra."}`, confirmLabel: "Crear documento" })) return;
    setBusy(true);
    setError("");
    const items = form.lines.map(line => ({ product_id: line.product.id, quantity: line.quantity, unit_cost: line.unit_cost, discount_percentage: line.discount_percentage, tax_rate: line.tax_rate }));
    try {
      await apiClient.request(mode === "order" ? "/api/v1/purchase-orders" : "/api/v1/purchases/requisitions", { method: "POST", headers: { "Idempotency-Key": key.current }, body: JSON.stringify(mode === "order" ? { supplier_id: form.supplier!.id, warehouse_id: form.warehouse, currency: form.currency || companyCurrency, payment_terms_days: form.terms, delivery_date: form.delivery ? `${form.delivery}T12:00:00-05:00` : null, notes: form.notes || null, source_requisition_id: source?.id || null, source_version: source?.version || null, items } : { warehouse_id: form.warehouse, suggested_supplier_id: form.supplier?.id || null, justification: form.justification, priority: form.priority, items }) });
      clearDraft(draftKey);
      setForm(empty);
      toast.success(mode === "order" ? "Orden creada" : "Requisición creada", "El documento conserva sus líneas y espera aprobación.");
      onSaved();
    } catch (requestError: unknown) {
      setError(requestError && typeof requestError === "object" && "detail" in requestError ? String(requestError.detail) : "No se pudo guardar. Revisa los datos y reintenta.");
    } finally { setBusy(false); }
  }

  if (!isOpen) return null;
  const currency = form.currency || companyCurrency;
  const money = (value: number) => new Intl.NumberFormat("es-PE", { style: "currency", currency: /^[A-Z]{3}$/.test(currency) ? currency : "PEN" }).format(value);
  const subtotal = form.lines.reduce((sum, line) => sum + Number(line.quantity) * Number(line.unit_cost) * (1 - Number(line.discount_percentage) / 100), 0);
  const tax = form.lines.reduce((sum, line) => sum + Number(line.quantity) * Number(line.unit_cost) * (1 - Number(line.discount_percentage) / 100) * Number(line.tax_rate), 0);
  const locked = Boolean(source?.id);
  return <ModalSurface labelledBy="purchase-editor-title" onClose={() => void close()} blocked={busy}>
    <section className="app-modal-panel w-[min(940px,94vw)] rounded-2xl bg-white p-5">
      <header className="flex items-center justify-between gap-3"><div><h2 id="purchase-editor-title" className="text-lg font-bold">{mode === "order" ? "Crear Orden de Compra" : "Crear requisición de compra"}</h2><p className="text-xs text-slate-500">{locked ? "Conversión de requisición aprobada con referencia de origen" : "Productos, condiciones y revisión antes de enviar"}</p></div><button type="button" disabled={busy} aria-label="Cerrar compra" onClick={() => void close()}><X className="h-5 w-5" /></button></header>
      <form onSubmit={submit} className="mt-4 space-y-4">
        {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        {hydrating && <p role="status">Cargando productos del documento de origen…</p>}
        <fieldset disabled={busy || hydrating || !sourceReady} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <RemoteEntitySelect<Supplier> value={form.supplier?.id || ""} initialOption={form.supplier ? { value: form.supplier.id, label: form.supplier.legal_name, description: form.supplier.tax_id, data: form.supplier } : undefined} onChange={(_, option) => setForm(previous => ({ ...previous, supplier: option?.data, currency: option?.data.currency || previous.currency, terms: option?.data.payment_terms_days ?? previous.terms }))} endpoint="/api/v1/suppliers" entityType="supplier" mapOption={item => ({ value: item.id, label: item.legal_name, description: `${item.tax_id} · ${item.currency}`, data: item })} label={mode === "order" ? "Proveedor" : "Proveedor sugerido (opcional)"} onCreate={onCreateSupplier} />
            <label className="text-xs font-semibold">Almacén destino<CustomSelect remote={{ resource: "warehouses" }} value={form.warehouse} required disabled={locked} onChange={event => setForm(previous => ({ ...previous, warehouse: event.target.value }))} className="mt-1 w-full"><option value="">Seleccionar almacén</option>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.name} ({item.code})</option>)}</CustomSelect></label>
          </div>
          {!locked && <div className="rounded-xl border border-slate-200 p-3"><div className="grid items-end gap-3 sm:grid-cols-[minmax(0,1fr)_100px_110px_auto]"><RemoteEntitySelect<Product> value={choice?.id || ""} initialOption={choice ? { value: choice.id, label: choice.name, description: choice.sku, data: choice } : undefined} onChange={(_, option) => { setChoice(option?.data); setCost(""); }} endpoint="/api/v1/products" entityType="product" mapOption={item => ({ value: item.id, label: item.name, description: item.sku, data: item })} label="Producto" onCreate={() => setProductOpen(true)} createLabel="Crear producto" /><label className="text-xs">Cantidad<input aria-label="Cantidad a agregar" type="number" min="0.000001" step="any" value={quantity} onChange={event => setQuantity(event.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label><label className="text-xs">Costo de lista<input aria-label="Costo a agregar" type="number" min="0" step="any" value={cost || choice?.unit_cost || ""} onChange={event => setCost(event.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label><button type="button" onClick={addLine} disabled={!choice} className="flex items-center gap-1 rounded-xl bg-teal-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"><Plus className="h-4 w-4" />Agregar línea</button></div>{condition && <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg bg-teal-50 p-3 text-xs text-teal-900"><span>Condición vigente: {condition.currency} {condition.unit_cost} · mínimo {condition.minimum_quantity} · múltiplo {condition.order_multiple} · {condition.lead_time_days} días · código {condition.supplier_sku || "sin código"}</span><button type="button" onClick={() => { setCost(condition.unit_cost); const minimum = Math.max(Number(quantity) || 0, Number(condition.minimum_quantity)); const multiple = Number(condition.order_multiple); setQuantity(String(Math.ceil(minimum / multiple) * multiple)); }} className="rounded border border-teal-300 bg-white px-2 py-1">Aplicar costo y múltiplo</button></div>}{historyError && <p className="mt-2 text-xs text-amber-800">{historyError}</p>}{choice && form.supplier && <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">{history.length ? history.map(item => <button key={item.order_id} type="button" disabled={item.currency !== currency} title={item.currency !== currency ? "Selecciona la misma moneda para usar este precio" : "Usar costo neto histórico; descuento adicional en cero"} onClick={() => setCost(item.unit_cost)} className="rounded-lg border p-2">{new Date(item.created_at).toLocaleDateString("es-PE")} · {item.currency} {item.unit_cost}</button>) : "Sin compras aprobadas previas para este producto y proveedor."}</div>}</div>}
          <div className="overflow-x-auto rounded-xl border border-slate-200"><table className="w-full text-left text-xs"><thead className="bg-slate-50"><tr><th className="p-2">Producto / SKU</th><th className="p-2">Cantidad</th><th className="p-2">Costo de lista</th>{mode === "order" && <><th className="p-2">Desc. %</th><th className="p-2">Impuesto %</th></>}<th className="p-2">Acción</th></tr></thead><tbody>{form.lines.map((line, index) => <tr key={line.product.id}><td className="p-2"><strong>{line.product.name}</strong><span className="block text-slate-500">{line.product.sku}</span></td><td className="p-2"><input aria-label={`Cantidad de ${line.product.sku}`} type="number" required disabled={locked} min="0.000001" step="any" value={line.quantity} onChange={event => changeLine(index, "quantity", event.target.value)} className="w-24 rounded border p-2" /></td><td className="p-2"><input aria-label={`Costo de ${line.product.sku}`} type="number" required min="0" step="any" value={line.unit_cost} onChange={event => changeLine(index, "unit_cost", event.target.value)} className="w-24 rounded border p-2" /></td>{mode === "order" && <><td className="p-2"><input aria-label={`Descuento de ${line.product.sku}`} type="number" required min="0" max="100" step="any" value={line.discount_percentage} onChange={event => changeLine(index, "discount_percentage", event.target.value)} className="w-20 rounded border p-2" /></td><td className="p-2"><input aria-label={`Impuesto de ${line.product.sku}`} type="number" required min="0" max="100" step="any" value={Number(line.tax_rate) * 100} onChange={event => changeLine(index, "tax_rate", String(Number(event.target.value) / 100))} className="w-20 rounded border p-2" /></td></>}<td className="p-2"><button type="button" disabled={locked} aria-label={`Quitar ${line.product.sku}`} onClick={() => setForm(previous => ({ ...previous, lines: previous.lines.filter((_, row) => row !== index) }))}><Trash2 className="h-4 w-4 text-rose-700" /></button></td></tr>)}{!form.lines.length && <tr><td colSpan={6} className="p-6 text-center text-slate-500">Agrega productos para preparar el documento.</td></tr>}</tbody></table></div>
          {mode === "order" ? <><div className="grid gap-3 sm:grid-cols-3"><label className="text-xs">Moneda<input aria-label="Moneda de compra" required pattern="[A-Z]{3}" maxLength={3} value={currency} onChange={event => setForm(previous => ({ ...previous, currency: event.target.value.toUpperCase() }))} className="mt-1 w-full rounded-lg border p-2" /></label><label className="text-xs">Pago a días<input type="number" required min="0" max="365" value={form.terms} onChange={event => setForm(previous => ({ ...previous, terms: Number(event.target.value) }))} className="mt-1 w-full rounded-lg border p-2" /></label><label className="text-xs">Entrega estimada<input type="date" value={form.delivery} onChange={event => setForm(previous => ({ ...previous, delivery: event.target.value }))} className="mt-1 w-full rounded-lg border p-2" /></label></div><label className="block text-xs">Notas y condiciones<textarea maxLength={1000} value={form.notes} onChange={event => setForm(previous => ({ ...previous, notes: event.target.value }))} className="mt-1 w-full rounded-lg border p-2" /></label><p className="text-right text-sm">Subtotal {money(subtotal)} · Impuestos {money(tax)} · <strong>Total {money(subtotal + tax)}</strong></p></> : <><label className="block text-xs">Justificación<textarea required minLength={3} maxLength={500} value={form.justification} onChange={event => setForm(previous => ({ ...previous, justification: event.target.value }))} className="mt-1 w-full rounded-lg border p-2" /></label><label className="block text-xs">Prioridad<CustomSelect value={form.priority} onChange={event => setForm(previous => ({ ...previous, priority: event.target.value }))}><option value="LOW">Baja</option><option value="MEDIUM">Media</option><option value="HIGH">Alta</option><option value="URGENT">Urgente</option></CustomSelect></label></>}
        </fieldset>
        <footer className="flex justify-end gap-2"><button type="button" disabled={busy} onClick={() => void close()} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy || hydrating || !sourceReady || !form.lines.length} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy ? "Guardando…" : mode === "order" ? "Crear Orden" : "Crear requisición"}</button></footer>
      </form>
    </section>
    <QuickProductDialog isOpen={productOpen} currency={currency} defaultTaxRate={defaultTaxRate} onClose={() => setProductOpen(false)} onCreated={item => { setChoice(item as Product); setProductOpen(false); }} />
    {ConfirmDialogNode}
  </ModalSurface>;
}
