import { useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

export type CollectionAgreement = { id: string; version: number; kind: string; currency: string; promised_amount: string; applied_amount: string; remaining_amount: string; paid_on_time: string; status: string; started_at: string; due_at: string; responsible: string; notes: string; legacy: boolean; fulfilled_late: boolean; fulfilled_at: string | null; previous_id?: string; replacement_id?: string; applications: { id: string; amount: string; at: string; reference: string; method: string }[]; history: { action: string; actor: string; at: string; reason?: string; status?: string; applied_amount?: string }[] };
const labels: Record<string, string> = { pending: "Pendiente", partial: "Cumplimiento parcial", broken: "Incumplido", fulfilled: "Cumplido", renegotiated: "Renegociado", cancelled: "Cancelado" };
const input = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

export function CollectionAgreementsPanel({ saleId, currency, balance, agreements, canWrite, onBusyChange, onChanged }: { saleId: string; currency: string; balance: string; agreements: CollectionAgreement[]; canWrite: boolean; onBusyChange: (value: boolean) => void; onChanged: (items: CollectionAgreement[]) => void }) {
  const [editing, setEditing] = useState<string | null>(null);
  const [action, setAction] = useState("renegotiate");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  async function submit(event: FormEvent<HTMLFormElement>, agreement: CollectionAgreement) {
    event.preventDefault();
    if (sending.current) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const body = JSON.stringify({ version: agreement.version, reason: values.reason, promised_amount: action === "renegotiate" ? values.promised_amount : null, due_at: action === "renegotiate" && values.due_at ? new Date(String(values.due_at)).toISOString() : null });
    const signature = `${agreement.id}:${action}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    sending.current = true;
    setBusy(true);
    onBusyChange(true);
    setError("");
    try { const result = await apiClient.request<{ items: CollectionAgreement[] }>(`/api/v1/receivables/${saleId}/agreements/${agreement.id}/${action}`, { method: "POST", headers: { "Idempotency-Key": key }, body }); onChanged(result.items); setEditing(null); }
    catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : "No se pudo actualizar el acuerdo. Vuelve a cargar la deuda si cambió su saldo o versión."); }
    finally { sending.current = false; setBusy(false); onBusyChange(false); }
  }
  return <section className="mb-5 space-y-3 rounded-xl border p-4"><h4 className="font-semibold">Cumplimiento de promesas y acuerdos</h4><p className="text-xs text-slate-500">Se consideran aplicaciones confirmadas de cobros posteriores al acuerdo, con sus reembolsos y reversiones. Los anticipos sin aplicar y las notas de crédito no se cuentan como cumplimiento.</p>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{!agreements.length && <p className="text-sm text-slate-500">No hay compromisos de pago registrados.</p>}{agreements.map(item => <article key={item.id} className="space-y-2 rounded-lg border p-3 text-sm"><div className="flex flex-wrap justify-between gap-2"><strong>{item.kind === "promise" ? "Promesa" : "Acuerdo"} · {labels[item.status] || item.status}{item.fulfilled_late && " · Cumplido fuera de plazo"}</strong><span>Versión {item.version}{item.legacy && " · Registro histórico"}</span></div><p>{item.notes}</p><p>{item.responsible} · Vence {new Date(item.due_at).toLocaleString("es-PE")}</p><dl className="grid gap-2 sm:grid-cols-2"><div><dt>Comprometido</dt><dd>{currency} {item.promised_amount}</dd></div><div><dt>Aplicado al compromiso</dt><dd>{currency} {item.applied_amount}</dd></div><div><dt>Pendiente del compromiso</dt><dd>{currency} {item.remaining_amount}</dd></div><div><dt>Pagado dentro del plazo</dt><dd>{currency} {item.paid_on_time}</dd></div></dl>{item.fulfilled_at && <p>Cumplimiento: {new Date(item.fulfilled_at).toLocaleString("es-PE")}</p>}{item.previous_id && <p className="break-all text-xs text-slate-500">Acuerdo anterior: {item.previous_id}</p>}{item.replacement_id && <p className="break-all text-xs text-slate-500">Acuerdo reemplazante: {item.replacement_id}</p>}
      {canWrite && !["renegotiated", "cancelled"].includes(item.status) && <button type="button" className={button} disabled={busy} onClick={() => { setEditing(editing === item.id ? null : item.id); setAction(item.status === "fulfilled" ? "cancel" : "renegotiate"); }}>Gestionar acuerdo</button>}
      {editing === item.id && <form onSubmit={event => void submit(event, item)} className="grid gap-3 rounded-lg bg-slate-50 p-3"><label className="grid gap-1">Acción<select className={input} value={action} onChange={event => setAction(event.target.value)} disabled={busy}>{item.status !== "fulfilled" && <option value="renegotiate">Renegociar saldo con un nuevo compromiso</option>}<option value="cancel">Cancelar con motivo e historial</option></select></label>{action === "renegotiate" && <><label className="grid gap-1">Nuevo importe {currency}<input className={input} type="number" name="promised_amount" required min="0.000001" max={balance} step="0.000001" defaultValue={Math.min(Number(item.remaining_amount), Number(balance)) || ""} /></label><label className="grid gap-1">Nuevo vencimiento<input className={input} name="due_at" type="datetime-local" required /></label></>}<label className="grid gap-1">Motivo<textarea className={input} name="reason" required minLength={5} maxLength={2000} /></label><p className="text-xs text-slate-500">El registro anterior conservará los cobros evaluados y el motivo del cambio. El nuevo compromiso comenzará desde este momento.</p><button className={button} disabled={busy}>Registrar cambio</button></form>}
      <details><summary className="cursor-pointer text-xs font-medium">Cobros e historial del compromiso</summary><ul className="mt-2 space-y-1 text-xs">{item.applications.map(payment => <li key={payment.id}>{new Date(payment.at).toLocaleString("es-PE")} · {payment.reference} · {payment.method} · {currency} {payment.amount}</li>)}{item.history.map((event, index) => <li key={`${event.at}:${index}`}>{new Date(event.at).toLocaleString("es-PE")} · {event.actor} · {event.reason || labels[event.status || ""] || event.action}{event.applied_amount && ` · ${currency} ${event.applied_amount}`}</li>)}</ul></details>
    </article>)}</section>;
}
