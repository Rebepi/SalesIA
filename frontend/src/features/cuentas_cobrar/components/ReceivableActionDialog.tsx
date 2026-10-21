import { ReceivableInstallmentsPanel, type ReceivableSchedule } from "./ReceivableInstallmentsPanel";
import { CollectionAgreementsPanel, type CollectionAgreement } from "./CollectionAgreementsPanel";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { FormEvent, useEffect, useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { PosPaymentEditor, CheckoutPayment } from "../../ventas/components/PosPaymentEditor";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useToast } from "../../../ui/toast/ToastContext";
import { useConfirm } from "../../../ui/components/ConfirmDialog";

interface DebtContext {
  sale_id: string; document: string; customer_name: string; customer_code: string; currency: string; branch_id: string; total_amount: string; paid_amount: string; balance_due: string;
  payments: Array<{ date: string; amount: string; method: string; reference?: string; status: string }>;
  credit_notes: Array<{ document: string; amount: string; status: string }>;
  sale_version: number;
  installment_schedule: ReceivableSchedule | null;
  agreements: CollectionAgreement[];
  activities: Array<{ id: string; kind: string; notes: string; responsible: string; created_at: string; next_action_at?: string; promised_amount?: string }>;
}
const labels: Record<string, string> = { contact: "Contacto realizado", dispute: "Disputa de deuda", promise: "Promesa de pago", agreement: "Acuerdo de pago", reminder: "Recordatorio interno" };

export function ReceivableActionDialog({ saleId, mode, canWrite, onClose, onSaved }: { saleId: string; mode: "payment" | "activity" | "context"; canWrite: boolean; onClose: () => void; onSaved: () => void }) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [context, setContext] = useState<DebtContext | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [installmentTargets, setInstallmentTargets] = useState<{ installment_id: string; amount: string }[]>([]);
  const [payments, setPayments] = useState<CheckoutPayment[]>([]);
  const [valid, setValid] = useState(false);
  const [kind, setKind] = useState("contact");
  const [paymentKey] = useState(() => crypto.randomUUID());
  const toast = useToast();
  useEffect(() => { apiClient.request<DebtContext>(`/api/v1/receivables/${saleId}/context`).then(setContext).catch(failure => setError(String(failure?.detail || "No se pudo cargar el detalle de la deuda."))); }, [saleId]);
  const money = (amount: string | number) => new Intl.NumberFormat("es-PE", { style: "currency", currency: context?.currency || "PEN" }).format(Number(amount));
  async function collect() {
    if (!context || !valid || payments.length !== 1 || !canWrite || busy) return;
    const payment = payments[0];
    if (installmentTargets.length && Math.abs(installmentTargets.reduce((sum, item) => sum + Number(item.amount || 0), 0) - Number(payment.amount)) > 0.0000001) { setError("Distribuye exactamente el importe del abono entre las cuotas seleccionadas."); return; }
    if (!await confirm({ title: "¿Confirmar cobro?", text: `Se registrará un cobro de ${money(payment.amount)} para ${context.document}. El saldo se reducirá y el pago quedará en el historial.`, confirmLabel: "Registrar cobro" })) return;
    setBusy(true);
    setError("");
    try {
      await apiClient.request("/api/v1/payments", { method: "POST", headers: { "Idempotency-Key": paymentKey }, body: JSON.stringify({ installment_targets: installmentTargets, schedule_version: context.installment_schedule?.version, sale_id: saleId, amount: payment.amount, currency: context.currency, payment_method: payment.method, reference_code: payment.referenceCode || null, cash_session_id: payment.cashSessionId || null, cash_tendered: payment.method === "CASH" ? payment.cashTendered : undefined, require_cash_session: payment.method === "CASH" }) });
      toast.success("Cobro registrado", "El saldo y los movimientos del documento fueron actualizados.");
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo confirmar el cobro. Revisa los pagos del documento antes de volver a intentar.")); }
    finally { setBusy(false); }
  }
  async function activity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canWrite || busy) return;
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      await apiClient.request(`/api/v1/receivables/${saleId}/activities`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ adjust_to_operating_calendar: data.get("adjust_to_operating_calendar") === "on", kind, notes: String(data.get("notes") || ""), promised_amount: data.get("promised_amount") || null, next_action_at: data.get("next_action_at") ? new Date(String(data.get("next_action_at"))).toISOString() : null }) });
      toast.success("Gestión registrada", "El seguimiento quedó en el historial. Si indicaste fecha, se creó una tarea en Mi trabajo.");
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo registrar la gestión. Revisa los campos.")); }
    finally { setBusy(false); }
  }
  return (
    <>
      <ModalSurface labelledBy="debt-title" onClose={onClose} blocked={busy}><section className="app-modal-panel max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><header className="mb-4 flex justify-between"><h3 id="debt-title" className="font-bold">{mode === "payment" ? "Cobrar cuenta pendiente" : mode === "activity" ? "Gestionar cobranza" : "Detalle de la deuda"}</h3><button type="button" disabled={busy} onClick={onClose} aria-label="Cerrar detalle de cobranza"><X className="h-5 w-5" /></button></header>{error && <p role="alert" className="mb-3 rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}{!context && !error && <p role="status" className="text-sm">Cargando comprobante y movimientos…</p>}{context && <><div className="mb-5 rounded-xl bg-slate-50 p-4 text-sm dark:bg-slate-800"><strong>{context.customer_name} · {context.customer_code}</strong><p>{context.document}</p><dl className="mt-3 grid grid-cols-3 gap-2 text-xs"><div><dt>Total</dt><dd>{money(context.total_amount)}</dd></div><div><dt>Pagado</dt><dd>{money(context.paid_amount)}</dd></div><div><dt>Pendiente</dt><dd className="font-bold">{money(context.balance_due)}</dd></div></dl></div>
        <ReceivableInstallmentsPanel saleId={saleId} saleVersion={context.sale_version} currency={context.currency} balance={context.balance_due} schedule={context.installment_schedule} canWrite={canWrite && !busy && mode !== "payment"} onBusyChange={setBusy} onChanged={installment_schedule => { setContext(previous => previous ? { ...previous, installment_schedule } : previous); setInstallmentTargets([]); }} />
        {mode !== "payment" && <CollectionAgreementsPanel saleId={saleId} currency={context.currency} balance={context.balance_due} agreements={context.agreements || []} canWrite={canWrite && !busy} onBusyChange={setBusy} onChanged={agreements => setContext(previous => previous ? { ...previous, agreements } : previous)} />}
        {mode === "payment" && <div className="space-y-4"><p className="text-xs text-slate-500">Puedes cobrar el saldo completo o editar el importe para registrar un pago parcial. Registra cada medio de pago por separado.</p><PosPaymentEditor total={Number(context.balance_due)} currency={context.currency} branchId={context.branch_id} disabled={busy || !canWrite} onChange={(items, isValid) => { setPayments(items); setValid(isValid && items.length === 1); }} />{context.installment_schedule && <div className="space-y-3 rounded-lg border p-3"><div className="flex flex-wrap items-center justify-between gap-2"><h4 className="text-sm font-medium">Cuotas a las que se aplicará este abono</h4><button type="button" disabled={busy || !canWrite || installmentTargets.length >= context.installment_schedule.items.length} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50" onClick={() => setInstallmentTargets(previous => [...previous, { installment_id: "", amount: "" }])}>Seleccionar cuota</button></div>{!installmentTargets.length && <p className="text-xs text-slate-500">El abono se aplicará primero a las cuotas con vencimiento más antiguo.</p>}{installmentTargets.map((target, index) => <div key={index} className="flex flex-wrap gap-2"><select aria-label={`Cuota del abono ${index + 1}`} value={target.installment_id} disabled={busy} className="grow rounded-lg border p-2 text-sm" onChange={event => setInstallmentTargets(previous => previous.map((item, position) => position === index ? { ...item, installment_id: event.target.value } : item))}><option value="">Seleccionar cuota</option>{context.installment_schedule?.items.filter(item => Number(item.balance) > 0).map(item => <option key={item.id} value={item.id}>Cuota {item.sequence} · {item.due_date} · Saldo {item.balance}</option>)}</select><input aria-label={`Importe aplicado a cuota ${index + 1}`} className="rounded-lg border p-2 text-sm" type="number" min="0.000001" step="0.000001" value={target.amount} disabled={busy} onChange={event => setInstallmentTargets(previous => previous.map((item, position) => position === index ? { ...item, amount: event.target.value } : item))} /><button type="button" className="rounded-lg border px-3 py-2 text-sm" disabled={busy} onClick={() => setInstallmentTargets(previous => previous.filter((_, position) => position !== index))}>Quitar</button></div>)}</div>}<button type="button" disabled={!valid || busy || !canWrite || installmentTargets.some(item => !item.installment_id || !item.amount)} onClick={collect} className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Registrando…" : `Confirmar cobro${payments[0] ? ` de ${money(payments[0].amount)}` : ""}`}</button></div>}
        {mode === "activity" && <form onSubmit={activity} className="space-y-3"><label className="block text-xs font-semibold">Tipo de gestión<CustomSelect value={kind} onChange={event => setKind(event.target.value)} className="mt-1 w-full rounded-xl border p-2.5">{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="block text-xs font-semibold">Detalle<textarea name="notes" required minLength={3} maxLength={2000} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label>{["promise", "agreement"].includes(kind) && <label className="block text-xs font-semibold">Importe comprometido ({context.currency})<input name="promised_amount" type="number" min="0.000001" max={context.balance_due} step="0.000001" required className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label>}<label className="block text-xs font-semibold">Próxima gestión<input name="next_action_at" type="datetime-local" required={["promise", "agreement"].includes(kind)} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label><label className="flex items-center gap-2 text-xs"><input type="checkbox" name="adjust_to_operating_calendar" />Ajustar la próxima gestión al calendario de la sede y conservar la regla aplicada</label><button type="submit" disabled={busy || !canWrite} className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">Guardar gestión</button></form>}
        {mode === "context" && <div className="space-y-5 text-xs"><section><h4 className="mb-2 font-bold">Historial de pagos</h4>{context.payments.length ? context.payments.map((payment, index) => <div key={index} className="flex flex-wrap justify-between gap-2 border-t py-2"><span>{new Date(payment.date).toLocaleString("es-PE", { timeZone: "America/Lima" })} · {payment.method} · {payment.status}</span><strong>{money(payment.amount)}</strong><span>{payment.reference}</span></div>) : <p>Sin pagos registrados.</p>}</section><section><h4 className="mb-2 font-bold">Notas de crédito</h4>{context.credit_notes.map(note => <p key={note.document}>{note.document} · {money(note.amount)} · {note.status}</p>)}{!context.credit_notes.length && <p>Sin notas de crédito.</p>}</section><section><h4 className="mb-2 font-bold">Gestiones y compromisos</h4>{context.activities.map(item => <article key={item.id} className="mb-2 rounded-xl border p-3"><strong>{labels[item.kind] || item.kind}</strong><p>{item.notes}</p><p className="mt-1 text-slate-500">{item.responsible} · {new Date(item.created_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</p>{item.promised_amount && <p>Compromiso: {money(item.promised_amount)}</p>}{item.next_action_at && <p>Próxima gestión: {new Date(item.next_action_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</p>}</article>)}{!context.activities.length && <p>Sin gestiones registradas.</p>}</section></div>}</>}</section></ModalSurface>
      {ConfirmDialogNode}
    </>
  );
}
