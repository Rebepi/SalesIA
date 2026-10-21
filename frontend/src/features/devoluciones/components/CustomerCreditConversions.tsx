import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Conversion = { id: string; source_currency: string; target_currency: string; source_amount: string; target_amount: string; rate: string; rate_reference: string; reason: string; status: string; expires_at: string; created_by: string; reviewed_by: string | null; review_reason: string | null; source_ids: string[]; debit_id: string | null; credit_id: string | null; version: number; created_at: string };
const field = "w-full rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const labels: Record<string, string> = { pending: "Pendiente de revisión", expired: "Propuesta vencida", approved: "Conversión aplicada", rejected: "Rechazada", cancelled: "Cancelada" };
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo registrar o consultar la conversión de crédito."; }

export function CustomerCreditConversions({ customerId, currency, sourceIds, canWrite, canManage, revision, onChanged }: { customerId: string; currency: string; sourceIds: string[]; canWrite: boolean; canManage: boolean; revision: number; onChanged: () => void }) {
  const [items, setItems] = useState<Conversion[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [actor, setActor] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [localRevision, setLocalRevision] = useState(0);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => {
    const controller = new AbortController();
    void apiClient.request<{ items: Conversion[]; total_count: number; actor_id: string }>(`/api/v1/customers/${customerId}/credit-conversions?limit=10&offset=${page * 10}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) { setItems(result.items); setTotal(result.total_count); setActor(result.actor_id); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [customerId, page, revision, localRevision]);
  async function write(path: string, payload: unknown, message: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try { await apiClient.request<Conversion>(path, { method: "POST", headers: { "Idempotency-Key": key }, body }); keys.current.delete(signature); setNotice(message); setLocalRevision(value => value + 1); onChanged(); }
    catch (cause) { setError(problem(cause)); setLocalRevision(value => value + 1); }
    finally { lock.current = false; setBusy(false); }
  }
  async function propose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await write(`/api/v1/customers/${customerId}/credit-conversions`, { source_currency: currency, target_currency: values.target_currency, source_amount: values.source_amount, rate: values.rate, rate_reference: values.rate_reference, reason: values.reason, source_ids: sourceIds, valid_hours: Number(values.valid_hours) }, "Propuesta registrada. Otra persona autorizada debe revisar los importes y la tasa antes de aplicarla.");
  }
  return <details className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-semibold">Conversión documentada entre monedas ({total})</summary><div className="mt-3 space-y-3"><p className="text-sm text-slate-500">Registre manualmente la tasa acordada y su respaldo. La aprobación descuenta el crédito de origen y crea el crédito de destino en una misma operación, sin movimiento de caja. El destino conserva el vencimiento más próximo de los créditos consumidos. La propuesta no reserva saldo y vuelve a comprobar su disponibilidad al aprobarse.</p>
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    {canWrite && currency && <form className="space-y-3 rounded-lg border p-3" key={`${customerId}:${currency}`} onSubmit={propose}><h3 className="font-semibold">Proponer conversión de crédito {currency}</h3><p className="text-xs text-slate-500">{sourceIds.length ? `${sourceIds.length} créditos elegidos en el libro.` : "Se usarán créditos libres de la moneda de origen, priorizando vencimientos."}</p><div className="grid gap-3 md:grid-cols-3"><label className="grid gap-1 text-sm">Importe de origen {currency}<input className={field} name="source_amount" type="number" required min="0.000001" step="0.000001" disabled={busy} /></label><label className="grid gap-1 text-sm">Moneda de destino<input className={field} name="target_currency" required pattern="[A-Z]{3}" maxLength={3} onInput={event => { event.currentTarget.value = event.currentTarget.value.toUpperCase(); }} disabled={busy} /></label><label className="grid gap-1 text-sm">Unidades de destino por 1 {currency}<input className={field} name="rate" type="number" required min="0.0000000001" step="0.0000000001" disabled={busy} /></label><label className="grid gap-1 text-sm">Documento o referencia de tasa<input className={field} name="rate_reference" required minLength={5} maxLength={255} disabled={busy} /></label><label className="grid gap-1 text-sm">Motivo<input className={field} name="reason" required minLength={5} maxLength={2000} disabled={busy} /></label><label className="grid gap-1 text-sm">Validez de la propuesta en horas<input className={field} name="valid_hours" type="number" defaultValue="24" required min="1" max="168" disabled={busy} /></label></div><p className="text-xs text-slate-500">El importe de destino se calcula con seis decimales y redondeo de mitad hacia arriba. La revisión muestra el valor definitivo antes de aprobar.</p><button className={button} disabled={busy}>Solicitar conversión</button></form>}
    {items.map(row => <article className="space-y-2 rounded-lg border p-3 text-xs" key={row.id}><strong>{row.source_currency} {row.source_amount} → {row.target_currency} {row.target_amount} · {labels[row.status] || row.status}</strong><p>Conversión {row.id} · Tasa {row.rate} {row.target_currency} por {row.source_currency}</p><p>Respaldo de la tasa: {row.rate_reference} · Motivo: {row.reason}</p><p>Solicitada por {row.created_by} · Válida hasta {row.expires_at.slice(0, 19).replace("T", " ")}</p>{row.reviewed_by && <p>Revisada por {row.reviewed_by} · {row.review_reason}</p>}{row.debit_id && <p>Consumo de origen {row.debit_id} · Crédito de destino {row.credit_id}</p>}{row.source_ids.length > 0 && <p>Créditos propuestos: {row.source_ids.join(", ")}</p>}
      {canWrite && row.status === "pending" && <form className="grid gap-2 md:grid-cols-3" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void write(`/api/v1/customer-credit-conversions/${row.id}/review`, { expected_version: row.version, action: values.action, reason: values.reason }, "Revisión registrada con su decisión y movimientos asociados."); }}><select aria-label="Decisión sobre conversión" name="action" className={field} required disabled={busy}><option value="">Seleccione una decisión</option>{actor !== row.created_by && <><option value="approve">Aprobar y aplicar la conversión</option><option value="reject">Rechazar propuesta</option></>}{(actor === row.created_by || canManage) && <option value="cancel">Cancelar propuesta</option>}</select><input aria-label="Motivo de revisión" className={field} name="reason" required minLength={5} maxLength={2000} placeholder="Motivo de la decisión" disabled={busy} /><button className={button} disabled={busy}>Registrar decisión</button></form>}
    </article>)}{items.length === 0 && <p className="text-sm text-slate-500">Sin conversiones registradas.</p>}<div className="flex gap-3 text-sm"><button className={button} disabled={page === 0 || busy} onClick={() => setPage(value => value - 1)}>Anterior</button><span>Página {page + 1} · {total} conversiones</span><button className={button} disabled={(page + 1) * 10 >= total || busy} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>
  </div></details>;
}
