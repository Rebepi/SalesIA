import { IconAction } from "../../../ui/components/primitives/IconAction";
import "./cash-submodules.css";
import { ArrowLeftRight, RefreshCw, Plus, Settings2, Eye } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Point = { kind: "cash_session" | "custody_account"; id: string; label: string; branch_id: string; responsible_id: string; responsible_name: string; currency: string; balance: string };
type Account = { id: string; code: string; name: string; kind: string; currency: string; branch_id: string; branch_name: string; responsible_id: string; responsible_name: string; balance: string; version: number; is_active: boolean; movements: { movement_id: string; movement_type: string; amount_delta: string; balance_after: string; reason: string; timestamp: string }[] };
type Transfer = { id: string; code: string; currency: string; amount: string; source: Point; destination: Point; sender_id: string; sender_name: string; receiver_id: string; receiver_name: string; status: string; version: number; reason: string; reference: string; created_at: string; received_at: string | null; returned_at: string | null; history: { action: string; reason: string; actor: string; at: string; counted_amount: string | null }[] };
type Options = { accounts: Account[]; endpoints: Point[]; people: { id: string; name: string }[]; branches: { id: string; name: string }[]; current_user_id: string; can_configure: boolean; base_currency: string };
const statuses: Record<string, string> = { sent: "Pendiente de recepción", disputed: "Diferencia de conteo", return_pending: "Retorno pendiente", received: "Recibido", returned: "Devuelto al origen" };
const actions: Record<string, string> = { receive: "Confirmar recepción física", reject: "Rechazar y solicitar retorno", report_difference: "Registrar diferencia de conteo", recall: "Solicitar retorno al origen", confirm_return: "Confirmar retorno físico" };
const historyLabels: Record<string, string> = { SEND: "Entrega registrada", RECEIVE: "Recepción confirmada", REJECT: "Entrega rechazada", REPORT_DIFFERENCE: "Diferencia registrada", RECALL: "Retorno solicitado", CONFIRM_RETURN: "Retorno confirmado" };
const accountKinds: Record<string, string> = { safe: "Caja fuerte", treasury: "Tesorería", branch_fund: "Fondo de sede" };
const input = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const pointKey = (point: Point) => `${point.kind}:${point.id}`;
function problem(cause: unknown) { const detail = (cause as { detail?: unknown }).detail; return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo completar la operación de custodia."; }

export function CashCustodyPanel({ canWrite, revision, onChanged }: { canWrite: boolean; revision: number; onChanged: () => void }) {
  const [options, setOptions] = useState<Options>({ accounts: [], endpoints: [], people: [], branches: [], current_user_id: "", can_configure: false, base_currency: "" });
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [total, setTotal] = useState(0);
  const [inTransit, setInTransit] = useState<Record<string, string>>({});
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("");
  const [currency, setCurrency] = useState("");
  const [localRevision, setLocalRevision] = useState(0);
  const [creating, setCreating] = useState(false);
  const [accountEdit, setAccountEdit] = useState<Account | "new" | null>(null);
  const [sourceKey, setSourceKey] = useState("");
  const [destinationKey, setDestinationKey] = useState("");
  const [detail, setDetail] = useState<Transfer | null>(null);
  const [action, setAction] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const detailVersion = useRef(0);
  const source = options.endpoints.find(point => pointKey(point) === sourceKey);
  const destination = options.endpoints.find(point => pointKey(point) === destinationKey);
  const accountValue = accountEdit && accountEdit !== "new" ? accountEdit : null;

  useEffect(() => {
    const controller = new AbortController();
    const query = new URLSearchParams({ limit: "10", offset: String(page * 10) });
    if (status) query.set("status", status);
    if (currency) query.set("currency", currency);
    void Promise.all([apiClient.request<Options>("/api/v1/cash-custody/options", { signal: controller.signal }), apiClient.request<{ items: Transfer[]; total_count: number; in_transit_by_currency: Record<string, string> }>(`/api/v1/cash-custody/transfers?${query}`, { signal: controller.signal })]).then(([available, result]) => { if (controller.signal.aborted) return; setOptions(available); setTransfers(result.items); setTotal(result.total_count); setInTransit(result.in_transit_by_currency); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [page, status, currency, localRevision, revision]);
  useEffect(() => () => { detailVersion.current += 1; }, []);

  function availableActions(transfer: Transfer) {
    if (!["sent", "disputed", "return_pending"].includes(transfer.status)) return [];
    const values: string[] = [];
    if (transfer.receiver_id === options.current_user_id && transfer.status !== "return_pending") values.push("receive", "report_difference", "reject");
    if (transfer.sender_id === options.current_user_id) values.push(...(transfer.status === "return_pending" ? ["confirm_return"] : ["recall"]));
    return values;
  }

  async function open(id: string) {
    const version = ++detailVersion.current;
    try { const result = await apiClient.request<Transfer>(`/api/v1/cash-custody/transfers/${id}`); if (version === detailVersion.current) { setDetail(result); setAction(availableActions(result)[0] || ""); } }
    catch (cause) { if (version === detailVersion.current) setError(problem(cause)); }
  }

  async function mutate(path: string, values: Record<string, unknown>, method = "POST") {
    if (sending.current) return;
    const body = JSON.stringify(values);
    const signature = `${method}:${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    sending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await apiClient.request<Account | Transfer>(`/api/v1/cash-custody${path}`, { method, headers: { "Idempotency-Key": key }, body });
      keys.current.delete(signature);
      if ("sender_id" in result) { detailVersion.current += 1; setDetail(result); setAction(availableActions(result)[0] || ""); }
      setCreating(false);
      setAccountEdit(null);
      setLocalRevision(value => value + 1);
      setNotice("Movimiento registrado. Los fondos en tránsito permanecen separados de los saldos disponibles hasta su confirmación.");
      onChanged();
    } catch (cause) { setError(problem(cause)); if (detail) await open(detail.id); }
    finally { sending.current = false; setBusy(false); }
  }

  function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!source || !destination) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void mutate("/transfers", { ...values, source_kind: source.kind, source_id: source.id, destination_kind: destination.kind, destination_id: destination.id });
  }

  return <section className="cash-submodule cash-submodule-custody space-y-5"><div className="cash-submodule-toolbar flex flex-wrap items-center justify-between gap-4"><div><h2 className="font-semibold"><span className="cash-submodule-symbol"><ArrowLeftRight size={22} aria-hidden="true" /></span>Custodia y traspaso de efectivo</h2><p className="text-sm text-slate-500">Entrega documentada entre responsables, recepción contada y retorno confirmado.</p></div><div className="flex flex-wrap gap-2"><button className={button} disabled={busy} onClick={() => { setLocalRevision(value => value + 1); if (detail) void open(detail.id); }}><RefreshCw size={16} aria-hidden="true" />Actualizar</button>{canWrite && <button className={`${button} cash-button-primary`} disabled={busy} onClick={() => setCreating(value => !value)}><Plus size={16} aria-hidden="true" />Entregar efectivo</button>}{canWrite && options.can_configure && <button className={button} disabled={busy} onClick={() => setAccountEdit("new")}><Settings2 size={16} aria-hidden="true" />Nuevo punto de custodia</button>}</div></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    <div className="flex flex-wrap gap-3">{Object.entries(inTransit).map(([code, amount]) => <div key={code} className="rounded-lg border bg-amber-50 p-3 text-sm"><p>Efectivo en tránsito {code}</p><strong>{amount}</strong></div>)}</div>
    <details><summary className="cursor-pointer text-sm font-medium">Caja fuerte, tesorería y fondos de sede</summary><div className="mt-3 space-y-3">{options.accounts.map(account => <article key={account.id} className="space-y-2 rounded-lg border p-3 text-sm"><div className="flex flex-wrap justify-between gap-2"><strong>{account.code} · {account.name} · {accountKinds[account.kind]}</strong>{canWrite && options.can_configure && <button className={button} disabled={busy} onClick={() => setAccountEdit(account)}>Editar</button>}</div><p>{account.branch_name} · {account.responsible_name} · {account.is_active ? "Activo" : "Inactivo"}</p><p>Saldo disponible: {account.currency} {account.balance} · Versión {account.version}</p><details><summary className="cursor-pointer text-xs">Movimientos de custodia</summary>{account.movements.map(item => <p className="mt-2 text-xs" key={item.movement_id}>{new Date(item.timestamp).toLocaleString("es-PE")} · {item.reason} · Variación {account.currency} {item.amount_delta} · Saldo {item.balance_after}</p>)}</details></article>)}{!options.accounts.length && <p className="text-sm text-slate-500">Todavía no hay puntos de custodia registrados.</p>}</div></details>
    {accountEdit && <form key={accountValue?.id || "new-account"} className="space-y-3 rounded-xl border p-4" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate(`/accounts${accountValue ? `/${accountValue.id}` : ""}`, { ...values, version: accountValue?.version || 0, opening_balance: values.opening_balance || "0", is_active: values.is_active === "on" }, accountValue ? "PUT" : "POST"); }}><h3 className="font-medium">{accountValue ? "Editar punto de custodia" : "Registrar punto y saldo contado inicial"}</h3><div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Código<input className={input} name="code" required pattern="[A-Za-z0-9_-]+" maxLength={64} defaultValue={accountValue?.code} /></label><label className="grid gap-1 text-sm">Nombre<input className={input} name="name" required minLength={2} maxLength={255} defaultValue={accountValue?.name} /></label><label className="grid gap-1 text-sm">Tipo<CustomSelect className={input} name="kind" defaultValue={accountValue?.kind || "safe"}>{Object.entries(accountKinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Moneda<input className={input} name="currency" readOnly={Boolean(accountValue)} pattern="[A-Z]{3}" required maxLength={3} defaultValue={accountValue?.currency || options.base_currency} /></label><label className="grid gap-1 text-sm">Sede<CustomSelect remote={{ resource: "branches" }} className={input} name="branch_id" required defaultValue={accountValue?.branch_id || ""}><option value="">Seleccionar</option>{options.branches.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Persona responsable<CustomSelect remote={{ resource: "people" }} className={input} name="responsible_id" required defaultValue={accountValue?.responsible_id || ""}><option value="">Seleccionar</option>{options.people.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</CustomSelect></label>{!accountValue && <label className="grid gap-1 text-sm">Saldo físico contado al incorporar el punto<input className={input} name="opening_balance" type="number" min="0" step="0.000001" required defaultValue="0" /></label>}</div><label className="flex gap-2 text-sm"><input name="is_active" type="checkbox" defaultChecked={accountValue?.is_active ?? true} />Disponible para custodiar efectivo</label><label className="grid gap-1 text-sm">Motivo y sustento del conteo o cambio<textarea className={input} name="reason" minLength={5} maxLength={4000} required /></label><p className="text-xs text-slate-500">El saldo inicial incorpora efectivo que ya existe. Los fondos posteriores se mueven con traspasos confirmados. Un punto con fondos o traspasos pendientes conserva su responsable.</p><div className="flex gap-2"><button className={button} disabled={busy}>Guardar punto</button><button type="button" className={button} disabled={busy} onClick={() => setAccountEdit(null)}>Cerrar</button></div></form>}
    {creating && <form className="space-y-3 rounded-xl border p-4" onSubmit={send}><h3 className="font-medium">Entregar fondos a otro punto de custodia</h3><label className="grid gap-1 text-sm">Origen bajo tu custodia<CustomSelect className={input} value={sourceKey} required disabled={busy} onChange={event => { setSourceKey(event.target.value); setDestinationKey(""); }}><option value="">Seleccionar origen</option>{options.endpoints.filter(point => point.responsible_id === options.current_user_id).map(point => <option key={pointKey(point)} value={pointKey(point)}>{point.label} · {point.currency} {point.balance}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Destino y persona que confirmará la recepción<CustomSelect className={input} value={destinationKey} required disabled={busy || !source} onChange={event => setDestinationKey(event.target.value)}><option value="">Seleccionar destino</option>{options.endpoints.filter(point => pointKey(point) !== sourceKey && point.currency === source?.currency).map(point => <option key={pointKey(point)} value={pointKey(point)}>{point.label} · {point.responsible_name} · {point.currency}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Importe {source?.currency}<input className={input} name="amount" required type="number" min="0.000001" step="0.000001" max={source?.balance} /></label><label className="grid gap-1 text-sm">Referencia del acta o entrega<input className={input} name="reference" required maxLength={128} /></label><label className="grid gap-1 text-sm">Motivo<textarea className={input} name="reason" required minLength={5} maxLength={4000} /></label><p className="text-sm text-slate-500">El origen reducirá su efectivo disponible. El destino lo incorporará cuando su responsable cuente y confirme la recepción. Las cajas relacionadas conservarán el traspaso pendiente al intentar cerrar.</p><button className={button} disabled={busy || !source || !destination}>Registrar entrega de efectivo</button></form>}
    <div className="cash-submodule-filters flex flex-wrap gap-4"><label className="grid gap-1 text-sm">Estado<CustomSelect className={input} value={status} disabled={busy} onChange={event => { setStatus(event.target.value); setPage(0); }}><option value="">Todos</option>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Moneda<CustomSelect className={input} value={currency} disabled={busy} onChange={event => { setCurrency(event.target.value); setPage(0); }}><option value="">Todas, con importes separados</option>{[...new Set([...options.endpoints.map(point => point.currency), ...Object.keys(inTransit), options.base_currency].filter(Boolean))].sort().map(code => <option key={code} value={code}>{code}</option>)}</CustomSelect></label></div>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Traspaso", "Origen", "Destino", "Importe", "Estado", "Detalle"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{transfers.map(transfer => <tr className="border-t" key={transfer.id}><td className="p-2">{transfer.code} · {transfer.reference}</td><td className="p-2">{transfer.source.label}<p className="text-xs text-slate-500">{transfer.sender_name}</p></td><td className="p-2">{transfer.destination.label}<p className="text-xs text-slate-500">{transfer.receiver_name}</p></td><td className="p-2">{transfer.currency} {transfer.amount}</td><td className="p-2">{statuses[transfer.status]}</td><td className="p-2"><IconAction label="Ver traspaso" tone="primary" className="cash-detail-action" disabled={busy} onClick={() => void open(transfer.id)}><Eye aria-hidden="true" /></IconAction></td></tr>)}</tbody></table>{!transfers.length && <p className="p-3 text-sm text-slate-500">No hay traspasos para estos filtros.</p>}</div><div className="cash-submodule-pagination flex flex-wrap items-center gap-3 text-sm"><button className={button} disabled={busy || page === 0} onClick={() => setPage(value => value - 1)}>Anterior</button><span>{total} traspasos · Página {page + 1}</span><button className={button} disabled={busy || (page + 1) * 10 >= total} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>
    {detail && <div className="space-y-3 rounded-xl border p-4"><div className="flex flex-wrap justify-between gap-2"><h3 className="font-semibold">{detail.code} · {statuses[detail.status]}</h3><button className={button} disabled={busy} onClick={() => { detailVersion.current += 1; setDetail(null); }}>Cerrar detalle</button></div><p className="text-sm">{detail.source.label} → {detail.destination.label} · {detail.currency} {detail.amount}</p><p className="text-sm">Entrega: {detail.sender_name} · Recibe: {detail.receiver_name}</p><p className="text-sm">{detail.reference} · {detail.reason}</p>{detail.received_at && <p className="text-sm">Recepción confirmada: {new Date(detail.received_at).toLocaleString("es-PE")}</p>}{detail.returned_at && <p className="text-sm">Retorno confirmado: {new Date(detail.returned_at).toLocaleString("es-PE")}</p>}
      {canWrite && !!availableActions(detail).length && <form className="grid gap-3 rounded-lg border p-3" key={`${detail.id}:${detail.version}`} onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate(`/transfers/${detail.id}/actions`, { ...values, action, version: detail.version, counted_amount: values.counted_amount || null }); }}><label className="grid gap-1 text-sm">Acción<CustomSelect className={input} value={action} disabled={busy} onChange={event => setAction(event.target.value)}>{availableActions(detail).map(value => <option key={value} value={value}>{actions[value]}</option>)}</CustomSelect></label>{["receive", "report_difference", "confirm_return"].includes(action) && <label className="grid gap-1 text-sm">Importe físicamente contado {detail.currency}<input className={input} name="counted_amount" type="number" min="0" step="0.000001" required /></label>}<label className="grid gap-1 text-sm">Motivo y constancia de la acción<textarea className={input} name="reason" required minLength={5} maxLength={4000} /></label><p className="text-xs text-slate-500">Una diferencia conserva el efectivo pendiente. Solicitar retorno no restaura el origen: debe confirmarse su recepción física por el importe completo.</p><button className={button} disabled={busy || !action}>Registrar acción</button></form>}
      <details open><summary className="cursor-pointer text-sm font-medium">Historial de entrega, conteos y recepción</summary><ul className="mt-2 space-y-2 text-sm">{detail.history.map((item, index) => <li key={`${item.at}:${index}`}>{new Date(item.at).toLocaleString("es-PE")} · {historyLabels[item.action] || item.action} · {item.actor}<p>{item.reason}</p>{item.counted_amount !== null && <p>Contado: {detail.currency} {item.counted_amount}</p>}</li>)}</ul></details>
    </div>}
  </section>;
}
