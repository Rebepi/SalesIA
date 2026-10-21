import { ModalSurface } from "../../../ui/components/ModalSurface";
import { TablePagination } from "../../../ui/components/TablePagination";
import { getDefaultPageSize, setDefaultPageSize as persistDefaultPageSize } from "../../../ui/preferences";
import { IconAction } from "../../../ui/components/primitives/IconAction";
import { Eye, ReceiptText, ArrowRightLeft, Check, X } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Movement = { id: string; kind: string; reference_id: string; amount: string; currency: string; details: Record<string, unknown>; created_at: string; legacy: boolean };
type Settlement = { can_grant_store_credit: boolean; return_id: string; sale_id: string; document_number?: string; reason?: string; currency: string; available_amount: string; remaining_financial_amount: string; applied_amount: string; sale_balance: string; debt_to_offset: string; can_settle: boolean; valuation: { refundable_total: string; retained_total: string }; movements: Movement[]; warnings: string[] };
const labels: Record<string, string> = { debt_offset: "Aplicación a deuda original", store_credit: "Saldo a favor otorgado", exchange: "Aplicación al cambio", refund: "Reembolso monetario" };
const field = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo completar la liquidación de la devolución."; }

export function ReturnSettlementPanel({ canWrite, revision, onChanged, standalone = false, initialReturnId = "" }: { standalone?: boolean; initialReturnId?: string; canWrite: boolean; revision: number; onChanged: () => void }) {
  const modalTitleId = useId();
  const closeDetail = () => { if (lock.current) return; detailVersion.current += 1; setDetail(null); };
  const [rows, setRows] = useState<Settlement[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(getDefaultPageSize);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<Settlement | null>(null);
  const [localRevision, setLocalRevision] = useState(0);
  const [action, setAction] = useState<"store-credit" | "settle-debt">("store-credit");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  const detailVersion = useRef(0);
  const detailId = useRef<string | null>(null);
  detailId.current = detail?.return_id || null;
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const query = new URLSearchParams({ limit: String(pageSize), offset: String(page * pageSize), search });
    const version = ++detailVersion.current;
    const identifier = detailId.current;
    void Promise.all([
      apiClient.request<{ items: Settlement[]; total_count: number }>(`/api/v1/return-settlements?${query}`, { signal: controller.signal }),
      identifier ? apiClient.request<Settlement>(`/api/v1/return-settlements/${identifier}`, { signal: controller.signal }) : Promise.resolve(null)
    ]).then(([result, current]) => { if (controller.signal.aborted) return; setRows(result.items); setTotal(result.total_count); if (current && version === detailVersion.current) setDetail(current); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [page, pageSize, search, revision, localRevision]);
  useEffect(() => () => { detailVersion.current += 1; }, []);
  async function open(identifier: string) {
    const version = ++detailVersion.current;
    try { const result = await apiClient.request<Settlement>(`/api/v1/return-settlements/${identifier}`); if (version === detailVersion.current) { setDetail(result); setAction(Number(result.debt_to_offset) > 0 ? "settle-debt" : "store-credit"); } }
    catch (cause) { if (version === detailVersion.current) setError(problem(cause)); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail || lock.current) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const body = JSON.stringify({ reason: values.reason, expected_available: detail.available_amount, ...(action === "store-credit" ? { amount: values.amount } : {}) });
    const signature = `${detail.return_id}:${action}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await apiClient.request<Settlement>(`/api/v1/return-settlements/${detail.return_id}/${action}`, { method: "POST", headers: { "Idempotency-Key": key }, body });
      keys.current.delete(signature);
      detailVersion.current += 1;
      setDetail(result);
      setNotice("Aplicación registrada. El valor utilizado deja de estar disponible para cambios o reembolsos.");
      setLocalRevision(value => value + 1);
      onChanged();
    } catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  useEffect(() => { if (initialReturnId) void open(initialReturnId); }, [initialReturnId]);
  const displayAmount = (value: string) => new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value));
  const Root = standalone ? "section" : "details";
  return <Root className={standalone ? "refund-submodule settlement-workspace" : "refund-submodule rounded-2xl border border-slate-200 bg-white p-5"}>
    {!standalone && <summary className="cursor-pointer font-semibold">Liquidación de devoluciones, cambios y saldos</summary>}
    <div className={standalone ? "space-y-5" : "mt-4 space-y-5"}>
    <div className="settlement-overview space-y-4">
      {standalone && <h2 className="font-semibold">Liquidación de devoluciones, cambios y saldos</h2>}
    <p className="text-sm text-slate-500">La devolución conserva un único valor después de retenciones. Se aplica primero a la deuda de la venta y el resto puede usarse para un cambio, saldo a favor o reembolso. Para comprar artículos con series, lotes o kits, otorgue el saldo a favor y aplíquelo a una nueva venta en la misma moneda con sus condiciones completas. Puede consultar sus orígenes y aplicaciones en el libro de créditos del cliente.</p>
    <div className="flex gap-3"><input aria-label="Buscar devolución o serie de venta" className={field} value={search} onChange={event => { setSearch(event.target.value); setPage(0); }} placeholder="Devolución, serie o motivo" /><button className={button} disabled={busy} onClick={() => setLocalRevision(value => value + 1)}>Actualizar</button></div>
    </div>
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    <div className="settlement-table-card overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Devolución", "Venta", "Valor tras retenciones", "Aplicado", "Disponible", "Detalle"].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.return_id} className="border-t"><td className="p-2">{row.return_id.slice(0, 8)}</td><td className="p-2">{row.document_number}</td><td className="p-2">{row.currency} {row.valuation.refundable_total}</td><td className="p-2">{row.applied_amount}</td><td className="p-2">{row.remaining_financial_amount}{row.warnings.length > 0 && <p className="text-xs text-amber-800">Requiere conciliación</p>}</td><td className="p-2"><IconAction label="Ver liquidación" tone="primary" disabled={busy} onClick={() => void open(row.return_id)}><Eye aria-hidden="true" /></IconAction></td></tr>)}</tbody></table>{rows.length === 0 && <p className="p-3 text-sm text-slate-500">No hay devoluciones aceptadas para estos filtros.</p>}</div>
    <TablePagination page={page} pageSize={pageSize} total={total} loading={loading || busy} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); persistDefaultPageSize(size); setPage(0); }} />
    {detail && <ModalSurface labelledBy={modalTitleId} onClose={closeDetail} blocked={busy} className="settlement-dialog w-[min(94vw,820px)]">
      <article className="app-modal-panel settlement-modal">
        <header className="settlement-modal-header">
          <span className="settlement-modal-symbol"><ReceiptText size={22} aria-hidden="true" /></span>
          <div className="min-w-0 flex-1"><h3 id={modalTitleId}>Liquidación de devolución</h3><p>{detail.document_number || `Devolución ${detail.return_id.slice(0, 8).toUpperCase()}`} · {detail.currency}</p></div>
          <IconAction label="Cerrar detalle" disabled={busy} onClick={closeDetail}><X aria-hidden="true" /></IconAction>
        </header>
        <div className="settlement-modal-body">
          {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">{error}</p>}
          {notice && <p role="status" className="rounded-xl bg-teal-50 p-3 text-sm text-teal-700 dark:bg-teal-950/40 dark:text-teal-300">{notice}</p>}
          <div className="settlement-metrics">
            {[["Valor devuelto", detail.valuation.refundable_total], ["Retenciones", detail.valuation.retained_total], ["Valor aplicado", detail.applied_amount]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{detail.currency} {displayAmount(value)}</strong></div>)}
          </div>
          <div className="settlement-balances">
            <div><span>Deuda original por compensar</span><strong>{detail.currency} {displayAmount(detail.debt_to_offset)}</strong></div>
            <div><span>Disponible para cambio, saldo o reembolso</span><strong>{detail.currency} {displayAmount(detail.remaining_financial_amount)}</strong></div>
          </div>
          {!detail.can_grant_store_credit && <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">La devolución requiere revisar sus condiciones antes de otorgar saldo a favor.</p>}
          {detail.warnings.map((warning, index) => <p key={index} className="text-sm text-rose-600 dark:text-rose-300">{warning}</p>)}
          {canWrite && detail.can_settle && Number(detail.available_amount) > 0 && <form id={`${modalTitleId}-form`} className="settlement-application" key={`${detail.return_id}:${detail.available_amount}`} onSubmit={submit}>
            <h4><ArrowRightLeft size={18} aria-hidden="true" />Aplicar valor de la devolución</h4>
            <label className="grid gap-2 text-sm font-medium">Acción<CustomSelect className={field} value={action} onChange={event => setAction(event.target.value as typeof action)} disabled={busy}><option value="store-credit">Otorgar saldo a favor</option>{Number(detail.debt_to_offset) > 0 && <option value="settle-debt">Compensar deuda de la venta original</option>}</CustomSelect></label>
            {action === "store-credit" && <label className="grid gap-2 text-sm font-medium">Importe a convertir en saldo ({detail.currency})<input className={field} type="number" name="amount" required min="0.000001" max={detail.remaining_financial_amount} step="0.000001" defaultValue={detail.remaining_financial_amount} disabled={busy || !detail.can_grant_store_credit || Number(detail.remaining_financial_amount) <= 0} /></label>}
            <label className="grid gap-2 text-sm font-medium">Motivo y sustento<textarea className={field} rows={3} placeholder="Describe el motivo y el sustento de esta aplicación" required name="reason" minLength={5} maxLength={2000} disabled={busy} /></label>
          </form>}
          {detail.movements.length > 0 && <details className="settlement-history"><summary>Aplicaciones registradas ({detail.movements.length})</summary><div className="mt-3 space-y-3">{detail.movements.map(item => <div className="rounded-xl border border-slate-200 p-3 text-sm" key={`${item.kind}:${item.id}`}><strong>{labels[item.kind] || item.kind} · {item.currency} {displayAmount(item.amount)}</strong><p className="mt-1 text-xs text-slate-500">{item.created_at.slice(0, 19).replace("T", " ")} · Referencia {item.reference_id}{item.legacy ? " · Origen histórico" : ""}</p></div>)}</div></details>}
          <details className="settlement-reference"><summary>Referencia completa de la devolución</summary><p className="mt-2 break-all font-mono text-xs">{detail.return_id}</p></details>
        </div>
        <footer className="settlement-modal-footer">
          <button type="button" className="settlement-secondary" disabled={busy} onClick={closeDetail}>Cerrar</button>
          {canWrite && detail.can_settle && Number(detail.available_amount) > 0 && <button type="submit" form={`${modalTitleId}-form`} className="settlement-primary" disabled={busy || (action === "store-credit" && (!detail.can_grant_store_credit || Number(detail.remaining_financial_amount) <= 0))}><Check size={17} aria-hidden="true" />{busy ? "Registrando…" : "Registrar aplicación"}</button>}
        </footer>
      </article>
    </ModalSurface>}
  </div></Root>;
}
