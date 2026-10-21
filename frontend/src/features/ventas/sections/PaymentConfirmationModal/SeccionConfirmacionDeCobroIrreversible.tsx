import type { usePaymentConfirmationModal } from "../../hooks/usePaymentConfirmationModal";
import { AlertCircle, Check, CreditCard, FileText, HelpCircle, LoaderCircle, Users, X, XCircle } from "lucide-react";
import { PaymentConfirmationModalProps } from "../../types/PaymentConfirmationModal";

export function SeccionConfirmacionDeCobroIrreversible({ loading, onClose, status, error, setStatus, setError, documentNumber, customerName, paymentMethod, currency, balance, amount, remainingBalance, refCode, setRefCode, handleConfirm }: { loading: ReturnType<typeof usePaymentConfirmationModal>["loading"]; status: ReturnType<typeof usePaymentConfirmationModal>["status"]; error: ReturnType<typeof usePaymentConfirmationModal>["error"]; setStatus: ReturnType<typeof usePaymentConfirmationModal>["setStatus"]; setError: ReturnType<typeof usePaymentConfirmationModal>["setError"]; refCode: ReturnType<typeof usePaymentConfirmationModal>["refCode"]; setRefCode: ReturnType<typeof usePaymentConfirmationModal>["setRefCode"] } & { onClose: PaymentConfirmationModalProps["onClose"]; documentNumber: PaymentConfirmationModalProps["documentNumber"]; customerName: PaymentConfirmationModalProps["customerName"]; paymentMethod: PaymentConfirmationModalProps["paymentMethod"]; currency: PaymentConfirmationModalProps["currency"]; balance: PaymentConfirmationModalProps["balance"]; amount: PaymentConfirmationModalProps["amount"] } & { remainingBalance: string | undefined; handleConfirm: () => Promise<void> }) {
  return (<div
    id="scr-018-payment-dialog"
    role="dialog"
    aria-modal="true"
    aria-labelledby="payment-confirmation-title"
    className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl transition-all"
  >
    <div className="flex items-center justify-between border-b border-slate-100 pb-4">
      <div className="flex items-center gap-2">
        <CreditCard className="h-6 w-6 text-teal-600" />
        <h2 id="payment-confirmation-title" className="text-lg font-semibold text-slate-900">
          Confirmación de cobro irreversible
        </h2>
      </div>
      {!loading && (
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          aria-label="Cerrar modal"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>

    <div className="mt-3 flex items-center justify-between">
      <span className="text-xs font-medium text-slate-500">Estado de la operación:</span>
      <span
        data-testid="payment-status-badge"
        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${status === "confirmed"
          ? "bg-teal-100 text-teal-800"
          : status === "rejected"
            ? "bg-rose-100 text-rose-800"
            : status === "unknown"
              ? "bg-amber-100 text-amber-800"
              : "bg-blue-100 text-blue-800"
          }`}
      >
        {status === "confirmed" && <Check className="h-3 w-3" />}
        {status === "rejected" && <XCircle className="h-3 w-3" />}
        {status === "unknown" && <HelpCircle className="h-3 w-3" />}
        {status === "pending" && <AlertCircle className="h-3 w-3" />}
        {status === "confirmed"
          ? "Confirmado"
          : status === "rejected"
            ? "Rechazado"
            : status === "unknown"
              ? "Estado desconocido"
              : "Pendiente"}
      </span>
    </div>

    {status === "confirmed" ? (
      <div className="py-8 text-center space-y-4" data-testid="payment-success-animated">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-teal-100 motion-safe:animate-bounce">
          <Check className="h-10 w-10 text-teal-600" />
        </div>
        <h3 className="text-xl font-bold text-slate-900">Cobro confirmado</h3>
        <p className="text-sm text-slate-600">
          La transacción fue procesada y registrada autoritativamente por el servidor.
        </p>
        <div className="pt-4">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl bg-teal-700 py-3 font-semibold text-white shadow-md hover:bg-teal-800 transition"
          >
            Cerrar
          </button>
        </div>
      </div>
    ) : status === "rejected" ? (
      <div className="py-8 text-center space-y-4" data-testid="payment-rejected-state">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-rose-100">
          <XCircle className="h-10 w-10 text-rose-600" />
        </div>
        <h3 className="text-xl font-bold text-slate-900">Cobro rechazado</h3>
        <p className="text-sm text-slate-600">
          {error || "El cobro fue rechazado o fondos insuficientes. No se afectaron saldos."}
        </p>
        <div className="pt-4 flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl border border-slate-300 py-2.5 font-medium text-slate-700 hover:bg-slate-50 transition"
          >
            Cerrar
          </button>
          <button
            type="button"
            onClick={() => { setStatus("pending"); setError(""); }}
            className="w-full rounded-xl bg-rose-600 py-2.5 font-semibold text-white shadow-md hover:bg-rose-700 transition"
          >
            Reintentar
          </button>
        </div>
      </div>
    ) : status === "unknown" ? (
      <div className="py-8 text-center space-y-4" data-testid="payment-unknown-state">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
          <HelpCircle className="h-10 w-10 text-amber-600" />
        </div>
        <h3 className="text-xl font-bold text-slate-900">Estado desconocido</h3>
        <p className="text-sm text-slate-600">
          El estado de la transacción no pudo verificarse de inmediato con el proveedor de pagos. Verifique en conciliación bancaria.
        </p>
        <div className="pt-4">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-xl bg-amber-600 py-3 font-semibold text-white shadow-md hover:bg-amber-700 transition"
          >
            Aceptar y revisar en tesorería
          </button>
        </div>
      </div>
    ) : (
      <div className="mt-4 space-y-4">
        <p className="text-xs text-slate-500">
          Verifique los datos de la operación antes de continuar. Esta acción afectará el saldo y el estado de la venta.
        </p>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-slate-400" />
              Documento:
            </span>
            <span className="text-sm font-semibold text-slate-900" data-testid="confirm-doc">
              {documentNumber || "—"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
              <Users className="h-4 w-4 text-slate-400" />
              Cliente:
            </span>
            <span className="text-sm font-semibold text-slate-900" data-testid="confirm-customer">
              {customerName || "—"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Método de pago:</span>
            <span className="text-sm font-medium text-slate-800" data-testid="confirm-method">
              {paymentMethod}
            </span>
          </div>

          <div className="flex items-center justify-between border-t border-slate-200 pt-3">
            <span className="text-xs font-medium text-slate-500">Moneda:</span>
            <span className="text-sm font-bold text-slate-900" data-testid="confirm-currency">
              {currency}
            </span>
          </div>

          {balance !== undefined && (
            <div className="flex items-center justify-between border-t border-slate-200 pt-3">
              <span className="text-xs font-medium text-slate-500">Saldo pendiente:</span>
              <span className="text-sm font-bold text-slate-800" data-testid="confirm-balance">
                {currency} {typeof balance === "number" ? balance.toFixed(2) : balance}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between border-t border-slate-200 pt-3">
            <span className="text-sm font-bold text-slate-700">Monto a cobrar:</span>
            <span className="text-lg font-black text-teal-700 tabular-nums" data-testid="confirm-amount">
              {currency} {typeof amount === "number" ? amount.toFixed(2) : amount}
            </span>
          </div>

          {remainingBalance !== undefined && (
            <div className="flex items-center justify-between border-t border-slate-200 pt-2 text-xs">
              <span className="text-slate-500">Saldo remanente proyectado:</span>
              <span className="font-semibold text-slate-700">{currency} {remainingBalance}</span>
            </div>
          )}
        </div>

        <label className="block text-xs font-semibold text-slate-700">
          Referencia / Voucher bancario
          <input
            data-testid="confirm-reference-input"
            type="text"
            value={refCode}
            onChange={e => setRefCode(e.target.value)}
            placeholder="Número de operación o constancia"
            className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
          />
        </label>

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 border border-red-200" role="alert">
            {error}
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3 pt-2">
          <button
            type="button"
            disabled={loading}
            onClick={onClose}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={loading}
            aria-busy={loading}
            onClick={handleConfirm}
            className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-teal-800 transition disabled:cursor-not-allowed disabled:opacity-50"
            data-testid="confirm-payment-btn"
          >
            {loading && <LoaderCircle className="h-4 w-4 animate-spin" />}
            {loading ? "Procesando cobro…" : "Confirmar cobro"}
          </button>
        </div>
      </div>
    )}
  </div>);
}
