import { IconAction } from "../../../ui/components/primitives/IconAction";
import "./cash-submodules.css";
import { Wallet, RefreshCw, Plus, Settings2, Eye } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Policy = { categories: string[]; max_advance: string; max_receipt: string; max_settlement: string; document_required: boolean };
type Fund = { id: string; account_id: string; name: string; code: string; currency: string; balance: string; responsible_id: string; responsible_name: string; version: number; is_active: boolean; policy: Policy; history: { version: number; actor: string; at: string; reason: string }[] };
type Receipt = { title: string; category: string; issuer: string; document_reference: string; evidence: string; expense_date: string; amount: string; cost_center_id: string };
type Advance = { id: string; code: string; fund_id: string; fund_name: string; responsible_id: string; beneficiary_id: string; beneficiary_name: string; currency: string; amount: string; due_date: string; is_overdue: boolean; purpose: string; status: string; version: number; policy: Policy; settlement: { receipts?: Receipt[]; total?: string; difference?: string; recall?: boolean; expense_ids?: string[]; revisions?: { total: string; submitted_at: string; receipts: Receipt[] }[] }; history: { version: number; action: string; reason: string; actor: string; at: string; counted_amount: string | null }[] };
type Options = { funds: Fund[]; accounts: { id: string; name: string; currency: string; is_active: boolean }[]; people: { id: string; name: string }[]; current_user_id: string; can_review: boolean; cost_centers: { id: string; name: string }[]; business_date: string };
const statusLabels: Record<string, string> = { requested: "Solicitado", issued: "Entregado, pendiente de aceptación", active: "Pendiente de rendir", submitted: "Rendición en revisión", return_due: "Sobrante pendiente de retorno", reimbursement_due: "Reembolso pendiente", reimbursement_sent: "Reembolso entregado, pendiente de aceptación", closed: "Concluido", cancelled: "Cancelado" };
const actionLabels: Record<string, string> = { issue: "Entregar anticipo", accept: "Aceptar efectivo recibido", submit: "Enviar rendición", approve: "Aprobar rendición", reject: "Rechazar para corregir", cancel: "Cancelar solicitud", recall: "Solicitar retorno íntegro", confirm_return: "Confirmar sobrante recibido", pay_reimbursement: "Entregar reembolso", accept_reimbursement: "Aceptar reembolso recibido" };
const field = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
function errorText(cause: unknown) { const value = (cause as { detail?: unknown })?.detail; return typeof value === "string" ? value : cause instanceof Error ? cause.message : "No se pudo completar la operación de caja chica."; }

export function PettyCashPanel({ canWrite, revision, onChanged }: { canWrite: boolean; revision: number; onChanged: () => void }) {
  const [options, setOptions] = useState<Options>({ funds: [], accounts: [], people: [], current_user_id: "", can_review: false, cost_centers: [], business_date: "" });
  const [rows, setRows] = useState<Advance[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState("");
  const [fundFilter, setFundFilter] = useState("");
  const [localRevision, setLocalRevision] = useState(0);
  const [editing, setEditing] = useState<Fund | "new" | null>(null);
  const [requesting, setRequesting] = useState(false);
  const [fundId, setFundId] = useState("");
  const [detail, setDetail] = useState<Advance | null>(null);
  const [action, setAction] = useState("");
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const mutex = useRef(false);
  const keys = useRef(new Map<string, string>());
  const detailRevision = useRef(0);
  const currentFund = options.funds.find(row => row.id === fundId);
  const editingFund = editing && editing !== "new" ? editing : null;

  useEffect(() => {
    const controller = new AbortController();
    const query = new URLSearchParams({ limit: "10", offset: String(page * 10) });
    if (filter) query.set("status", filter);
    if (fundFilter) query.set("fund_id", fundFilter);
    void Promise.all([
      apiClient.request<Options>("/api/v1/petty-cash/options", { signal: controller.signal }),
      apiClient.request<{ items: Advance[]; total_count: number }>(`/api/v1/petty-cash/advances?${query}`, { signal: controller.signal })
    ]).then(([available, result]) => { if (controller.signal.aborted) return; setOptions(available); setRows(result.items); setTotal(result.total_count); }).catch(cause => { if (!controller.signal.aborted) setError(errorText(cause)); });
    return () => controller.abort();
  }, [revision, localRevision, page, filter, fundFilter]);
  useEffect(() => () => { detailRevision.current += 1; }, []);

  function availableActions(row: Advance) {
    const choices: string[] = [];
    const beneficiary = row.beneficiary_id === options.current_user_id;
    const custodian = row.responsible_id === options.current_user_id;
    if (row.status === "requested") {
      if (custodian) choices.push("issue");
      if (custodian || beneficiary) choices.push("cancel");
    }
    if (row.status === "issued" && beneficiary) choices.push("accept");
    if (row.status === "active" && beneficiary) choices.push("submit");
    if (["issued", "active"].includes(row.status) && custodian) choices.push("recall");
    if (row.status === "submitted" && options.can_review && !beneficiary) choices.push("approve", "reject");
    if (row.status === "return_due" && custodian) choices.push("confirm_return");
    if (row.status === "reimbursement_due" && custodian) choices.push("pay_reimbursement");
    if (row.status === "reimbursement_sent" && beneficiary) choices.push("accept_reimbursement");
    return choices;
  }

  function show(row: Advance) {
    setDetail(row);
    setAction(availableActions(row)[0] || "");
    setReceipts(row.settlement.receipts || []);
  }

  async function open(identifier: string) {
    const version = ++detailRevision.current;
    try { const result = await apiClient.request<Advance>(`/api/v1/petty-cash/advances/${identifier}`); if (version === detailRevision.current) show(result); }
    catch (cause) { if (version === detailRevision.current) setError(errorText(cause)); }
  }

  async function mutate(path: string, values: Record<string, unknown>, method = "POST") {
    if (mutex.current) return;
    const body = JSON.stringify(values);
    const signature = `${method}:${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    mutex.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await apiClient.request<Fund | Advance>(`/api/v1/petty-cash${path}`, { method, body, headers: { "Idempotency-Key": key } });
      keys.current.delete(signature);
      if ("beneficiary_id" in result) { detailRevision.current += 1; show(result); }
      setEditing(null);
      setRequesting(false);
      setLocalRevision(value => value + 1);
      setNotice("Operación registrada con su historial y movimientos del fondo.");
      onChanged();
    } catch (cause) { setError(errorText(cause)); }
    finally { mutex.current = false; setBusy(false); }
  }

  function saveFund(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void mutate(`/funds${editingFund ? `/${editingFund.id}` : ""}`, { ...values, account_id: editingFund?.account_id || values.account_id, version: editingFund?.version || 0, categories: String(values.categories).split("\n").map(value => value.trim()).filter(Boolean), document_required: values.document_required === "on", is_active: values.is_active === "on" }, editingFund ? "PUT" : "POST");
  }

  function changeReceipt(index: number, key: keyof Receipt, value: string) {
    setReceipts(previous => previous.map((item, position) => position === index ? { ...item, [key]: value } : item));
  }

  return <section className="cash-submodule cash-submodule-petty space-y-5">
    <div className="cash-submodule-toolbar flex flex-wrap items-center justify-between gap-4"><div><h2 className="font-semibold"><span className="cash-submodule-symbol"><Wallet size={22} aria-hidden="true" /></span>Caja chica y rendiciones</h2><p className="text-sm text-slate-500">Anticipos por beneficiario, comprobantes, devolución de sobrantes y reembolsos.</p></div><div className="flex flex-wrap gap-2"><button className={button} disabled={busy} onClick={() => { setLocalRevision(value => value + 1); if (detail) void open(detail.id); }}><RefreshCw size={16} aria-hidden="true" />Actualizar</button>{canWrite && <button className={`${button} cash-button-primary`} disabled={busy} onClick={() => setRequesting(value => !value)}><Plus size={16} aria-hidden="true" />Solicitar anticipo</button>}{canWrite && options.can_review && <button className={button} disabled={busy} onClick={() => setEditing("new")}><Settings2 size={16} aria-hidden="true" />Configurar fondo</button>}</div></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    <details><summary className="cursor-pointer text-sm font-medium">Fondos y reglas</summary><div className="mt-3 space-y-3">{options.funds.map(fund => <article key={fund.id} className="space-y-2 rounded-lg border p-3 text-sm"><div className="flex justify-between gap-3"><strong>{fund.code} · {fund.name}</strong>{canWrite && options.can_review && <button className={button} onClick={() => setEditing(fund)} disabled={busy}>Editar reglas</button>}</div><p>{fund.responsible_name} · {fund.is_active ? "Activo" : "Inactivo"} · Saldo disponible: {fund.currency} {fund.balance}</p><p>Categorías: {fund.policy.categories.join(", ")}</p><p>Máximo anticipo: {fund.policy.max_advance} · Comprobante: {fund.policy.max_receipt} · Rendición: {fund.policy.max_settlement} {fund.currency}</p><p>{fund.policy.document_required ? "Comprobante obligatorio" : "Admite gastos sin número de comprobante con sustento escrito"}</p><details><summary>Historial de reglas</summary>{fund.history.map(item => <p key={item.version}>Versión {item.version} · {item.actor} · {item.at.slice(0, 19).replace("T", " ")} · {item.reason}</p>)}</details></article>)}{!options.funds.length && <p className="text-sm text-slate-500">Cree un punto de custodia de tipo fondo de sede y configure aquí sus reglas.</p>}</div></details>
    {editing && <form key={editingFund?.id || "new-fund"} onSubmit={saveFund} className="space-y-3 rounded-xl border p-4"><h3 className="font-medium">Reglas del fondo</h3><label className="grid gap-1 text-sm">Punto de custodia<CustomSelect name="account_id" required disabled={Boolean(editingFund)} defaultValue={editingFund?.account_id || ""} className={field}><option value="">Seleccione fondo de sede</option>{options.accounts.filter(account => account.is_active || account.id === editingFund?.account_id).map(account => <option key={account.id} value={account.id}>{account.name} · {account.currency}</option>)}</CustomSelect></label><div className="grid gap-3 md:grid-cols-3">{[["max_advance", "Máximo anticipo"], ["max_receipt", "Máximo por comprobante"], ["max_settlement", "Máximo total rendición"]].map(([name, label]) => <label key={name} className="grid gap-1 text-sm">{label}<input type="number" name={name} required min="0.000001" step="0.000001" defaultValue={editingFund?.policy[name as keyof Policy] as string || ""} className={field} /></label>)}</div><label className="grid gap-1 text-sm">Categorías permitidas, una por línea<textarea name="categories" required rows={3} defaultValue={editingFund?.policy.categories.join("\n") || "Movilidad\nMateriales\nAlimentación"} className={field} /></label><label className="flex gap-2 text-sm"><input type="checkbox" name="document_required" defaultChecked={editingFund?.policy.document_required ?? true} />Exigir número de comprobante</label><label className="flex gap-2 text-sm"><input type="checkbox" name="is_active" defaultChecked={editingFund?.is_active ?? true} />Permitir nuevas solicitudes y entregas</label><label className="grid gap-1 text-sm">Motivo<textarea name="reason" required minLength={5} maxLength={2000} className={field} /></label><p className="text-xs text-slate-500">Los anticipos ya solicitados conservan las reglas vigentes al crearlos. Un fondo inactivo permite concluir sus rendiciones pendientes.</p><div className="flex gap-2"><button className={button} disabled={busy}>Guardar reglas</button><button type="button" className={button} disabled={busy} onClick={() => setEditing(null)}>Cerrar</button></div></form>}
    {requesting && <form className="space-y-3 rounded-xl border p-4" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate("/advances", { ...values, fund_id: fundId }); }}><h3 className="font-medium">Solicitar anticipo para gastos</h3><label className="grid gap-1 text-sm">Fondo<CustomSelect required value={fundId} onChange={event => setFundId(event.target.value)} className={field}><option value="">Seleccionar fondo</option>{options.funds.filter(fund => fund.is_active).map(fund => <option key={fund.id} value={fund.id}>{fund.name} · {fund.currency} · {fund.responsible_name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Beneficiario<CustomSelect key={fundId} required name="beneficiary_id" defaultValue={options.current_user_id} className={field}>{options.people.filter(person => currentFund?.responsible_id === options.current_user_id || person.id === options.current_user_id).map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Importe {currentFund?.currency}<input type="number" name="amount" required min="0.000001" step="0.000001" max={currentFund?.policy.max_advance} className={field} /></label><label className="grid gap-1 text-sm">Rendir hasta<input type="date" required name="due_date" min={options.business_date} className={field} /></label><label className="grid gap-1 text-sm">Finalidad<textarea required name="purpose" minLength={5} maxLength={2000} className={field} /></label><p className="text-xs text-slate-500">La solicitud no retira efectivo. El custodio registrará su entrega y el beneficiario confirmará el importe recibido.</p><button className={button} disabled={busy || !currentFund}>Registrar solicitud</button></form>}
    <div className="cash-submodule-filters flex flex-wrap gap-4"><label className="grid gap-1 text-sm">Estado<CustomSelect className={field} value={filter} onChange={event => { setFilter(event.target.value); setPage(0); }}><option value="">Todos</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Fondo<CustomSelect className={field} value={fundFilter} onChange={event => { setFundFilter(event.target.value); setPage(0); }}><option value="">Todos</option>{options.funds.map(fund => <option key={fund.id} value={fund.id}>{fund.name} · {fund.currency}</option>)}</CustomSelect></label></div>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Anticipo", "Beneficiario", "Fondo", "Importe", "Vencimiento", "Estado", "Detalle"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.id} className="border-t"><td className="p-2">{row.code}</td><td className="p-2">{row.beneficiary_name}</td><td className="p-2">{row.fund_name}</td><td className="p-2">{row.currency} {row.amount}</td><td className={`p-2 ${row.is_overdue ? "text-red-700" : ""}`}>{row.due_date}{row.is_overdue ? " · Vencido" : ""}</td><td className="p-2">{statusLabels[row.status]}</td><td className="p-2"><IconAction label="Ver anticipo y rendición" tone="primary" className="cash-detail-action" disabled={busy} onClick={() => void open(row.id)}><Eye aria-hidden="true" /></IconAction></td></tr>)}</tbody></table>{!rows.length && <p className="p-3 text-sm text-slate-500">No hay anticipos para estos filtros.</p>}</div><div className="cash-submodule-pagination flex flex-wrap items-center gap-3 text-sm"><button className={button} disabled={busy || page === 0} onClick={() => setPage(value => value - 1)}>Anterior</button><span>{total} anticipos · Página {page + 1}</span><button className={button} disabled={busy || (page + 1) * 10 >= total} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>
    {detail && <article className="space-y-3 rounded-xl border p-4"><div className="flex justify-between gap-3"><h3 className="font-semibold">{detail.code} · {statusLabels[detail.status]}</h3><button className={button} disabled={busy} onClick={() => { detailRevision.current += 1; setDetail(null); }}>Cerrar detalle</button></div><p className="text-sm">{detail.beneficiary_name} · {detail.fund_name} · {detail.currency} {detail.amount} · Rendir hasta {detail.due_date}</p><p className="text-sm">{detail.purpose}</p><p className="text-sm">Gastos rendidos: {detail.settlement.total || "0"} {detail.currency} · Saldo de la rendición (positivo: devolver; negativo: reembolsar): {detail.settlement.difference ?? "Pendiente de aprobación"}</p>{detail.settlement.recall && <p className="text-sm text-amber-800">Se solicitó el retorno íntegro del anticipo.</p>}
      {detail.settlement.receipts?.map((receipt, index) => <div key={index} className="rounded-lg border p-3 text-sm"><strong>{receipt.title} · {receipt.amount} {detail.currency}</strong><p>{receipt.category} · {receipt.expense_date} · {receipt.issuer} · {receipt.document_reference || "Sin número de comprobante"}</p><p>{receipt.evidence}</p></div>)}
      {Boolean(detail.settlement.expense_ids?.length) && <p className="text-xs text-slate-600">Gastos vinculados: {detail.settlement.expense_ids?.join(", ")}. La devolución del sobrante y el reembolso se registran como movimientos del fondo y no como gastos adicionales.</p>}
      {canWrite && availableActions(detail).length > 0 && <form key={`${detail.id}:${detail.version}`} className="space-y-3 rounded-lg border p-3" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void mutate(`/advances/${detail.id}/actions`, { action, version: detail.version, reason: values.reason, counted_amount: values.counted_amount || null, receipts: action === "submit" ? receipts : [] }); }}>
        <label className="grid gap-1 text-sm">Acción<CustomSelect value={action} onChange={event => setAction(event.target.value)} className={field} disabled={busy}>{availableActions(detail).map(value => <option key={value} value={value}>{actionLabels[value]}</option>)}</CustomSelect></label>
        {action === "submit" && <div className="space-y-3"><p className="text-xs text-slate-500">Registre cada comprobante y su centro de costo. Una rendición sin gastos exige devolver el anticipo completo.</p>{receipts.map((receipt, index) => <fieldset key={index} className="space-y-2 rounded-lg border p-3"><legend className="px-1 text-sm">Gasto {index + 1}</legend><div className="grid gap-2 md:grid-cols-2"><label className="grid gap-1 text-xs">Concepto<input required minLength={3} maxLength={255} value={receipt.title} onChange={event => changeReceipt(index, "title", event.target.value)} className={field} /></label><label className="grid gap-1 text-xs">Categoría<CustomSelect remote={{ resource: "categories" }} required value={receipt.category} onChange={event => changeReceipt(index, "category", event.target.value)} className={field}><option value="">Seleccione</option>{detail.policy.categories.map(category => <option key={category} value={category}>{category}</option>)}</CustomSelect></label><label className="grid gap-1 text-xs">Emisor o identificación del proveedor<input required minLength={2} maxLength={40} value={receipt.issuer} onChange={event => changeReceipt(index, "issuer", event.target.value)} className={field} /></label><label className="grid gap-1 text-xs">Número de comprobante<input required={detail.policy.document_required} maxLength={60} value={receipt.document_reference} onChange={event => changeReceipt(index, "document_reference", event.target.value)} className={field} /></label><label className="grid gap-1 text-xs">Fecha del gasto<input type="date" required max={options.business_date} value={receipt.expense_date} onChange={event => changeReceipt(index, "expense_date", event.target.value)} className={field} /></label><label className="grid gap-1 text-xs">Importe {detail.currency}<input type="number" required min="0.000001" step="0.000001" max={detail.policy.max_receipt} value={receipt.amount} onChange={event => changeReceipt(index, "amount", event.target.value)} className={field} /></label><label className="grid gap-1 text-xs">Centro de costo<CustomSelect required value={receipt.cost_center_id} onChange={event => changeReceipt(index, "cost_center_id", event.target.value)} className={field}><option value="">Seleccione</option>{options.cost_centers.map(center => <option key={center.id} value={center.id}>{center.name}</option>)}</CustomSelect></label><label className="grid gap-1 text-xs">Detalle y sustento<textarea required minLength={5} maxLength={2000} value={receipt.evidence} onChange={event => changeReceipt(index, "evidence", event.target.value)} className={field} /></label></div><button type="button" className={button} disabled={busy} onClick={() => setReceipts(previous => previous.filter((_, position) => position !== index))}>Quitar gasto</button></fieldset>)}<button type="button" disabled={busy || receipts.length >= 100} className={button} onClick={() => setReceipts(previous => [...previous, { title: "", category: "", issuer: "", document_reference: "", evidence: "", expense_date: options.business_date, amount: "", cost_center_id: "" }])}>Añadir comprobante</button></div>}
        {["issue", "accept", "confirm_return", "pay_reimbursement", "accept_reimbursement"].includes(action) && <label className="grid gap-1 text-sm">Importe físicamente contado {detail.currency}<input type="number" name="counted_amount" required min="0" step="0.000001" className={field} /></label>}
        <label className="grid gap-1 text-sm">Motivo y constancia<textarea name="reason" required minLength={5} maxLength={2000} className={field} /></label><button disabled={busy || !action} className={button}>Registrar acción</button>
      </form>}
      <details><summary className="cursor-pointer text-sm font-medium">Rendiciones anteriores corregidas</summary>{detail.settlement.revisions?.map((item, index) => <div key={index} className="mt-2 text-xs"><p>{item.submitted_at.slice(0, 19).replace("T", " ")} · Total {item.total} {detail.currency}</p>{item.receipts.map((receipt, position) => <p key={position}>{receipt.title} · {receipt.amount} · {receipt.issuer} {receipt.document_reference}</p>)}</div>)}</details>
      <details open><summary className="cursor-pointer text-sm font-medium">Historial de entrega y rendición</summary>{detail.history.map(item => <div key={item.version} className="mt-2 text-sm"><p>{item.at.slice(0, 19).replace("T", " ")} · {actionLabels[item.action.toLowerCase()] || item.action} · {item.actor}</p><p>{item.reason}{item.counted_amount !== null ? ` · Contado: ${item.counted_amount} ${detail.currency}` : ""}</p></div>)}</details>
    </article>}
  </section>;
}
