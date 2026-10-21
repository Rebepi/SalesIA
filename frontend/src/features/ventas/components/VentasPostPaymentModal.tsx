import { useState, useEffect } from "react";
import { CreditCard, X, Plus, Trash2, Printer, CheckCircle, AlertCircle } from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatMoney } from "../utils/formateadores";
import { apiClient } from "../../../api/client";

interface VentasPostPaymentModalProps {
  sale: SaleRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onPaymentSuccess: () => void;
  toast: { success: (msg: string) => void; error: (title: string, desc?: string) => void };
}

interface SplitPaymentRow {
  key: string;
  method: string;
  amount: number;
  cashTendered?: number;
  referenceCode?: string;
}

export function VentasPostPaymentModal({
  sale,
  isOpen,
  onClose,
  onPaymentSuccess,
  toast,
}: VentasPostPaymentModalProps) {
  if (!isOpen || !sale) return null;

  const totalNum = Number(sale.total_amount || 0);
  const paidNum = Number(sale.paid_amount || 0);
  const currentBalance = Math.max(0, totalNum - paidNum);

  const [payments, setPayments] = useState<SplitPaymentRow[]>([
    {
      key: "pay-1",
      method: "CASH",
      amount: currentBalance,
      cashTendered: currentBalance,
      referenceCode: "",
    },
  ]);

  const [overpaymentHandling, setOverpaymentHandling] = useState<"CHANGE" | "STORE_CREDIT">("CHANGE");
  const [busy, setBusy] = useState(false);
  const [selectedInstallment, setSelectedInstallment] = useState<string>("OLDEST");
  const [receiptSuccess, setReceiptSuccess] = useState<any | null>(null);

  useEffect(() => {
    setPayments([
      {
        key: "pay-1",
        method: "CASH",
        amount: currentBalance,
        cashTendered: currentBalance,
        referenceCode: "",
      },
    ]);
    setReceiptSuccess(null);
  }, [sale, currentBalance]);

  const totalPaying = payments.reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
  const cashTenderedTotal = payments
    .filter((p) => p.method === "CASH")
    .reduce((sum, p) => sum + (Number(p.cashTendered) || 0), 0);
  const cashAmountTotal = payments
    .filter((p) => p.method === "CASH")
    .reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
  const cashChange = Math.max(0, cashTenderedTotal - cashAmountTotal);
  const remainingAfterPayment = Math.max(0, currentBalance - totalPaying);
  const excessPayment = Math.max(0, totalPaying - currentBalance);

  const handleAddPayment = () => {
    const diff = Math.max(0, currentBalance - totalPaying);
    setPayments((prev) => [
      ...prev,
      {
        key: `pay-${Date.now()}`,
        method: "CARD",
        amount: diff,
        referenceCode: "",
      },
    ]);
  };

  const handleUpdatePayment = (key: string, patch: Partial<SplitPaymentRow>) => {
    setPayments((prev) => prev.map((p) => (p.key === key ? { ...p, ...patch } : p)));
  };

  const handleRemovePayment = (key: string) => {
    if (payments.length <= 1) return;
    setPayments((prev) => prev.filter((p) => p.key !== key));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (totalPaying <= 0) {
      toast.error("Importe inválido", "El monto a pagar debe ser mayor a 0.");
      return;
    }

    setBusy(true);
    try {

      for (const p of payments) {
        await apiClient.request("/api/v1/payments", {
          method: "POST",
          body: JSON.stringify({
            sale_id: sale.id || sale.sale_id,
            currency: sale.currency,
            amount: p.amount,
            payment_method: p.method,
            reference_code: p.referenceCode || undefined,
          }),
        });
      }

      setReceiptSuccess({
        date: new Date().toISOString(),
        sale_number: sale.number,
        customer_name: sale.customer_name,
        amount_paid: totalPaying,
        remaining_balance: remainingAfterPayment,
        currency: sale.currency,
        payments: [...payments],
        change: cashChange,
      });

      toast.success("Cobro registrado exitosamente.");
      onPaymentSuccess();
    } catch (err: any) {
      toast.error("Error al registrar cobro", err?.message || err?.detail || "Revise los datos de la operación.");
    } finally {
      setBusy(false);
    }
  };

  const handlePrintReceipt = () => {
    if (!receiptSuccess) return;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Recibo de Cobro - ${receiptSuccess.sale_number}</title>
        <style>
          body { font-family: monospace; width: 80mm; margin: 0 auto; padding: 10px; font-size: 11px; }
          .center { text-align: center; }
          .right { text-align: right; }
          .bold { font-weight: bold; }
          .divider { border-top: 1px dashed #000; margin: 8px 0; }
        </style>
      </head>
      <body>
        <div class="center bold">RECIBO DE COBRO</div>
        <div class="center">Documento: ${receiptSuccess.sale_number}</div>
        <div class="center">${new Date(receiptSuccess.date).toLocaleString("es-PE")}</div>
        <div class="divider"></div>
        <div>Cliente: ${receiptSuccess.customer_name}</div>
        <div class="divider"></div>
        ${receiptSuccess.payments
          .map(
            (p: any) => `
          <div>${p.method}: <span class="right">${formatMoney(p.amount, receiptSuccess.currency)}</span></div>
          ${p.referenceCode ? `<div>Ref: ${p.referenceCode}</div>` : ""}
        `
          )
          .join("")}
        <div class="divider"></div>
        <div class="bold right">TOTAL COBRADO: ${formatMoney(receiptSuccess.amount_paid, receiptSuccess.currency)}</div>
        ${receiptSuccess.change > 0 ? `<div class="right">Vuelto: ${formatMoney(receiptSuccess.change, receiptSuccess.currency)}</div>` : ""}
        <div class="right">Saldo pendiente: ${formatMoney(receiptSuccess.remaining_balance, receiptSuccess.currency)}</div>
        <div class="divider"></div>
        <div class="center">¡Gracias por su pago!</div>
        <script>window.onload = function() { window.print(); }</script>
      </body>
      </html>
    `);
    w.document.close();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
      <div className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <header className="flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-700 text-white">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Registrar Cobro: {sale.number}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Cliente: <strong>{sale.customer_name || "Cliente General"}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {receiptSuccess ? (
          <div className="p-6 text-center">
            <CheckCircle className="mx-auto h-12 w-12 text-emerald-600" />
            <h3 className="mt-3 text-base font-bold text-slate-900 dark:text-slate-100">
              ¡Cobro aplicado con éxito!
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Se registró el pago de {formatMoney(receiptSuccess.amount_paid, sale.currency)}.
            </p>
            <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-xs font-mono dark:bg-slate-800/60">
              <div className="flex justify-between">
                <span>Nuevo saldo pendiente:</span>
                <strong className="text-amber-700 dark:text-amber-400">
                  {formatMoney(receiptSuccess.remaining_balance, sale.currency)}
                </strong>
              </div>
              {receiptSuccess.change > 0 && (
                <div className="flex justify-between mt-1 text-emerald-700">
                  <span>Vuelto entregado:</span>
                  <strong>{formatMoney(receiptSuccess.change, sale.currency)}</strong>
                </div>
              )}
            </div>
            <div className="mt-6 flex justify-center gap-3">
              <button
                type="button"
                onClick={handlePrintReceipt}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200"
              >
                <Printer className="h-4 w-4" />
                <span>Imprimir Recibo</span>
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl bg-teal-700 px-5 py-2 text-xs font-bold text-white hover:bg-teal-800"
              >
                Cerrar
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            <div className="grid grid-cols-3 gap-2 rounded-2xl bg-slate-50 p-3 text-center dark:bg-slate-800/60">
              <div>
                <span className="block text-[10px] uppercase text-slate-400">Total Venta</span>
                <strong className="font-mono text-sm text-slate-900 dark:text-slate-100">
                  {formatMoney(totalNum, sale.currency)}
                </strong>
              </div>
              <div>
                <span className="block text-[10px] uppercase text-slate-400">Cobrado Previo</span>
                <strong className="font-mono text-sm text-emerald-700 dark:text-emerald-400">
                  {formatMoney(paidNum, sale.currency)}
                </strong>
              </div>
              <div>
                <span className="block text-[10px] uppercase text-slate-400">Saldo Pendiente</span>
                <strong className="font-mono text-sm text-amber-700 dark:text-amber-400">
                  {formatMoney(currentBalance, sale.currency)}
                </strong>
              </div>
            </div>

            {sale.is_credit && (
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Aplicación a cuotas
                </label>
                <select
                  aria-label="Aplicar cobro a cuotas"
                  value={selectedInstallment}
                  onChange={(e) => setSelectedInstallment(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                >
                  <option value="OLDEST">Pagar cuota más antigua primero (FIFO)</option>
                  <option value="ALL">Distribuir proporcionalmente en todas</option>
                  <option value="NEXT">Aplicar a la siguiente cuota por vencer</option>
                </select>
              </div>
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Medios de pago (Pago dividido)
                </span>
                <button
                  type="button"
                  onClick={handleAddPayment}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 hover:underline dark:text-teal-400"
                >
                  <Plus className="h-3 w-3" />
                  <span>Añadir medio</span>
                </button>
              </div>

              {payments.map((p, idx) => (
                <div
                  key={p.key}
                  className="grid grid-cols-[110px_1fr_auto] gap-2 rounded-xl border border-slate-200 bg-white p-2.5 dark:border-slate-800 dark:bg-slate-950"
                >
                  <select
                    aria-label={`Método de pago ${idx + 1}`}
                    value={p.method}
                    onChange={(e) => handleUpdatePayment(p.key, { method: e.target.value })}
                    className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                  >
                    <option value="CASH">Efectivo</option>
                    <option value="CARD">Tarjeta</option>
                    <option value="YAPE">Yape</option>
                    <option value="PLIN">Plin</option>
                    <option value="TRANSFER">Transferencia</option>
                    <option value="STORE_CREDIT">Saldo a favor</option>
                  </select>

                  <div className="flex gap-2">
                    <input
                      type="number"
                      aria-label={`Importe del pago ${idx + 1}`}
                      step="0.01"
                      min="0.01"
                      placeholder="Importe"
                      value={p.amount || ""}
                      onChange={(e) => handleUpdatePayment(p.key, { amount: Number(e.target.value) || 0 })}
                      className="w-1/2 rounded-lg border border-slate-300 px-2 py-1 text-xs font-mono outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                    />

                    {p.method === "CASH" ? (
                      <input
                        type="number"
                        aria-label="Efectivo recibido"
                        step="0.01"
                        min="0"
                        placeholder="Recibido"
                        value={p.cashTendered || ""}
                        onChange={(e) =>
                          handleUpdatePayment(p.key, { cashTendered: Number(e.target.value) || 0 })
                        }
                        className="w-1/2 rounded-lg border border-slate-300 px-2 py-1 text-xs font-mono outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                      />
                    ) : (
                      <input
                        type="text"
                        aria-label="Código o referencia"
                        placeholder="N° Operación / Ref"
                        value={p.referenceCode || ""}
                        onChange={(e) => handleUpdatePayment(p.key, { referenceCode: e.target.value })}
                        className="w-1/2 rounded-lg border border-slate-300 px-2 py-1 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                      />
                    )}
                  </div>

                  <button
                    type="button"
                    disabled={payments.length === 1}
                    onClick={() => handleRemovePayment(p.key)}
                    className="p-1 text-slate-400 hover:text-rose-600 disabled:opacity-30"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            {cashChange > 0 && (
              <div className="flex items-center justify-between rounded-xl bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
                <span>Vuelto a entregar:</span>
                <span className="font-mono text-sm">{formatMoney(cashChange, sale.currency)}</span>
              </div>
            )}

            {excessPayment > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-200">
                <div className="flex items-center gap-1.5 font-bold mb-1">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <span>El pago supera el saldo pendiente por {formatMoney(excessPayment, sale.currency)}</span>
                </div>
                <div className="flex gap-4 mt-2">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="overpay"
                      value="CHANGE"
                      checked={overpaymentHandling === "CHANGE"}
                      onChange={() => setOverpaymentHandling("CHANGE")}
                    />
                    <span>Entregar como vuelto</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="overpay"
                      value="STORE_CREDIT"
                      checked={overpaymentHandling === "STORE_CREDIT"}
                      onChange={() => setOverpaymentHandling("STORE_CREDIT")}
                    />
                    <span>Registrar como saldo a favor</span>
                  </label>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs dark:border-slate-800">
              <span className="text-slate-500">Saldo tras este cobro:</span>
              <strong className="font-mono text-slate-900 dark:text-slate-100">
                {formatMoney(remainingAfterPayment, sale.currency)}
              </strong>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={busy || totalPaying <= 0}
                className="rounded-xl bg-teal-700 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-50"
              >
                {busy ? "Procesando..." : "Confirmar cobro"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
