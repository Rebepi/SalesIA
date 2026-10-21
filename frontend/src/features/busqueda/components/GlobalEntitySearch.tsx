import { useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import { apiClient, SearchResultItem } from "../../../api/client";
import { readDraft, writeDraft } from "../../../ui/drafts";

const labels: Record<SearchResultItem["type"], string> = { customer: "Cliente", product: "Producto", sale: "Venta o comprobante", order: "Pedido", task: "Tarea", quotation: "Cotización", supplier: "Proveedor", purchase_order: "Compra", delivery: "Entrega", return: "Devolución", credit_note: "Nota de crédito", payment: "Cobro", payable: "Obligación", expense: "Gasto", lot: "Lote", serial: "Serie", branch: "Sede", warehouse: "Almacén", warranty: "Garantía", supplier_claim: "Reclamo de proveedor", delivery_route: "Recorrido", delivery_vehicle: "Vehículo", delivery_window: "Franja de entrega o retiro" };

export function GlobalEntitySearch({ open, onClose, onSelect }: { open: boolean; onClose: () => void; onSelect: (item: SearchResultItem) => Promise<void> }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [recent, setRecent] = useState<SearchResultItem[]>(() => readDraft("salesia_recent_entities", { items: [] as SearchResultItem[] }).items);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(0);
  useEffect(() => {
    if (open) { dialog.current?.showModal(); input.current?.focus(); setRecent(readDraft("salesia_recent_entities", { items: [] as SearchResultItem[] }).items); }
    else dialog.current?.close();
  }, [open]);
  useEffect(() => {
    if (!open || query.trim().length < 2) { setResults([]); setLoading(false); return; }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timer = window.setTimeout(async () => {
      try { const response = await apiClient.request<{ results: SearchResultItem[] }>(`/api/v1/search?q=${encodeURIComponent(query.trim())}`, { signal: controller.signal }); if (!controller.signal.aborted) { setResults(response.results || []); setSelected(0); } }
      catch (failure: unknown) { if (!controller.signal.aborted) setError(String((failure as { detail?: string }).detail || "No se pudo buscar. Revisa la conexión e intenta nuevamente.")); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, open]);
  const items = query.trim().length >= 2 ? results : recent;
  async function select(item: SearchResultItem) {
    setBusy(true);
    setError("");
    try {
      await onSelect(item);
      const next = [item, ...recent.filter(previous => previous.id !== item.id || previous.type !== item.type)].slice(0, 20);
      setRecent(next);
      writeDraft("salesia_recent_entities", { items: next });
      setQuery("");
      onClose();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "El registro ya no está disponible o tu usuario no tiene acceso.")); }
    finally { setBusy(false); }
  }
  return <dialog ref={dialog} onCancel={onClose} aria-labelledby="global-search-title" className="app-modal-panel max-h-[85vh] w-[min(95vw,720px)] rounded-2xl border-0 bg-white p-0 shadow-2xl backdrop:bg-slate-950/60 dark:bg-slate-900"><header className="flex items-center justify-between border-b p-4"><h2 id="global-search-title" className="font-bold">Buscar en el sistema</h2><button type="button" aria-label="Cerrar búsqueda" onClick={onClose}><X className="h-5 w-5" /></button></header><div className="p-4"><div className="flex items-center gap-2 rounded-xl border px-3"><Search className="h-4 w-4 text-slate-500" /><input ref={input} aria-label="Buscar registros en todos los módulos" value={query} onChange={event => { setQuery(event.target.value); setSelected(0); }} onKeyDown={event => { if (event.key === "ArrowDown") { event.preventDefault(); setSelected(value => Math.min(value + 1, items.length - 1)); } if (event.key === "ArrowUp") { event.preventDefault(); setSelected(value => Math.max(0, value - 1)); } if (event.key === "Enter" && items[selected] && !busy) { event.preventDefault(); void select(items[selected]); } }} className="w-full bg-transparent py-3 text-sm outline-none" placeholder="Nombre, SKU, documento o número de pedido" /></div><p className="mt-2 text-xs text-slate-500">Ctrl + K para abrir · ↑ ↓ para elegir · Enter para abrir · Escape para cerrar</p>{error && <p role="alert" className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<div aria-live="polite" className="mt-3 text-xs text-slate-500">{loading ? "Buscando…" : query.trim().length >= 2 ? `${items.length} resultados autorizados` : "Abiertos recientemente"}</div><div className="mt-2 max-h-[50vh] space-y-1 overflow-y-auto">{items.map((item, index) => <button key={`${item.type}-${item.id}`} type="button" disabled={busy} onClick={() => select(item)} onFocus={() => setSelected(index)} className={`block w-full rounded-xl p-3 text-left text-sm disabled:opacity-50 ${selected === index ? "bg-teal-50 text-teal-900 dark:bg-teal-950" : "hover:bg-slate-50 dark:hover:bg-slate-800"}`}><span className="text-[10px] uppercase text-slate-500">{labels[item.type]}</span><strong className="block">{item.title}</strong><span className="text-xs text-slate-500">{item.subtitle}</span></button>)}{!loading && !items.length && <p className="p-6 text-center text-sm text-slate-500">{query.trim().length >= 2 ? "No hay coincidencias. Prueba otro nombre o código y verifica tus permisos." : "Los registros que abras aparecerán aquí."}</p>}</div></div></dialog>;
}
