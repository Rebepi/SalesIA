import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Version = { quotation_id: string; quotation_number: string; version: number; total_amount: string; currency: string; status: string };
type Comparison = { before_version: number; after_version: number; changes: { field: string; before: string | null; after: string | null }[]; lines: { product_id: string; name: string; change: string; before: Record<string, string> | null; after: Record<string, string> | null }[] };
const labels: Record<string, string> = { currency: "Moneda", valid_until: "Vencimiento", payment_terms_days: "Días de pago", delivery_terms: "Entrega", notes: "Notas", special_conditions: "Condiciones", subtotal_amount: "Subtotal", tax_amount: "Impuesto", total_amount: "Total", quantity: "Cantidad", unit_price: "Precio", discount_pct: "Descuento %", line_subtotal: "Subtotal", line_tax: "Impuesto" };
const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

export function QuotationReviewDialog({ quotationId, canWrite, close, onSaved }: { quotationId: string; canWrite: boolean; close: () => void; onSaved: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [leftId, setLeftId] = useState(quotationId);
  const [rightId, setRightId] = useState("");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [operation, setOperation] = useState("renew");
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  const latest = versions[versions.length - 1];
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.showModal();
    apiClient.request<Version[]>(`/api/v1/quotations/${quotationId}/versions`).then(result => { setVersions(result); setRightId(result[result.length - 1]?.quotation_id || quotationId); setLeftId(result.length > 1 ? result[result.length - 2].quotation_id : quotationId); }).catch(failure => setError(String((failure as { detail?: string }).detail || "No se pudieron cargar las versiones.")));
    return () => previous?.focus();
  }, [quotationId]);
  useEffect(() => {
    if (!leftId || !rightId) return;
    const controller = new AbortController();
    apiClient.request<Comparison>(`/api/v1/quotations/${leftId}/compare/${rightId}`, { signal: controller.signal }).then(setComparison).catch(failure => { if (!controller.signal.aborted) setError(String((failure as { detail?: string }).detail || "No se pudieron comparar las versiones.")); });
    return () => controller.abort();
  }, [leftId, rightId]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!latest || lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const until = String(data.get("valid_until") || "");
    const body = { version: latest.version, action: operation, reason: String(data.get("reason")), keep_prices: data.get("keep_prices") === "on", valid_until: operation === "renew" && until ? new Date(`${until}T23:59:59-05:00`).toISOString() : null };
    const signature = JSON.stringify(body);
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try { await apiClient.request(`/api/v1/quotations/${latest.quotation_id}/review`, { method: "POST", body: JSON.stringify(body), headers: { "Idempotency-Key": key } }); keys.current.delete(signature); onSaved(); close(); }
    catch (failure) { const detail = (failure as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo registrar la revisión."); }
    finally { setBusy(false); lock.current = false; }
  }
  return <dialog ref={dialog} onCancel={event => { event.preventDefault(); if (!busy) close(); }} className="max-h-[90vh] w-[min(96vw,900px)] rounded-2xl bg-white p-5 text-slate-900 shadow-xl backdrop:bg-slate-950/60"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Versiones y negociación · {latest?.quotation_number}</h2><button className={button} disabled={busy} onClick={close}>Cerrar</button></div>{error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}<div className="my-4 grid gap-3 sm:grid-cols-2"><label className="text-sm">Comparar desde<select className={input} value={leftId} onChange={event => setLeftId(event.target.value)}>{versions.map(version => <option value={version.quotation_id} key={version.quotation_id}>Versión {version.version} · {version.status}</option>)}</select></label><label className="text-sm">Hasta<select className={input} value={rightId} onChange={event => setRightId(event.target.value)}>{versions.map(version => <option value={version.quotation_id} key={version.quotation_id}>Versión {version.version} · {version.status}</option>)}</select></label></div>{comparison && <section className="space-y-3 rounded-xl border p-4"><h3 className="font-medium">Cambios entre v{comparison.before_version} y v{comparison.after_version}</h3>{comparison.changes.map(change => <div className="grid gap-2 border-b pb-2 text-sm sm:grid-cols-3" key={change.field}><strong>{labels[change.field] || change.field}</strong><span>{change.before ?? "Sin indicar"}</span><span>{change.after ?? "Sin indicar"}</span></div>)}{comparison.lines.map((line, index) => <div key={`${line.product_id}:${index}`} className="rounded-lg bg-slate-50 p-3 text-sm"><strong>{line.name} · {line.change === "added" ? "Agregado" : line.change === "removed" ? "Retirado" : "Modificado"}</strong>{Object.keys(labels).filter(key => ["quantity", "unit_price", "discount_pct", "line_subtotal", "line_tax"].includes(key) && line.before?.[key] !== line.after?.[key]).map(key => <p key={key}>{labels[key]}: {line.before?.[key] ?? "—"} → {line.after?.[key] ?? "—"}</p>)}</div>)}{!comparison.changes.length && !comparison.lines.length && <p className="text-sm text-slate-500">Sin diferencias comerciales.</p>}</section>}{canWrite && latest && !["converted", "superseded"].includes(latest.status) && <form onSubmit={submit} className="mt-5 space-y-4 border-t pt-4"><h3 className="font-medium">Revisar la última versión</h3><label className="block text-sm">Acción<select className={input} value={operation} onChange={event => setOperation(event.target.value)}><option value="renew">Renovar propuesta</option>{["pending", "draft", "negotiating", "rejected"].includes(latest.status) && <><option value="negotiate">Pasar a negociación</option><option value="reject">Registrar rechazo</option></>}</select></label>{operation === "renew" && <><label className="block text-sm">Nueva fecha de vencimiento<input className={input} type="date" required name="valid_until" /></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" name="keep_prices" defaultChecked />Conservar precios y descuentos de la propuesta</label><p className="text-xs text-slate-500">Si desmarcas esta opción, se recalculan los precios de catálogo. La versión anterior queda reemplazada.</p></>}<label className="block text-sm">Motivo<textarea className={input} required minLength={3} maxLength={2000} name="reason" /></label><button className={button} disabled={busy}>Registrar revisión</button></form>}</dialog>;
}
