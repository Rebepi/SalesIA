import { useEffect, useState } from "react";
import "./refund-submodules.css";
import { ReturnSettlementPanel } from "./ReturnSettlementPanel";
import { CustomerCreditPanel } from "./CustomerCreditPanel";
import { Panel1 } from "../sections/RefundsWorkspaceTab/Panel1";
import { Panel2 } from "../sections/RefundsWorkspaceTab/Panel2";
import { SeccionUpdate_status } from "../sections/RefundsWorkspaceTab/SeccionUpdate_status";
export type { RefundItem } from "../types/RefundsWorkspaceTab";
export type { RefundsWorkspaceTabProps } from "../types/RefundsWorkspaceTab";
import { useRefundsWorkspaceTab } from "../hooks/useRefundsWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { Plus, RefreshCw, X } from "lucide-react";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";
import { RefundsWorkspaceTabProps } from "../types/RefundsWorkspaceTab";
import { PaymentChoice } from "../types/RefundsWorkspaceTab";
import { paymentOption } from "../support/RefundsWorkspaceTab";

export function RefundsWorkspaceTab({ canWrite = true, section = "refunds", onNavigate }: RefundsWorkspaceTabProps) {
  const { currencyOptions, currencyFilter, setCurrencyFilter, dateFrom, setDateFrom, dateTo, setDateTo, returnFilter, setReturnFilter, resetFilters, selectedReturnId, setSelectedReturnId, selectedReturn, maxRefundAmount, revision, ConfirmDialogNode, loading, error, selectedStatus, setSelectedStatus, search, setSearch, setRevision, modalType, setModalType, activeRefund, setActiveRefund, refundBusy, paymentDetails, selectedPayment, setSelectedPayment, handleCreateRefund, handleUpdateStatus, filteredRefunds, isUncertain } = useRefundsWorkspaceTab({ canWrite, section });
  const [settlementId, setSettlementId] = useState("");
  useEffect(() => { setModalType(null); setActiveRefund(null); }, [section, setModalType, setActiveRefund]);
  return (
    <div id="scr-030-refunds-tab" className="refund-workspace space-y-5">
      {section === "refunds" && <>
      <NavbarSectionHeader view="refunds" className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Reembolsos y liquidación de devoluciones</h1>
          <p className="mt-1 text-xs text-slate-500">
            Desembolsos vinculados al pago original, disponibilidad de la devolución y movimientos de efectivo.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setRevision(r => r + 1)}
            disabled={loading}
            aria-label="Actualizar reembolsos"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Actualizar
          </button>
          {canWrite && (
            <button
              onClick={() => setModalType("create_refund")}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition"
              data-testid="request-refund-btn"
            >
              <Plus className="h-3.5 w-3.5" />
              Registrar reembolso
            </button>
          )}
        </div>
      </NavbarSectionHeader>

      <Panel1 setSelectedStatus={setSelectedStatus} selectedStatus={selectedStatus} search={search} setSearch={setSearch} currencyFilter={currencyFilter} setCurrencyFilter={setCurrencyFilter} currencies={currencyOptions} dateFrom={dateFrom} setDateFrom={setDateFrom} dateTo={dateTo} setDateTo={setDateTo} returnFilter={returnFilter} setReturnFilter={setReturnFilter} resetFilters={resetFilters} />

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800">
          {error}
        </div>
      )}

      <Panel2 filteredRefunds={filteredRefunds} isUncertain={isUncertain} canWrite={canWrite} setActiveRefund={setActiveRefund} setModalType={setModalType} loading={loading} onOpenSettlement={onNavigate ? id => { setSettlementId(id); onNavigate("settlements"); } : undefined} />

      </>}
      {section === "settlements" && <ReturnSettlementPanel standalone initialReturnId={settlementId} canWrite={canWrite} revision={revision} onChanged={() => setRevision(value => value + 1)} />}
      {section === "credit" && <CustomerCreditPanel standalone canWrite={canWrite} revision={revision} onChanged={() => setRevision(value => value + 1)} />}


      {modalType === "create_refund" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Registrar desembolso de reembolso</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleCreateRefund} className="mt-4 space-y-4">
              <p className="text-xs text-slate-500">
                Registre el dinero que está entregando al cliente e identifique la referencia del desembolso. Si es efectivo, se descontará de la caja elegida.
              </p>
              <RemoteEntitySelect<PaymentChoice> name="payment_id" required value={selectedPayment?.id || ""} onChange={(_, option) => setSelectedPayment(option?.data)} endpoint="/api/v1/payments" queryParams={{ refundable: "true" }} entityType="payment" mapOption={paymentOption} initialOption={selectedPayment ? paymentOption(selectedPayment) : undefined} label="Pago de origen" placeholder="Buscar por comprobante, cliente, documento o referencia" />
              {selectedPayment && <section className="rounded-xl bg-slate-50 p-3 text-xs">{paymentDetails ? <><p>Pagado: {selectedPayment.currency} {selectedPayment.amount}</p><p>Reembolsos anteriores: {selectedPayment.currency} {paymentDetails.refunded_amount}</p><strong>Saldo reembolsable: {selectedPayment.currency} {paymentDetails.refundable_amount}</strong>{paymentDetails.refunds.map(refund => <p key={refund.refund_id} className="mt-2 border-t pt-2">{new Date(refund.created_at).toLocaleDateString("es-PE", { timeZone: "America/Lima" })} · {refund.amount} · {refund.reason} · {refund.status}</p>)}</> : <p role="status">Consultando historial y saldo elegible…</p>}</section>}
              {paymentDetails && <div className="space-y-3 rounded-xl border p-3 text-xs">
                <label className="grid gap-1 font-semibold">Devolución vinculada<select value={selectedReturnId} required={paymentDetails.options.requires_return} onChange={event => setSelectedReturnId(event.target.value)} className="rounded-lg border p-2" disabled={refundBusy}><option value="">{paymentDetails.options.requires_return ? "Seleccione una devolución con valor disponible" : "Corrección de pago sin devolución comercial"}</option>{paymentDetails.options.returns.map(row => <option key={row.id} value={row.id}>{row.id.slice(0, 8)} · Disponible {row.currency} {row.available_amount}</option>)}</select></label>
                {selectedReturn && <><p>Retenciones: {selectedReturn.currency} {selectedReturn.retained_total} · Aplicado a deuda, saldo, cambios o reembolsos: {selectedReturn.applied_amount}</p>{selectedReturn.warnings.map((warning, index) => <p key={index} className="text-red-700">{warning}</p>)}</>}
                <p className="font-semibold">Máximo desembolsable: {paymentDetails.options.currency} {maxRefundAmount}</p>
                {paymentDetails.options.payment_method === "CASH" && <label className="grid gap-1 font-semibold">Caja que entrega el efectivo<select name="cash_session_id" required className="rounded-lg border p-2" disabled={refundBusy}><option value="">Seleccione una caja autorizada</option>{paymentDetails.options.cash_sessions.map(row => <option key={row.id} value={row.id}>{row.terminal_code} · Saldo {paymentDetails.options.currency} {row.balance}</option>)}</select></label>}
              </div>}
              <label className="block text-xs font-semibold text-slate-700">Referencia del desembolso o acta de entrega<input name="payout_reference" required minLength={3} maxLength={128} className="mt-1 w-full rounded-xl border p-2.5 text-xs" /></label>
              <label className="block text-xs font-semibold text-slate-700">
                Monto a reembolsar (en blanco = máximo disponible)
                <input name="amount" type="number" step="0.000001" min="0.000001" max={maxRefundAmount} placeholder={paymentDetails ? `Disponible: ${maxRefundAmount}` : "Selecciona un pago"} className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Motivo del Reembolso
                <textarea name="reason" rows={2} required placeholder="Discrepancia en cobro, producto defectuoso, acuerdo con cliente" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" disabled={refundBusy || !paymentDetails || Number(maxRefundAmount) <= 0} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition disabled:opacity-50">{refundBusy ? "Registrando…" : "Registrar reembolso"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalType === "update_status" && activeRefund && (
        <SeccionUpdate_status activeRefund={activeRefund} setModalType={setModalType} handleUpdateStatus={handleUpdateStatus} />
      )}
      {ConfirmDialogNode}
    </div>
  );
}
