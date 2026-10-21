import { Eye, Plus, RefreshCw, Wallet, HandCoins, Receipt, Building2, ChartNoAxesCombined, Send, X, Check, Ban } from "lucide-react";
import { IconAction } from "../../../ui/components/primitives/IconAction";
import "./payables-workspace.css";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { apiClient } from "../../../api/client";
import { SupplierClaimsPanel } from "../../compras/components/SupplierClaimsPanel";
import { SupplierCreditLedger } from "./SupplierCreditLedger";

type Center = { id: string; code: string; name: string };
type Supplier = { id: string; legal_name: string; currency?: string };
type Payable = { id: string; supplier_id: string; supplier_name: string; document_number: string; purchase_order_id: string | null; currency: string; amount: string; paid_amount: string; balance: string; issue_date: string; due_date: string; status: string; version: number; notes: string; installments?: { id: string; sequence: number; due_date: string; amount: string; paid_amount: string }[]; payments?: { id: string; amount: string; date: string; method: string; reference: string; status: string; reversal_reason: string | null }[] };
type InvoiceMatch = { id: string; purchase_order_id: string; supplier_id: string; document_number: string; amount: string; currency: string; payment_terms_days: number };
type Expense = { petty_cash_advance_id: string | null; id: string; title: string; category: string; document_number: string | null; expense_date: string; currency: string; amount: string; status: string; version: number; created_by: string; notes: string; allocations: { cost_center_id: string; amount: string }[] };
type Budget = { id: string; cost_center_id: string; period: string; currency: string; amount: string; consumed: string; remaining: string; version: number };
type Page<T> = { items: T[]; total_count: number };
const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:opacity-50";
const primary = "rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50";
const statusNames: Record<string, string> = { open: "Pendiente", partial: "Parcial", paid: "Pagada", cancelled: "Cancelada", draft: "Borrador", pending: "Por aprobar", approved: "Aprobado", rejected: "Rechazado", posted: "Registrado", reversed: "Revertido" };

function localDate() {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Lima", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
  return ["year", "month", "day"].map(type => parts.find(part => part.type === type)?.value).join("-");
}

function Field({ title, children }: { title: string; children: ReactNode }) {
  return <label className="block text-sm font-medium text-slate-700">{title}{children}</label>;
}

function Dialog({ title, close, busy, children }: { title: string; close: () => void; busy: boolean; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; ref.current?.showModal(); return () => previous?.focus(); }, []);
  return <dialog ref={ref} onCancel={event => { event.preventDefault(); if (!busy) close(); }} className="max-h-[90vh] w-[min(96vw,850px)] rounded-2xl p-0 text-slate-900 shadow-xl backdrop:bg-slate-950/60"><div className="flex items-center justify-between border-b p-5"><h2 className="text-lg font-semibold">{title}</h2><button type="button" className={button} disabled={busy} onClick={close}>Cerrar</button></div><div className="space-y-4 p-5">{children}</div></dialog>;
}

export function FinancialManagementWorkspace({ mode, permissions, userId }: { mode: "payables" | "expenses"; permissions: string[]; userId?: string }) {
  const [creditRevision, setCreditRevision] = useState(0);
  const [balanceSupplierId, setBalanceSupplierId] = useState("");
  const [payables, setPayables] = useState<Payable[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [invoiceMatches, setInvoiceMatches] = useState<InvoiceMatch[]>([]);
  const [payableMatchId, setPayableMatchId] = useState("");
  const selectedInvoiceMatch = invoiceMatches.find(item => item.id === payableMatchId);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<{ id: string; supplier_id: string; label: string }[]>([]);
  const [centers, setCenters] = useState<Center[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [supplierBalances, setSupplierBalances] = useState<{ supplier_id: string; currency: string; balance: string }[]>([]);
  const [balances, setBalances] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [modal, setModal] = useState<"payable" | "expense" | "center" | "budget" | "supplier_balance" | null>(null);
  const [detail, setDetail] = useState<Payable | null>(null);
  const [action, setAction] = useState<{ title: string; path: string; version: number; payment?: boolean } | null>(null);
  const [installments, setInstallments] = useState<{ date: string; amount: string }[]>([]);
  const [allocations, setAllocations] = useState<{ center: string; amount: string }[]>([{ center: "", amount: "" }]);
  const [budgetEdit, setBudgetEdit] = useState<Budget | null>(null);
  const busyRef = useRef(false);
  const pendingKeys = useRef(new Map<string, string>());
  const loadRevision = useRef(0);
  const writeAllowed = permissions.includes("payments:write");
  const canAdmin = permissions.includes("organization:manage");
  const canApprove = permissions.includes("approvals:manage");

  async function load() {
    const revision = ++loadRevision.current;
    setLoading(true);
    setError("");
    try {
      if (mode === "payables") {
        const query = `/api/v1/payables?limit=25&offset=${page * 25}${filter ? `&status=${encodeURIComponent(filter)}` : ""}`;
        const result = await apiClient.request<Page<Payable> & { balances_by_currency: Record<string, string> }>(query);
        if (revision !== loadRevision.current) return;
        setPayables(result.items);
        setCreditRevision(value => value + 1);
        setTotal(result.total_count);
        setBalances(result.balances_by_currency);
        const supplierBalancesResult = await apiClient.request<{ supplier_id: string; currency: string; balance: string }[]>("/api/v1/supplier-balances");
        if (revision === loadRevision.current) setSupplierBalances(supplierBalancesResult);
        if (writeAllowed) {
          const options = await apiClient.request<{ invoice_matches: InvoiceMatch[]; suppliers: Supplier[]; purchase_orders: { id: string; supplier_id: string; label: string }[] }>("/api/v1/payable-options");
          if (revision === loadRevision.current) { setSuppliers(options.suppliers); setPurchaseOrders(options.purchase_orders); setInvoiceMatches(options.invoice_matches || []); }
        }
      } else {
        const [result, centerResult, budgetResult] = await Promise.all([apiClient.request<Page<Expense>>(`/api/v1/expenses?limit=25&offset=${page * 25}`), apiClient.request<Center[]>("/api/v1/cost-centers"), apiClient.request<Budget[]>("/api/v1/cost-budgets")]);
        if (revision !== loadRevision.current) return;
        setExpenses(result.items);
        setTotal(result.total_count);
        setCenters(centerResult);
        setBudgets(budgetResult);
      }
    } catch (failure) { if (revision === loadRevision.current) setError(problem(failure)); }
    finally { if (revision === loadRevision.current) setLoading(false); }
  }

  function problem(failure: unknown) {
    const value = failure as { detail?: unknown; title?: string };
    return typeof value.detail === "string" ? value.detail : value.detail ? JSON.stringify(value.detail) : value.title || "No se pudo completar la operación.";
  }

  useEffect(() => { setPage(0); setFilter(""); setDetail(null); setModal(null); setPayableMatchId(""); }, [mode]);
  useEffect(() => { void load(); return () => { loadRevision.current += 1; }; }, [mode, page, filter]);
  useEffect(() => { if (modal !== "payable") setPayableMatchId(""); }, [modal]);

  async function write(path: string, body: unknown, method = "POST") {
    if (busyRef.current) return false;
    busyRef.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const signature = JSON.stringify({ path, body, method });
    const key = pendingKeys.current.get(signature) || crypto.randomUUID();
    pendingKeys.current.set(signature, key);
    try {
      await apiClient.request(path, { method, headers: { "Idempotency-Key": key }, body: JSON.stringify(body) });
      pendingKeys.current.delete(signature);
      setModal(null);
      setAction(null);
      if (detail) {
        try { setDetail(await apiClient.request<Payable>(`/api/v1/payables/${detail.id}`)); }
        catch { setDetail(null); }
      }
      await load();
      setNotice("Operación registrada.");
      return true;
    } catch (failure) { setError(problem(failure)); return false; }
    finally { setBusy(false); busyRef.current = false; }
  }

  async function openDetail(id: string) {
    setError("");
    try { setDetail(await apiClient.request<Payable>(`/api/v1/payables/${id}`)); }
    catch (failure) { setError(problem(failure)); }
  }

  function formValues(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    return Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
  }

  function submitPayable(event: FormEvent<HTMLFormElement>) {
    const values = formValues(event);
    void write("/api/v1/payables", { ...values, purchase_order_id: selectedInvoiceMatch?.purchase_order_id || values.purchase_order_id || null, invoice_match_id: payableMatchId || null, supplier_id: selectedInvoiceMatch?.supplier_id || values.supplier_id, currency: selectedInvoiceMatch?.currency || values.currency, document_number: selectedInvoiceMatch?.document_number || values.document_number, amount: selectedInvoiceMatch?.amount || values.amount, installments: installments.map(item => ({ due_date: item.date, amount: item.amount })) });
  }

  function submitExpense(event: FormEvent<HTMLFormElement>) {
    const values = formValues(event);
    void write("/api/v1/expenses", { ...values, document_number: values.document_number || null, allocations: allocations.map(item => ({ cost_center_id: item.center, amount: item.amount })) });
  }

  function submitBudget(event: FormEvent<HTMLFormElement>) {
    const values = formValues(event);
    void write("/api/v1/cost-budgets", { ...values, version: budgetEdit?.version || 0 }, "PUT");
  }

  const amountInput = (name: string, value?: string) => <input className={input} name={name} type="number" step="0.000001" min="0.000001" required defaultValue={value} />;
  const currencyInput = (value = "PEN") => <select className={input} name="currency" defaultValue={value}><option value="PEN">PEN</option><option value="USD">USD</option><option value="EUR">EUR</option></select>;
  const centerName = (id: string) => centers.find(center => center.id === id)?.name || id;

  return <div className={`payables-workspace ${mode === "expenses" ? "expenses-workspace" : ""} space-y-5 text-slate-900`}>
    <div className="payables-toolbar flex flex-wrap items-end justify-between gap-4">{mode === "payables" ? <div className="w-full sm:w-64"><Field title="Estado"><CustomSelect className={input} value={filter} onChange={event => { setFilter(event.target.value); setPage(0); }}><option value="">Todos los estados</option>{["open", "partial", "paid", "cancelled"].map(status => <option key={status} value={status}>{statusNames[status]}</option>)}</CustomSelect></Field></div> : <div className="flex items-center gap-3"><span className="financial-section-icon"><Receipt size={22} aria-hidden="true" /></span><span className="text-sm font-semibold">Registro y control de gastos</span></div>}<div className="flex flex-wrap gap-2"><button className={button} disabled={loading || busy} onClick={() => void load()}><RefreshCw size={16} className={loading ? "animate-spin" : ""} />Actualizar</button>{writeAllowed && <button className={primary} disabled={busy} onClick={() => { setError(""); setInstallments([]); setAllocations([{ center: centers[0]?.id || "", amount: "" }]); setModal(mode === "payables" ? "payable" : "expense"); }}><Plus size={16} />{mode === "payables" ? "Nueva obligación" : "Nuevo gasto"}</button>}{mode === "payables" && writeAllowed && <button className={button} disabled={busy} onClick={() => setModal("supplier_balance")}><HandCoins size={16} />Anticipo o crédito</button>}{mode === "expenses" && canAdmin && <><button className={button} onClick={() => setModal("center")}><Building2 size={16} />Nuevo centro</button><button className={button} onClick={() => { setBudgetEdit(null); setModal("budget"); }}><ChartNoAxesCombined size={16} />Nuevo presupuesto</button></>}</div></div>
    {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</p>}
    {notice && <p role="status" className="rounded-xl bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
    {mode === "payables" && <><div className="flex flex-wrap gap-3">{Object.entries(balances).map(([currency, balance]) => <div key={currency} className="rounded-xl border bg-white p-4"><p className="text-xs text-slate-500">Pendiente {currency}</p><strong className="text-xl">{balance}</strong></div>)}</div></>}
    <div className="payables-table overflow-x-auto rounded-2xl border bg-white"><table className="w-full text-left text-sm"><thead className="bg-slate-50"><tr>{(mode === "payables" ? ["Documento", "Proveedor", "Vencimiento final", "Importe", "Pendiente", "Estado", "Acciones"] : ["Gasto", "Categoría", "Fecha", "Importe", "Distribución", "Estado", "Acciones"]).map(title => <th className="p-3" key={title}>{title}</th>)}</tr></thead><tbody>{mode === "payables" ? payables.map(row => <tr key={row.id} className="border-t"><td className="p-3">{row.document_number}</td><td className="p-3">{row.supplier_name}</td><td className="p-3">{row.due_date}</td><td className="p-3">{row.currency} {row.amount}</td><td className="p-3">{row.currency} {row.balance}</td><td className="p-3"><span className={`payables-status payables-status-${row.status}`}>{statusNames[row.status] || row.status}</span></td><td className="p-3"><IconAction label="Ver cuotas y pagos" tone="primary" className="payables-detail-action" onClick={() => void openDetail(row.id)}><Eye aria-hidden="true" /></IconAction></td></tr>) : expenses.map(row => <tr className="border-t" key={row.id}><td className="p-3">{row.title}<p className="text-xs text-slate-500">{row.document_number}</p>{row.petty_cash_advance_id && <p className="text-xs text-teal-700">Rendido mediante caja chica · {row.notes}</p>}</td><td className="p-3">{row.category}</td><td className="p-3">{row.expense_date}</td><td className="p-3">{row.currency} {row.amount}</td><td className="p-3">{row.allocations.map(item => `${centerName(item.cost_center_id)}: ${item.amount}`).join(" · ")}</td><td className="p-3"><span className={`payables-status payables-status-${row.status}`}>{statusNames[row.status] || row.status}</span></td><td className="p-3"><div className="flex justify-end gap-2">{writeAllowed && row.status === "draft" && ["submit", "cancel"].map(operation => <IconAction label={operation === "submit" ? "Enviar gasto a aprobación" : "Cancelar gasto"} tone={operation === "submit" ? "primary" : "danger"} key={operation} onClick={() => setAction({ title: operation === "submit" ? "Enviar gasto a aprobación" : "Cancelar gasto", path: `/api/v1/expenses/${row.id}/${operation}`, version: row.version })}>{operation === "submit" ? <Send aria-hidden="true" /> : <X aria-hidden="true" />}</IconAction>)}{writeAllowed && canApprove && row.status === "pending" && row.created_by !== userId && ["approve", "reject"].map(operation => <IconAction label={operation === "approve" ? "Aprobar gasto" : "Rechazar gasto"} tone={operation === "approve" ? "primary" : "danger"} key={operation} onClick={() => setAction({ title: operation === "approve" ? "Aprobar gasto" : "Rechazar gasto", path: `/api/v1/expenses/${row.id}/${operation}`, version: row.version })}>{operation === "approve" ? <Check aria-hidden="true" /> : <Ban aria-hidden="true" />}</IconAction>)}</div></td></tr>)}</tbody></table>{loading ? <p className="p-4 text-sm" role="status">Cargando…</p> : total === 0 && <div className="payables-empty p-5 text-sm text-slate-500">{mode === "payables" ? <Wallet size={32} aria-hidden="true" /> : <Receipt size={32} aria-hidden="true" />}<p>Todavía no hay registros.</p></div>}</div>
    <div className="payables-pagination flex flex-wrap items-center justify-between gap-3"><span className="text-sm text-slate-500">{total} registros · página {page + 1}</span><div className="flex gap-2"><button className={button} disabled={page === 0 || loading} onClick={() => setPage(value => value - 1)}>Anterior</button><button className={button} disabled={(page + 1) * 25 >= total || loading} onClick={() => setPage(value => value + 1)}>Siguiente</button></div></div>
    {mode === "expenses" && <section className="space-y-3 rounded-xl border bg-white p-5"><h2 className="font-semibold"><ChartNoAxesCombined size={20} className="text-teal-500" aria-hidden="true" />Presupuestos y ejecución</h2>{budgets.length === 0 && <p className="text-sm text-slate-500">No hay presupuestos registrados. Los centros sin presupuesto no tienen un límite configurado.</p>}<div className="grid gap-3 md:grid-cols-2">{budgets.map(row => <div className="rounded-lg border p-4" key={row.id}><strong>{centerName(row.cost_center_id)} · {row.period}</strong><p className="mt-2 text-sm">Presupuesto: {row.currency} {row.amount}</p><p className="text-sm">Aprobado: {row.currency} {row.consumed}</p><p className="text-sm">Disponible: {row.currency} {row.remaining}</p>{canAdmin && <button className={`${button} mt-3`} onClick={() => { setBudgetEdit(row); setModal("budget"); }}>Revisar presupuesto</button>}</div>)}</div><h3 className="font-medium">Centros registrados</h3><div className="financial-centers">{centers.length ? centers.map(center => <div key={center.id} className="financial-center"><Building2 size={18} aria-hidden="true" /><div><strong>{center.name}</strong><p className="text-xs text-slate-500">{center.code}</p></div></div>) : <p className="text-sm text-slate-500">Crea un centro para distribuir los gastos.</p>}</div></section>}
    {mode === "payables" && <><SupplierCreditLedger revision={creditRevision} /><SupplierClaimsPanel onChanged={() => { void load(); }} /></>}
    {modal && <Dialog title={{ payable: "Nueva obligación", expense: "Nuevo gasto", center: "Nuevo centro de costo", budget: "Presupuesto mensual", supplier_balance: "Anticipo, crédito o reintegro de proveedor" }[modal]} close={() => setModal(null)} busy={busy}>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {modal === "payable" && <><Field title="Factura conciliada de compra"><select className={input} value={payableMatchId} onChange={event => { setPayableMatchId(event.target.value); setInstallments([]); }}><option value="">Obligación independiente de una compra</option>{invoiceMatches.map(item => <option key={item.id} value={item.id}>{item.document_number} · {suppliers.find(supplier => supplier.id === item.supplier_id)?.legal_name} · {item.currency} {item.amount}</option>)}</select></Field><p className="text-xs text-slate-500">Para vincular una compra selecciona su factura conciliada. El importe y los datos del proveedor se conservan.</p><form key={payableMatchId || "independent"} className="space-y-4" onSubmit={submitPayable}><Field title="Proveedor"><CustomSelect remote={{ resource: "suppliers" }} className={input} required name="supplier_id" defaultValue={selectedInvoiceMatch?.supplier_id} disabled={Boolean(selectedInvoiceMatch)}><option value="">Seleccionar proveedor</option>{suppliers.map(supplier => <option key={supplier.id} value={supplier.id}>{supplier.legal_name}</option>)}</CustomSelect></Field><div className="grid gap-4 sm:grid-cols-2"><Field title="Número de documento"><input className={input} name="document_number" defaultValue={selectedInvoiceMatch?.document_number} readOnly={Boolean(selectedInvoiceMatch)} required maxLength={128} /></Field><Field title="Orden de compra vinculada"><select className={input} name="purchase_order_id" defaultValue={selectedInvoiceMatch?.purchase_order_id} disabled={Boolean(selectedInvoiceMatch)}><option value="">Sin vinculación</option>{purchaseOrders.map(order => <option key={order.id} value={order.id}>{order.label} · {suppliers.find(supplier => supplier.id === order.supplier_id)?.legal_name}</option>)}</select></Field><Field title="Moneda">{selectedInvoiceMatch ? <input className={input} name="currency" readOnly value={selectedInvoiceMatch.currency} /> : currencyInput()}</Field><Field title="Importe total">{selectedInvoiceMatch ? <input className={input} name="amount" readOnly value={selectedInvoiceMatch.amount} /> : amountInput("amount")}</Field><Field title="Fecha de emisión"><input className={input} name="issue_date" required type="date" defaultValue={localDate()} /></Field><Field title="Vencimiento"><input className={input} name="due_date" required type="date" defaultValue={localDate()} /></Field></div><Field title="Notas"><textarea className={input} name="notes" maxLength={4000} /></Field><fieldset className="space-y-3 rounded-lg border p-3"><legend className="px-2 text-sm font-medium">Cuotas opcionales</legend><p className="text-xs text-slate-500">Sin cuotas se crea un único vencimiento. La suma de cuotas debe coincidir con el total.</p>{installments.map((item, index) => <div className="grid grid-cols-[1fr_1fr_auto] gap-2" key={index}><input aria-label={`Vencimiento cuota ${index + 1}`} className={input} type="date" required value={item.date} onChange={event => setInstallments(rows => rows.map((row, position) => position === index ? { ...row, date: event.target.value } : row))} /><input aria-label={`Importe cuota ${index + 1}`} className={input} type="number" min="0.000001" step="0.000001" required value={item.amount} onChange={event => setInstallments(rows => rows.map((row, position) => position === index ? { ...row, amount: event.target.value } : row))} /><button className={button} type="button" onClick={() => setInstallments(rows => rows.filter((_, position) => position !== index))}>Quitar</button></div>)}<button className={button} type="button" onClick={() => setInstallments(rows => [...rows, { date: localDate(), amount: "" }])}>Agregar cuota</button></fieldset><button className={primary} disabled={busy}>Registrar obligación</button></form></>}
      {modal === "expense" && <form className="space-y-4" onSubmit={submitExpense}><div className="grid gap-4 sm:grid-cols-2"><Field title="Concepto"><input className={input} name="title" required minLength={3} maxLength={255} /></Field><Field title="Categoría"><input className={input} name="category" required minLength={2} maxLength={128} /></Field><Field title="Documento de referencia"><input className={input} name="document_number" maxLength={128} /></Field><Field title="Fecha del gasto"><input className={input} name="expense_date" type="date" required defaultValue={localDate()} /></Field><Field title="Moneda">{currencyInput()}</Field><Field title="Importe">{amountInput("amount")}</Field></div><Field title="Notas"><textarea className={input} name="notes" maxLength={4000} /></Field><fieldset className="space-y-2 rounded-lg border p-3"><legend className="px-2 text-sm">Distribución por centro de costo</legend>{allocations.map((item, index) => <div key={index} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2"><Field title="Centro"><select className={input} required value={item.center} onChange={event => setAllocations(rows => rows.map((row, position) => position === index ? { ...row, center: event.target.value } : row))}><option value="">Seleccionar</option>{centers.map(center => <option key={center.id} value={center.id}>{center.code} · {center.name}</option>)}</select></Field><Field title="Importe asignado"><input className={input} type="number" required min="0.000001" step="0.000001" value={item.amount} onChange={event => setAllocations(rows => rows.map((row, position) => position === index ? { ...row, amount: event.target.value } : row))} /></Field><button type="button" className={button} disabled={allocations.length === 1} onClick={() => setAllocations(rows => rows.filter((_, position) => position !== index))}>Quitar</button></div>)}<button type="button" className={button} onClick={() => setAllocations(rows => [...rows, { center: "", amount: "" }])}>Agregar distribución</button></fieldset><button className={primary} disabled={busy || centers.length === 0}>Guardar borrador</button></form>}
      {modal === "supplier_balance" && <form className="space-y-4" onSubmit={event => { const values = formValues(event); void write("/api/v1/supplier-balances", { ...values, source_document_id: values.source_document_id || null }); }}><Field title="Proveedor"><CustomSelect remote={{ resource: "suppliers" }} className={input} name="supplier_id" required value={balanceSupplierId} onChange={event => setBalanceSupplierId(event.target.value)}><option value="">Seleccionar</option>{suppliers.map(supplier => <option key={supplier.id} value={supplier.id}>{supplier.legal_name}</option>)}</CustomSelect></Field><Field title="Compra vinculada (opcional)"><select className={input} name="source_document_id" key={balanceSupplierId}><option value="">Sin compra específica</option>{purchaseOrders.filter(order => order.supplier_id === balanceSupplierId).map(order => <option key={order.id} value={order.id}>{order.label}</option>)}</select></Field><Field title="Movimiento"><select className={input} name="kind"><option value="advance">Anticipo entregado</option><option value="credit">Crédito reconocido por proveedor</option><option value="refund">Reintegro recibido del proveedor</option></select></Field><Field title="Moneda">{currencyInput()}</Field><Field title="Importe">{amountInput("amount")}</Field><Field title="Fecha"><input className={input} required type="date" name="movement_date" defaultValue={localDate()} /></Field><Field title="Referencia"><input className={input} required name="reference" maxLength={128} /></Field><Field title="Justificación"><textarea className={input} required name="notes" minLength={3} maxLength={2000} /></Field><button className={primary} disabled={busy}>Registrar movimiento</button></form>}
      {modal === "center" && <form className="space-y-4" onSubmit={event => { const values = formValues(event); void write("/api/v1/cost-centers", values); }}><Field title="Código"><input className={input} name="code" required pattern="[A-Za-z0-9_-]+" maxLength={64} /></Field><Field title="Nombre"><input className={input} name="name" required minLength={2} maxLength={255} /></Field><button className={primary} disabled={busy}>Crear centro</button></form>}
      {modal === "budget" && <form className="space-y-4" onSubmit={submitBudget}><Field title="Centro de costo"><select className={input} name="cost_center_id" defaultValue={budgetEdit?.cost_center_id || ""} required><option value="">Seleccionar</option>{centers.map(center => <option key={center.id} value={center.id}>{center.name}</option>)}</select></Field><Field title="Mes"><input className={input} name="period" type="month" required defaultValue={budgetEdit?.period || localDate().slice(0, 7)} /></Field><Field title="Moneda">{currencyInput(budgetEdit?.currency)}</Field><Field title="Presupuesto"><input className={input} name="amount" type="number" min="0" step="0.000001" required defaultValue={budgetEdit?.amount} /></Field><button className={primary} disabled={busy || centers.length === 0}>Guardar presupuesto</button></form>}
    </Dialog>}
    {detail && !action && <Dialog title={`${detail.document_number} · ${detail.supplier_name}`} close={() => setDetail(null)} busy={busy}><p className="text-sm">{statusNames[detail.status]} · saldo {detail.currency} {detail.balance}</p><p className="text-sm text-slate-600">Saldo general a favor (los anticipos vinculados se limitan a su compra): {detail.currency} {supplierBalances.find(item => item.supplier_id === detail.supplier_id && item.currency === detail.currency)?.balance || "0"}</p><h3 className="font-medium">Cuotas</h3>{detail.installments?.map(item => <div key={item.id} className="flex flex-wrap justify-between gap-2 rounded-lg border p-3 text-sm"><span>Cuota {item.sequence} · {item.due_date}</span><span>{detail.currency} {item.amount} · aplicado {item.paid_amount}</span></div>)}<h3 className="font-medium">Pagos</h3>{detail.payments?.map(item => <div key={item.id} className="rounded-lg border p-3 text-sm"><p>{item.date} · {detail.currency} {item.amount} · {item.method} · {item.reference} · {statusNames[item.status]}</p>{item.reversal_reason && <p>{item.reversal_reason}</p>}{writeAllowed && item.status === "posted" && <button className={`${button} mt-2`} onClick={() => setAction({ title: "Revertir pago", path: `/api/v1/payables/${detail.id}/payments/${item.id}/reverse`, version: detail.version })}>Revertir con motivo</button>}</div>)}{detail.payments?.length === 0 && <p className="text-sm text-slate-500">Sin pagos registrados.</p>}{writeAllowed && ["open", "partial"].includes(detail.status) && <button className={primary} onClick={() => setAction({ title: "Registrar pago manual", path: `/api/v1/payables/${detail.id}/payments`, version: detail.version, payment: true })}>Registrar pago</button>}{writeAllowed && detail.status === "open" && <button className={`${button} ml-2`} onClick={() => setAction({ title: "Cancelar obligación", path: `/api/v1/payables/${detail.id}/cancel`, version: detail.version })}>Cancelar obligación</button>}</Dialog>}
    {action && <Dialog title={action.title} close={() => setAction(null)} busy={busy}>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}<form className="space-y-4" onSubmit={event => { const values = formValues(event); void write(action.path, { ...values, version: action.version }); }}>{action.payment ? <><Field title={`Importe en ${detail?.currency || "la moneda de la obligación"}`}>{amountInput("amount")}</Field><Field title="Fecha de pago"><input className={input} name="payment_date" type="date" required defaultValue={localDate()} /></Field><Field title="Medio"><select className={input} name="method"><option value="MANUAL_TRANSFER">Transferencia registrada manualmente</option><option value="CASH">Efectivo registrado manualmente</option><option value="OTHER">Otro</option><option value="SUPPLIER_CREDIT">Aplicar anticipo o crédito disponible</option></select></Field><Field title="Referencia"><input className={input} name="reference" required maxLength={128} /></Field></> : <Field title="Motivo"><textarea className={input} name="reason" required minLength={3} maxLength={2000} /></Field>}<button className={primary} disabled={busy}>Confirmar</button></form></Dialog>}
  </div>;
}
