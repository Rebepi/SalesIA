import { useState } from "react";
import { CalendarClock, X } from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatDate } from "../utils/formateadores";

interface VentasReprogramarModalProps {
  sale: SaleRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmReschedule: (saleId: string, newDueDate: string, reason: string) => Promise<void>;
  toast: { error: (title: string, desc?: string) => void };
}

export function VentasReprogramarModal({
  sale,
  isOpen,
  onClose,
  onConfirmReschedule,
  toast,
}: VentasReprogramarModalProps) {
  if (!isOpen || !sale) return null;

  const [newDueDate, setNewDueDate] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDueDate) {
      toast.error("Fecha requerida", "Indica la nueva fecha de vencimiento.");
      return;
    }
    if (!reason.trim() || reason.trim().length < 5) {
      toast.error("Motivo obligatorio", "Indica el motivo de la reprogramación comercial.");
      return;
    }

    setBusy(true);
    try {
      await onConfirmReschedule(sale.id || sale.sale_id, newDueDate, reason.trim());
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
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
              <CalendarClock className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Reprogramar vencimiento
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Comprobante: <strong>{sale.number}</strong>
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
          <div className="rounded-2xl bg-slate-50 p-3 text-xs dark:bg-slate-800/40">
            <span className="text-slate-500">Vencimiento actual: </span>
            <strong className="text-slate-900 dark:text-slate-100 font-mono">
              {formatDate(sale.due_date)}
            </strong>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Nueva fecha de vencimiento <span className="text-rose-600">*</span>
            </label>
            <input
              type="date"
              required
              value={newDueDate}
              onChange={(e) => setNewDueDate(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Motivo de la prórroga o reprogramación <span className="text-rose-600">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Ej: Acuerdo de pago ampliado solicitado por gerencia del cliente..."
              className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
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
              disabled={busy || !newDueDate || !reason.trim()}
              className="rounded-xl bg-teal-700 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-50"
            >
              {busy ? "Guardando..." : "Guardar nuevo vencimiento"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
