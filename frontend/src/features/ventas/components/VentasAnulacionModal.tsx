import { useState } from "react";
import { AlertOctagon, X, AlertTriangle } from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatMoney } from "../utils/formateadores";

interface VentasAnulacionModalProps {
  sale: SaleRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmAnulacion: (saleId: string, reason: string, paymentDisposition: "REFUND" | "STORE_CREDIT") => Promise<void>;
  toast: { error: (title: string, desc?: string) => void };
}

export function VentasAnulacionModal({
  sale,
  isOpen,
  onClose,
  onConfirmAnulacion,
  toast,
}: VentasAnulacionModalProps) {
  if (!isOpen || !sale) return null;

  const [reason, setReason] = useState("");
  const [paymentDisposition, setPaymentDisposition] = useState<"REFUND" | "STORE_CREDIT">("REFUND");
  const [busy, setBusy] = useState(false);

  const paidNum = Number(sale.paid_amount || 0);
  const isSunatAccepted = sale.sunat_status === "Aceptado";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim() || reason.trim().length < 5) {
      toast.error("Motivo obligatorio", "Ingresa un motivo claro de anulación (mínimo 5 caracteres).");
      return;
    }

    setBusy(true);
    try {
      await onConfirmAnulacion(sale.id || sale.sale_id, reason.trim(), paymentDisposition);
      onClose();
    } catch {
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
              <AlertOctagon className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Anular comprobante: {sale.number}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Esta acción es irreversible y queda registrada en auditoría.
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
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {isSunatAccepted && (
            <div className="flex gap-2.5 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-200">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
              <span>
                Este comprobante ya fue <strong>Aceptado por SUNAT</strong>. Al anularlo, el sistema generará
                la correspondiente Comunicación de Baja o Nota de Crédito electrónica de anulación total.
              </span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Motivo de anulación <span className="text-rose-600">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explica el motivo (error de emisión, devolución total del cliente, etc.)..."
              className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:border-rose-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>

          {paidNum > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-800/40">
              <span className="block text-xs font-bold text-slate-800 dark:text-slate-200">
                Tratamiento de cobros previos ({formatMoney(paidNum, sale.currency)})
              </span>
              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                Selecciona el destino del dinero cobrado previamente:
              </p>
              <div className="mt-2.5 space-y-2 text-xs">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="radio"
                    name="disposition"
                    value="REFUND"
                    checked={paymentDisposition === "REFUND"}
                    onChange={() => setPaymentDisposition("REFUND")}
                    className="text-rose-600 focus:ring-rose-500"
                  />
                  <span>Extornar cobro (reembolso directo al cliente)</span>
                </label>
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="radio"
                    name="disposition"
                    value="STORE_CREDIT"
                    checked={paymentDisposition === "STORE_CREDIT"}
                    onChange={() => setPaymentDisposition("STORE_CREDIT")}
                    className="text-rose-600 focus:ring-rose-500"
                  />
                  <span>Acreditar a saldo a favor del cliente en su ficha</span>
                </label>
              </div>
            </div>
          )}

          <div className="rounded-2xl bg-slate-100 p-3 text-[11px] text-slate-600 dark:bg-slate-800/50 dark:text-slate-400">
            ✓ Las unidades vendidas se reincorporarán automáticamente al inventario físico del almacén.
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
              disabled={busy || !reason.trim()}
              className="rounded-xl bg-rose-700 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-rose-800 disabled:opacity-50"
            >
              {busy ? "Anulando..." : "Confirmar anulación"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
