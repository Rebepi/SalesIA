import { CustomSelect } from "../../../ui/components/CustomSelect";
import { TablePagination } from "../../../ui/components/TablePagination";
import { RefreshCw, Wallet, Search, Coins, History, LockKeyhole, HandCoins } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect, type RemoteEntityOption } from "../../../ui/components/RemoteEntitySelect";
import { CustomerCreditConversions } from "./CustomerCreditConversions";

type Customer = Record<string, unknown> & { id: string; legal_name?: string; full_name?: string; name?: string; document_number?: string };
type CreditSale = Record<string, unknown> & { id: string; document_number: string; currency: string; unpaid_amount: string; version: number };
type Source = { id: string; currency: string; original_amount: string; remaining_amount: string; available_amount: string; reserved_amount: string; expired: boolean; expires_at: string | null; reference_type: string; reference_id: string | null };
type Reservation = { id: string; payment_id: string | null; sale_id: string; currency: string; amount: string; status: string; expires_at: string; reason: string; version: number };
type Movement = { id: string; movement_type: string; currency: string | null; amount_delta: string; reference_type: string; reference_id: string | null; payment_id: string | null; notes: string | null; created_at: string; expires_at: string | null };
type Unapplied = { id: string; sale_id: string; document_number: string; currency: string; amount: string; allocated_amount: string; refunded_amount: string; available_amount: string; reserved_amount: string; payment_method: string; reference_code: string | null; created_at: string };
type RefundOptions = { unapplied_amount: string; payment_method: string; cash_sessions: { id: string; terminal_code: string; balance: string }[] };
type CreditBook = { balances: { currency: string; available_balance: string; reserved_balance: string; expired_balance: string; ledger_balance: string }[]; can_apply: boolean; warnings: string[]; sources: Source[]; reservations: Reservation[]; movements: Movement[]; allocations: { debit_id: string; credit_id: string; amount: string; currency: string; historical: boolean }[]; unapplied_payments: Unapplied[]; unapplied_balances: { currency: string; available_amount: string; reserved_amount: string }[] };
const field = "w-full rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const customerOption = (row: Customer): RemoteEntityOption<Customer> => ({ value: row.id, label: row.legal_name || row.full_name || row.name || row.id, description: row.document_number, data: row });
const saleOption = (row: CreditSale): RemoteEntityOption<CreditSale> => ({ value: row.id, label: row.document_number, description: `Pendiente ${row.currency} ${row.unpaid_amount}`, data: row });
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo actualizar el libro de saldos del cliente."; }
function units(value: string) { const [whole, fraction = ""] = value.split("."); return BigInt(whole || "0") * 1000000n + BigInt(fraction.padEnd(6, "0").slice(0, 6)); }
function amount(value: bigint) { return `${value / 1000000n}.${String(value % 1000000n).padStart(6, "0")}`; }
function sumAmounts(values: string[]) { return amount(values.reduce((sum, value) => sum + units(value), 0n)); }
function minimum(left: string, right: string) { return units(left) <= units(right) ? left : right; }

export function CustomerCreditPanel({ canWrite, revision, onChanged, standalone = false }: { standalone?: boolean; canWrite: boolean; revision: number; onChanged: () => void }) {
  const [customer, setCustomer] = useState<Customer>();
  const [book, setBook] = useState<CreditBook | null>(null);
  const [currency, setCurrency] = useState("");
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [sale, setSale] = useState<CreditSale>();
  const [selected, setSelected] = useState<string[]>([]);
  const [reservationId, setReservationId] = useState("");
  const [action, setAction] = useState<"apply" | "reserve">("apply");
  const [detail, setDetail] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [movementPageSize, setMovementPageSize] = useState(10);
  const [canIdentify, setCanIdentify] = useState(false);
  const [canApply, setCanApply] = useState(false);
  const [canPayments, setCanPayments] = useState(false);
  const [advanceId, setAdvanceId] = useState("");
  const [advanceSale, setAdvanceSale] = useState<CreditSale>();
  const [advanceAction, setAdvanceAction] = useState<"apply" | "refund" | "reserve">("apply");
  const [advanceReservationId, setAdvanceReservationId] = useState("");
  const [refundOptions, setRefundOptions] = useState<RefundOptions | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localRevision, setLocalRevision] = useState(0);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  const customerId = useRef(customer?.id);
  customerId.current = customer?.id;
  useEffect(() => {
    let active = true;
    void apiClient.getMe().then(me => { if (active) { setCanIdentify(Boolean(me.permissions?.includes("organization:manage") || me.permissions?.includes("approvals:manage"))); setCanApply(Boolean(me.permissions?.includes("sales:write"))); setCanPayments(Boolean(me.permissions?.includes("payments:write"))); } }).catch(() => undefined);
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    if (!customer) { setBook(null); return () => controller.abort(); }
    setLoading(true);
    setError("");
    void apiClient.request<CreditBook>(`/api/v1/customers/${customer.id}/store-credit${currency ? `?currency=${currency}` : ""}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) { setBook(result); setCurrencies(previous => Array.from(new Set([...previous, ...result.balances.map(row => row.currency), ...result.unapplied_balances.map(row => row.currency)])).sort()); setSelected(previous => previous.filter(id => result.sources.some(source => source.id === id && Number(source.available_amount) > 0))); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [customer, currency, revision, localRevision]);
  useEffect(() => {
    const controller = new AbortController();
    setRefundOptions(null);
    if (!advanceId || advanceAction !== "refund") return () => controller.abort();
    void apiClient.request<RefundOptions>(`/api/v1/refund-options/${advanceId}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setRefundOptions(result); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [advanceId, advanceAction, revision, localRevision]);
  async function write(path: string, payload: unknown, message: string) {
    if (lock.current || !customer) return false;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    const identifier = customer.id;
    try {
      await apiClient.request(path, { method: "POST", headers: { "Idempotency-Key": key }, body });
      keys.current.delete(signature);
      if (customerId.current === identifier) { setNotice(message); setLocalRevision(value => value + 1); setSelected([]); setReservationId(""); setSale(undefined); setAdvanceReservationId(""); setAdvanceSale(undefined); }
      onChanged();
      return true;
    } catch (cause) { if (customerId.current === identifier) { setError(problem(cause)); setLocalRevision(value => value + 1); setSale(undefined); setAdvanceSale(undefined); setAdvanceReservationId(""); } return false; }
    finally { lock.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sale) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (action === "reserve") await write(`/api/v1/sales/${sale.id}/reserve-store-credit`, { amount: values.amount, source_ids: selected, duration_hours: Number(values.duration_hours), expected_sale_version: sale.version, reason: values.reason }, "Reserva registrada. El importe queda asignado a esta deuda hasta su aplicación, liberación o vencimiento.");
    else await write(`/api/v1/sales/${sale.id}/apply-store-credit`, { amount: values.amount, source_ids: reservationId ? [] : selected, reservation_id: reservationId || null }, "Crédito aplicado a la venta y sus cuotas, con su procedencia registrada.");
  }
  async function submitAdvance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!advanceId) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (advanceAction === "apply" && advanceSale) await write(`/api/v1/payments/${advanceId}/allocations`, { sale_id: advanceSale.id, allocated_amount: values.amount, reservation_id: advanceReservationId || null }, "Anticipo aplicado. Se reduce la deuda sin volver a registrar una entrada de dinero.");
    if (advanceAction === "reserve" && advanceSale) await write(`/api/v1/sales/${advanceSale.id}/reserve-store-credit`, { payment_id: advanceId, amount: values.amount, expected_sale_version: advanceSale.version, duration_hours: Number(values.duration_hours), reason: values.reason }, "Anticipo reservado. Su importe queda protegido para la deuda elegida hasta su aplicación, liberación o vencimiento.");
    if (advanceAction === "refund") await write("/api/v1/refunds", { payment_id: advanceId, unapplied_only: true, amount: values.amount, cash_session_id: values.cash_session_id || null, payout_reference: values.payout_reference, reason: values.reason }, "Devolución del anticipo registrada. Los importes ya aplicados a ventas conservan sus asignaciones.");
  }
  const sources = book?.sources.filter(row => !currency || row.currency === currency) || [];
  const movements = book?.movements || [];
  const activeReservations = book?.reservations.filter(row => row.status === "active" && !row.payment_id && row.sale_id === sale?.id) || [];
  const reservation = activeReservations.find(row => row.id === reservationId);
  const available = reservation ? reservation.amount : sumAmounts(sources.filter(row => !selected.length || selected.includes(row.id)).map(row => row.available_amount));
  const maximum = minimum(available, sale?.unpaid_amount || "0");
  const advance = book?.unapplied_payments.find(row => row.id === advanceId);
  const advanceReservations = book?.reservations.filter(row => row.payment_id === advanceId && row.sale_id === advanceSale?.id && row.status === "active") || [];
  const advanceReservation = advanceReservations.find(row => row.id === advanceReservationId);
  const advanceMaximum = minimum(advanceAction === "apply" && advanceReservation ? advanceReservation.amount : advance?.available_amount || "0", advanceAction !== "refund" ? advanceSale?.unpaid_amount || "0" : refundOptions?.unapplied_amount || "0");
  const Root = standalone ? "section" : "details";
  const money = (value: string) => new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value));
  return <Root className={standalone ? "refund-submodule credit-workspace" : "refund-submodule rounded-2xl border border-slate-200 bg-white p-5"}>
    {!standalone && <summary className="cursor-pointer font-semibold">Saldos a favor del cliente por moneda</summary>}
    <div className={standalone ? "space-y-5" : "mt-4 space-y-5"}>
    <div className="credit-controls space-y-4">
    <div className="flex items-center gap-3"><span className="credit-symbol"><Wallet size={22} aria-hidden="true" /></span><div><h2 className="font-semibold">Libro de saldos a favor</h2><p className="mt-1 text-xs text-slate-500">Consulta por cliente y moneda</p></div></div>
    <p className="text-sm text-slate-500">Consulte el origen, consumo, reservas y vencimiento de cada crédito. Cada aplicación usa la moneda de la venta y reduce su deuda sin generar una nueva entrada de dinero.</p>
    <div className="credit-filter-grid grid items-end gap-4"><RemoteEntitySelect<Customer> value={customer?.id || ""} onChange={(_, option) => { setCustomer(option?.data); setBook(null); setCurrency(""); setCurrencies([]); setAdvanceId(""); setAdvanceSale(undefined); setAdvanceReservationId(""); setSale(undefined); setSelected([]); setReservationId(""); setPage(0); setDetail(null); }} endpoint="/api/v1/customers" entityType="customer" mapOption={customerOption} label="Cliente" disabled={busy} /><label className="grid gap-1 text-sm">Moneda<CustomSelect className={field} value={currency} disabled={busy || !customer} onChange={event => { setCurrency(event.target.value); setAdvanceId(""); setAdvanceSale(undefined); setAdvanceReservationId(""); setBook(null); setSale(undefined); setSelected([]); setReservationId(""); setPage(0); }}><option value="">Todas las monedas</option>{currencies.map(value => <option key={value}>{value}</option>)}</CustomSelect></label><button className={`${button} credit-refresh`} disabled={busy || !customer || loading} onClick={() => setLocalRevision(value => value + 1)}><RefreshCw size={16} className={loading ? "animate-spin" : ""} aria-hidden="true" />Actualizar libro</button></div>
    </div>
    {!customer && <div className="credit-empty"><Search size={30} aria-hidden="true" /><h3>Selecciona un cliente</h3><p>Busca por nombre o documento para consultar sus créditos, anticipos y aplicaciones.</p></div>}
    {loading && <p role="status" className="text-sm">Consultando saldos y aplicaciones…</p>}{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    {book && <><div className="credit-balance-grid">{book.balances.map(row => <article key={row.currency} className="credit-balance-card"><div className="flex items-center justify-between gap-3"><span className="credit-currency"><Coins size={16} aria-hidden="true" />{row.currency}</span><span className="text-xs text-slate-500">Crédito de tienda</span></div><p className="mt-4 text-xs text-slate-500">Disponible</p><strong className="credit-available">{row.currency} {money(row.available_balance)}</strong><dl><div><dt>Reservado</dt><dd>{money(row.reserved_balance)}</dd></div><div><dt>Vencido</dt><dd>{money(row.expired_balance)}</dd></div><div><dt>Remanente</dt><dd>{money(row.ledger_balance)}</dd></div></dl></article>)}</div>{book.warnings.map((warning, index) => <p key={index} className="text-sm text-amber-800">{warning}</p>)}
      <div className="credit-sources-card"><div className="credit-table-heading"><h3>Créditos y disponibilidad</h3><span>{sources.length} {sources.length === 1 ? "crédito" : "créditos"}</span></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Elegir", "Origen", "Moneda", "Otorgado", "Remanente", "Libre", "Reservado", "Vencimiento"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{sources.map(row => <tr className="border-t" key={row.id}><td className="p-2"><input aria-label={`Elegir crédito ${row.id}`} type="checkbox" checked={selected.includes(row.id)} disabled={busy || !currency || row.currency !== currency || Number(row.available_amount) <= 0 || !!reservationId} onChange={event => setSelected(previous => event.target.checked ? [...previous, row.id] : previous.filter(id => id !== row.id))} /></td><td className="p-2"><button className="text-teal-800 underline" onClick={() => setDetail(row.id)}>{row.reference_type} · {row.reference_id?.slice(0, 8) || row.id.slice(0, 8)}</button></td><td className="p-2">{row.currency}</td><td className="p-2">{money(row.original_amount)}</td><td className="p-2">{money(row.remaining_amount)}</td><td className="p-2">{money(row.available_amount)}</td><td className="p-2">{money(row.reserved_amount)}</td><td className="p-2">{row.expired ? "Vencido · " : ""}{row.expires_at ? row.expires_at.slice(0, 10) : "Sin vencimiento"}</td></tr>)}</tbody></table>{sources.length === 0 && <div className="credit-empty credit-empty-inline"><Coins size={28} aria-hidden="true" /><h3>Sin créditos para esta selección</h3><p>Los anticipos y el dinero sin aplicar se consultan en su bloque correspondiente.</p></div>}</div></div>
      {canWrite && canApply && currency && book.can_apply && <form onSubmit={submit} className="space-y-3 rounded-xl border p-4"><h3 className="font-semibold">Aplicar o reservar saldo {currency}</h3><RemoteEntitySelect<CreditSale> key={`${customer?.id}:${currency}:${localRevision}:${revision}`} value={sale?.id || ""} initialOption={sale ? saleOption(sale) : undefined} onChange={(_, option) => { setSale(option?.data); setReservationId(""); }} endpoint={`/api/v1/customers/${customer?.id}/store-credit/sales`} queryParams={{ currency }} entityType="sale" mapOption={saleOption} label="Venta con deuda" disabled={busy || loading} required />
        <div className="grid gap-3 md:grid-cols-3"><label className="grid gap-1 text-sm">Acción<CustomSelect className={field} value={action} disabled={busy} onChange={event => { setAction(event.target.value as typeof action); setReservationId(""); }}><option value="apply">Aplicar a deuda</option><option value="reserve">Reservar para esta deuda</option></CustomSelect></label>{action === "apply" && <label className="grid gap-1 text-sm">Origen del importe<CustomSelect className={field} value={reservationId} disabled={busy} onChange={event => { setReservationId(event.target.value); setSelected([]); }}><option value="">Créditos libres seleccionados o automáticos</option>{activeReservations.map(row => <option key={row.id} value={row.id}>Reserva {row.id.slice(0, 8)} · {row.amount}</option>)}</CustomSelect></label>}<label className="grid gap-1 text-sm">Importe (máximo {maximum})<input key={`${sale?.id}:${selected.join(":")}:${reservationId}:${action}:${maximum}`} className={field} name="amount" required type="number" min="0.000001" max={maximum} step="0.000001" defaultValue={Number(maximum) > 0 ? maximum : ""} disabled={busy || !sale} /></label></div>
        {action === "reserve" && <div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Vigencia en horas<input className={field} name="duration_hours" type="number" required min="1" max="2160" defaultValue="168" disabled={busy} /></label><label className="grid gap-1 text-sm">Motivo de la reserva<input className={field} name="reason" required minLength={5} maxLength={2000} disabled={busy} /></label></div>}<p className="text-xs text-slate-500">Si no elige créditos, se consumen primero los que vencen antes. La vigencia de una reserva se limita al vencimiento de sus créditos.</p><button className={button} disabled={busy || loading || !sale || Number(maximum) <= 0}>{action === "reserve" ? "Reservar saldo" : "Aplicar saldo a la venta"}</button></form>}
      <details className="credit-section"><summary><HandCoins size={18} aria-hidden="true" /><span>Anticipos y dinero sin aplicar</span><span className="credit-count">{book.unapplied_payments.length}</span></summary><div className="mt-3 space-y-3"><p className="text-sm text-slate-500">Estos importes corresponden a dinero recibido y aún no aplicado. Se muestran separados del crédito de tienda; sus reembolsos previos y reversos reducen la disponibilidad.</p><div className="flex flex-wrap gap-3">{book.unapplied_balances.map(row => <strong className="rounded-lg border p-3 text-sm" key={row.currency}>{row.currency} {row.available_amount} libres · {row.reserved_amount} reservados</strong>)}</div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Pago", "Comprobante de origen", "Moneda", "Recibido", "Aplicado", "Reembolsado", "Libre", "Reservado"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{book.unapplied_payments.map(row => <tr className="border-t" key={row.id}><td className="p-2">{row.reference_code || row.id.slice(0, 8)} · {row.payment_method}</td><td className="p-2">{row.document_number}</td><td className="p-2">{row.currency}</td><td className="p-2">{row.amount}</td><td className="p-2">{row.allocated_amount}</td><td className="p-2">{row.refunded_amount}</td><td className="p-2">{row.available_amount}</td><td className="p-2">{row.reserved_amount}</td></tr>)}</tbody></table></div>
        {canWrite && canPayments && <form className="space-y-3 rounded-lg border p-3" onSubmit={submitAdvance}><div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Pago con saldo libre<CustomSelect className={field} value={advanceId} required disabled={busy || loading} onChange={event => { setAdvanceId(event.target.value); setAdvanceSale(undefined); setAdvanceReservationId(""); }}><option value="">Seleccione un anticipo</option>{book.unapplied_payments.map(row => <option key={row.id} value={row.id}>{row.document_number} · {row.currency} {row.available_amount} libres / {row.reserved_amount} reservados · {row.reference_code || row.id.slice(0, 8)}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Acción<CustomSelect className={field} value={advanceAction} disabled={busy} onChange={event => { setAdvanceAction(event.target.value as typeof advanceAction); setAdvanceReservationId(""); }}><option value="apply">Aplicar a una deuda del cliente</option><option value="reserve">Reservar para una deuda</option><option value="refund">Devolver el importe sin aplicar</option></CustomSelect></label></div>
          {advance && advanceAction !== "refund" && <RemoteEntitySelect<CreditSale> key={`${customer?.id}:${advance.id}:${localRevision}:${revision}`} value={advanceSale?.id || ""} initialOption={advanceSale ? saleOption(advanceSale) : undefined} onChange={(_, option) => { setAdvanceSale(option?.data); setAdvanceReservationId(""); }} endpoint={`/api/v1/customers/${customer?.id}/store-credit/sales`} queryParams={{ currency: advance.currency }} entityType="sale" mapOption={saleOption} label={`Deuda en ${advance.currency}`} disabled={busy || loading} required />}
          {advance && advanceAction === "apply" && <label className="grid gap-1 text-sm">Origen del importe<CustomSelect className={field} value={advanceReservationId} disabled={busy} onChange={event => setAdvanceReservationId(event.target.value)}><option value="">Dinero libre del anticipo</option>{advanceReservations.map(row => <option key={row.id} value={row.id}>Reserva {row.id.slice(0, 8)} · {row.currency} {row.amount}</option>)}</CustomSelect></label>}
          {advance && advanceAction === "reserve" && <div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Vigencia en horas<input name="duration_hours" className={field} type="number" min="1" max="2160" defaultValue="168" required disabled={busy} /></label><label className="grid gap-1 text-sm">Motivo de la reserva<input name="reason" className={field} minLength={5} maxLength={2000} required disabled={busy} /></label></div>}
          {advance && advanceAction === "refund" && <><p className="text-xs text-slate-500">Registre el dinero que está entregando al cliente. El reintegro usa únicamente la parte libre del pago y conserva lo ya aplicado a ventas.</p>{!refundOptions && <p role="status" className="text-sm">Consultando disponibilidad y cajas autorizadas…</p>}{refundOptions?.payment_method === "CASH" && <label className="grid gap-1 text-sm">Caja que entrega el efectivo<CustomSelect name="cash_session_id" className={field} required disabled={busy}><option value="">Seleccione una caja abierta de la sede y moneda</option>{refundOptions.cash_sessions.map(row => <option key={row.id} value={row.id}>{row.terminal_code} · {advance.currency} {row.balance}</option>)}</CustomSelect></label>}<div className="grid gap-3 md:grid-cols-2"><label className="grid gap-1 text-sm">Referencia de entrega o desembolso<input name="payout_reference" className={field} required minLength={3} maxLength={128} disabled={busy} /></label><label className="grid gap-1 text-sm">Motivo<input name="reason" className={field} required minLength={3} maxLength={255} disabled={busy} /></label></div></>}
          <label className="grid gap-1 text-sm">Importe (máximo {advanceMaximum} {advance?.currency})<input key={`${advanceId}:${advanceAction}:${advanceSale?.id}:${advanceReservationId}:${advanceMaximum}`} className={field} type="number" name="amount" min="0.000001" max={advanceMaximum} step="0.000001" required defaultValue={Number(advanceMaximum) > 0 ? advanceMaximum : ""} disabled={busy || !advance} /></label><button className={button} disabled={busy || loading || Number(advanceMaximum) <= 0 || (advanceAction === "refund" && !refundOptions)}>{advanceAction === "apply" ? "Aplicar anticipo" : advanceAction === "reserve" ? "Reservar anticipo" : "Registrar devolución del anticipo"}</button></form>}
      </div></details>
      <details className="credit-section"><summary><LockKeyhole size={18} aria-hidden="true" /><span>Reservas y liberaciones</span><span className="credit-count">{book.reservations.length}</span></summary><div className="mt-3 space-y-3">{book.reservations.map(row => <article className="rounded-lg border p-3 text-sm" key={row.id}><strong>{row.payment_id ? "Anticipo" : "Crédito de tienda"} · {row.currency} {row.amount} · {row.status}</strong><p>Reserva {row.id} · Venta {row.sale_id}</p><p>{row.reason} · Vence {row.expires_at.slice(0, 19).replace("T", " ")}</p>{canWrite && (row.payment_id ? canPayments : canApply) && row.status === "active" && <form className="mt-2 flex gap-2" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void write(`/api/v1/customer-credit-reservations/${row.id}/release`, { expected_version: row.version, reason: values.reason }, "Reserva liberada. El crédito vuelve a estar disponible según su vencimiento."); }}><input aria-label="Motivo de liberación" className={field} name="reason" placeholder="Motivo de liberación" minLength={5} maxLength={2000} required disabled={busy} /><button className={button} disabled={busy}>Liberar</button></form>}</article>)}</div></details>
      <details className="credit-section"><summary><History size={18} aria-hidden="true" /><span>Movimientos y procedencia</span><span className="credit-count">{movements.length}</span></summary><div className="mt-3 space-y-2">{movements.slice(page * movementPageSize, (page + 1) * movementPageSize).map(row => <article className="rounded-lg border p-3 text-xs" key={row.id}><button className="font-semibold text-teal-800 underline" onClick={() => setDetail(row.id)}>{row.movement_type} · {row.currency || "Moneda por identificar"} {row.amount_delta}</button><p>{row.id} · {row.created_at.slice(0, 19).replace("T", " ")}</p><p>{row.reference_type} · {row.reference_id} · {row.notes}</p>{row.payment_id && <p>Pago aplicado: {row.payment_id}</p>}{canIdentify && !row.currency && <form className="mt-2 grid gap-2 md:grid-cols-4" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void write(`/api/v1/customers/${customer?.id}/store-credit/${row.id}/identify-currency`, { currency: values.currency, expected_amount: row.amount_delta, reason: values.reason, evidence_reference: values.evidence_reference }, "Moneda histórica identificada y justificación registrada."); }}><input aria-label="Moneda del documento original" className={field} name="currency" placeholder="Moneda original" pattern="[A-Z]{3}" maxLength={3} required disabled={busy} /><input aria-label="Documento de respaldo" className={field} name="evidence_reference" placeholder="Documento de respaldo" minLength={5} maxLength={255} required disabled={busy} /><input aria-label="Justificación" className={field} name="reason" placeholder="Justificación" minLength={10} maxLength={2000} required disabled={busy} /><button className={button} disabled={busy}>Identificar moneda</button></form>}</article>)}</div><TablePagination page={page} pageSize={movementPageSize} total={movements.length} loading={loading || busy} onPageChange={setPage} onPageSizeChange={size => { setMovementPageSize(size); setPage(0); }} /></details>
      {customer && <CustomerCreditConversions key={customer.id} customerId={customer.id} currency={currency} sourceIds={selected} canWrite={canWrite && canPayments && !busy && !loading} canManage={canIdentify} revision={revision + localRevision} onChanged={() => { setLocalRevision(value => value + 1); onChanged(); }} />}
      {detail && <article className="space-y-2 rounded-xl border p-4 text-xs"><div className="flex justify-between gap-3"><strong>Procedencia y consumo · {detail}</strong><button className={button} onClick={() => setDetail(null)}>Cerrar</button></div>{book.allocations.filter(row => row.credit_id === detail || row.debit_id === detail).map(row => <p key={`${row.debit_id}:${row.credit_id}`}>Crédito {row.credit_id} → Consumo {row.debit_id} · {row.currency} {row.amount}{row.historical ? " · Reconstrucción histórica por antigüedad" : ""}</p>)}{!book.allocations.some(row => row.credit_id === detail || row.debit_id === detail) && <p>Este movimiento no tiene aplicaciones de consumo registradas.</p>}</article>}
    </>}
  </div></Root>;
}
