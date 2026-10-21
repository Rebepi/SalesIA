import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";

type Line = { product_id: string; name: string; sku: string; transported_quantity: string; planned_quantity: string; accepted_quantity: string; return_quantity: string; pending_quantity: string; reason: string };
type Result = { window_reservation?: { status: string; requirements: string; checked_in_name: string | null; checked_in_doc: string | null; window: { mode: string; branch_name: string; starts_at: string; ends_at: string }; history: { at: string; actor: string; action: string; reason: string }[] } | null; id: string; version: number; status: string; items: Line[]; tasks: { id: string; title: string; status: string }[]; attempts: { at: string; actor: string; received_by_name: string; notes: string; items: { product_id: string; accepted_quantity: string; rejected_quantity: string; pending_quantity: string; rejected_action?: string; reason?: string }[] }[] };
type Entry = { accepted_quantity: string; rejected_quantity: string; pending_quantity: string; rejected_action: string; reason: string };
const input = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const statuses: Record<string, string> = { ready: "Listo para despacho", delivered: "Entregado", dispatched: "Despachado", in_transit: "En tránsito", out_for_delivery: "En reparto", partially_delivered: "Entrega parcial", pending_redelivery: "Reentrega pendiente", partially_rejected: "Rechazo parcial", rejected: "Rechazado para devolución", cancelled: "Cancelado", incident: "Con incidencia", failed_attempt: "Intento fallido", pending: "Pendiente", done: "Completada", in_progress: "En curso" };

export function DeliveryResultsDialog({ deliveryId, canWrite, onClose, onChanged }: { deliveryId: string; canWrite: boolean; onClose: () => void; onChanged: () => void }) {
  const [data, setData] = useState<Result | null>(null);
  const [entries, setEntries] = useState<Record<string, Entry>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const loadVersion = useRef(0);
  function hydrate(result: Result) { setData(result); setEntries(Object.fromEntries(result.items.map(item => [item.product_id, { accepted_quantity: "0", rejected_quantity: "0", pending_quantity: item.pending_quantity, rejected_action: "redelivery", reason: item.reason }]))); }
  function problem(cause: unknown) { const detail = (cause as { detail?: unknown }).detail; return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo registrar el resultado."; }
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    void apiClient.request<Result>(`/api/v1/deliveries/${deliveryId}/results`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) hydrate(result); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => { controller.abort(); loadVersion.current += 1; };
  }, [deliveryId]);

  function change(productId: string, field: keyof Entry, value: string) { setEntries(previous => ({ ...previous, [productId]: { ...previous[productId], [field]: value } })); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!data || sending.current) return;
    const invalid = data.items.find(item => { const entry = entries[item.product_id]; return Math.abs(Number(entry.accepted_quantity) + Number(entry.rejected_quantity) + Number(entry.pending_quantity) - Number(item.pending_quantity)) > 0.0000001; });
    if (invalid) { setError(`Distribuye exactamente el saldo pendiente de ${invalid.name}: ${invalid.pending_quantity}.`); return; }
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    const body = JSON.stringify({ ...fields, version: data.version, items: data.items.map(item => ({ product_id: item.product_id, ...entries[item.product_id] })) });
    const key = keys.current.get(body) || crypto.randomUUID();
    keys.current.set(body, key);
    const version = ++loadVersion.current;
    sending.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await apiClient.request<Result>(`/api/v1/deliveries/${deliveryId}/results`, { method: "POST", headers: { "Idempotency-Key": key }, body });
      if (version !== loadVersion.current) return;
      hydrate(result);
      setNotice("Resultado registrado; las cantidades pendientes y rechazadas tienen tareas de seguimiento.");
      onChanged();
    } catch (cause) { if (version === loadVersion.current) setError(problem(cause)); }
    finally { sending.current = false; if (version === loadVersion.current) setBusy(false); }
  }

  const editable = canWrite && data && ["dispatched", "in_transit", "out_for_delivery", "incident", "failed_attempt", "partially_delivered", "pending_redelivery"].includes(data.status);
  return <ModalSurface labelledBy="delivery-result-title" blocked={busy} onClose={onClose}><div className="app-modal-panel max-h-[90vh] w-full max-w-5xl space-y-4 overflow-y-auto rounded-2xl bg-white p-5"><div className="flex items-center justify-between gap-2"><h2 id="delivery-result-title" className="font-semibold">Resultado por producto · {deliveryId.substring(0, 8).toUpperCase()}</h2><button type="button" className={button} disabled={busy} onClick={onClose}>Cerrar</button></div>{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{!data && !error && <p role="status" className="text-sm">Cargando cantidades y antecedentes…</p>}{data && <><p className="text-sm">{statuses[data.status] || data.status} · Versión {data.version}</p>{data.window_reservation && <div className="rounded-lg bg-slate-50 p-3 text-sm"><strong>{data.window_reservation.window.mode === "pickup" ? "Retiro en local" : "Entrega con reserva"} · {data.window_reservation.window.branch_name}</strong><p>{new Date(data.window_reservation.window.starts_at).toLocaleString("es-PE")} – {new Date(data.window_reservation.window.ends_at).toLocaleString("es-PE")}</p><p>Requisitos: {data.window_reservation.requirements || "Sin requisitos adicionales"}</p><p>Persona verificada: {data.window_reservation.checked_in_name || "Atención pendiente"} · {data.window_reservation.checked_in_doc || ""}</p><details><summary className="cursor-pointer">Historial de atención</summary>{data.window_reservation.history.map((event, index) => <p key={`${event.at}:${index}`}>{new Date(event.at).toLocaleString("es-PE")} · {event.actor} · {event.reason}</p>)}</details></div>}<div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Producto", "Transportado", "Aceptado", "Rechazado para devolución", "Pendiente de reentrega"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{data.items.map(item => <tr className="border-t" key={item.product_id}><td className="p-2">{item.name} · {item.sku}</td><td className="p-2">{item.transported_quantity}</td><td className="p-2">{item.accepted_quantity}</td><td className="p-2">{item.return_quantity}</td><td className="p-2">{item.pending_quantity}</td></tr>)}</tbody></table></div>
      {editable && <form className="space-y-3" onSubmit={submit}><h3 className="font-medium">Registrar nuevo intento</h3><p className="text-sm text-slate-500">Reparte solo el saldo pendiente. Las cantidades ya aceptadas se conservan. El rechazo para devolución genera una tarea; su recepción física y ajuste comercial se resuelven por separado.</p>{data.items.filter(item => Number(item.pending_quantity) > 0).map(item => { const entry = entries[item.product_id]; return <fieldset key={item.product_id} className="space-y-3 rounded-lg border p-3" disabled={busy}><legend className="px-1 text-sm font-medium">{item.name} · Saldo {item.pending_quantity}</legend><div className="grid gap-2 sm:grid-cols-3">{([ ["accepted_quantity", "Aceptado en este intento"], ["rejected_quantity", "Rechazado en este intento"], ["pending_quantity", "Sin resolver en este intento"] ] as const).map(([field, label]) => <label key={field} className="grid gap-1 text-sm">{label}<input className={input} type="number" required min="0" max={item.pending_quantity} step="0.000001" value={entry[field]} onChange={event => change(item.product_id, field, event.target.value)} /></label>)}</div><label className="grid gap-1 text-sm">Tratamiento de las unidades rechazadas<select className={input} value={entry.rejected_action} onChange={event => change(item.product_id, "rejected_action", event.target.value)}><option value="redelivery">Conservar para reentrega</option><option value="return">Derivar a devolución física y comercial</option></select></label><label className="grid gap-1 text-sm">Motivo del rechazo o pendiente<textarea className={input} required={Number(entry.rejected_quantity) > 0 || Number(entry.pending_quantity) > 0} minLength={5} maxLength={2000} value={entry.reason} onChange={event => change(item.product_id, "reason", event.target.value)} /></label><button type="button" className={button} onClick={() => setEntries(previous => ({ ...previous, [item.product_id]: { ...previous[item.product_id], accepted_quantity: item.pending_quantity, rejected_quantity: "0", pending_quantity: "0" } }))}>Aceptar todo el saldo de este producto</button></fieldset>; })}<label className="grid gap-1 text-sm">Destinatario o contacto del intento<input className={input} name="received_by_name" required minLength={2} maxLength={255} /></label><label className="grid gap-1 text-sm">Documento del destinatario o contacto (obligatorio si tiene reserva con identificación)<input className={input} name="received_by_id_doc" maxLength={64} /></label><label className="grid gap-1 text-sm">Motivo de aceptación fuera del horario reservado, si corresponde<input className={input} name="outside_window_reason" maxLength={2000} /></label><label className="grid gap-1 text-sm">Sustento del resultado<textarea className={input} name="notes" required minLength={5} maxLength={4000} /></label><button className={button} disabled={busy}>Registrar resultado y tareas</button></form>}
      {!!data.tasks.length && <div><h3 className="font-medium">Tareas de seguimiento</h3><ul className="space-y-1 text-sm">{data.tasks.map(item => <li key={item.id}>{item.title} · {statuses[item.status] || item.status}</li>)}</ul></div>}<details><summary className="cursor-pointer text-sm font-medium">Historial de intentos</summary><ul className="mt-3 space-y-3 text-sm">{data.attempts.map((attempt, index) => <li key={`${attempt.at}:${index}`} className="rounded-lg border p-3">{new Date(attempt.at).toLocaleString("es-PE")} · {attempt.actor} · Contacto: {attempt.received_by_name}<p>{attempt.notes}</p><ul className="mt-2 text-xs">{attempt.items.map(item => <li key={item.product_id}>{data.items.find(line => line.product_id === item.product_id)?.name || "Producto histórico"} · Aceptado {item.accepted_quantity} · Rechazado {item.rejected_quantity} · Pendiente {item.pending_quantity}{item.rejected_action && ` · ${item.rejected_action === "return" ? "Devolución" : "Reentrega"}`}<p>{item.reason}</p></li>)}</ul></li>)}</ul></details>
    </>}</div></ModalSurface>;
}
