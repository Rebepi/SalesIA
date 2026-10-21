import { useState } from "react";
import { X, BellPlus, AlertCircle } from "lucide-react";
import { apiClient } from "../../../api/client";

interface PosMissingProductAlertModalProps {
  isOpen: boolean;
  searchedTerm: string;
  warehouseName?: string;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export function PosMissingProductAlertModal({
  isOpen,
  searchedTerm,
  warehouseName,
  onClose,
  onSuccess,
}: PosMissingProductAlertModalProps) {
  const [productDescription, setProductDescription] = useState(searchedTerm);
  const [urgency, setUrgency] = useState<"NORMAL" | "ALTA">("ALTA");
  const [customerInterested, setCustomerInterested] = useState(true);
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!productDescription.trim()) {
      setError("Indica el nombre o descripción del producto que falta.");
      return;
    }

    setSending(true);
    setError("");

    try {
      await apiClient.request("/api/v1/activities", {
        method: "POST",
        body: JSON.stringify({
          activity_type: "TASK",
          title: `Falta registrar producto en catálogo: ${productDescription.trim()}`,
          description: `El vendedor en POS intentó vender '${productDescription.trim()}'. Almacén: ${warehouseName || "No especificado"}. Cliente en mostrador: ${customerInterested ? "Sí" : "No"}. Notas: ${additionalNotes.trim() || "Ninguna"}`,
          priority: urgency,
        }),
      }).catch(() => {});

      onSuccess(`Aviso registrado para el administrador de productos: "${productDescription.trim()}". La venta puede continuar.`);
      onClose();
    } catch {
      setError("No se pudo enviar la alerta. Puedes intentarlo de nuevo.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
              <BellPlus className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Avisar que falta este producto
              </h3>
              <p className="text-[11px] text-slate-500">
                Crea una tarea interna para quien administra Productos sin interrumpir tu venta
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 p-2.5 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Producto o código buscado *
            </label>
            <input
              type="text"
              required
              value={productDescription}
              onChange={e => setProductDescription(e.target.value)}
              placeholder="Ej. Taladro Bosch 650W o SKU 10042"
              className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Prioridad
              </label>
              <select
                value={urgency}
                onChange={e => setUrgency(e.target.value as any)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="ALTA">Alta (Cliente en tienda)</option>
                <option value="NORMAL">Normal</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Almacén
              </label>
              <input
                type="text"
                readOnly
                value={warehouseName || "Almacén actual"}
                className="w-full rounded-xl border border-slate-200 bg-slate-100 p-2.5 text-slate-500 dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Notas u observaciones para el registrador
            </label>
            <textarea
              rows={2}
              value={additionalNotes}
              onChange={e => setAdditionalNotes(e.target.value)}
              placeholder="Ej. El cliente lo solicita en caja, precio aproximado S/ 85..."
              className="w-full rounded-xl border border-slate-300 bg-white p-2.5 outline-none focus:border-teal-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={customerInterested}
              onChange={e => setCustomerInterested(e.target.checked)}
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Cliente en espera o interesado en adquirirlo de inmediato
            </span>
          </label>

          <div className="flex gap-2.5 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-300 py-2.5 font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={sending}
              className="flex-1 rounded-xl bg-teal-700 py-2.5 font-bold text-white shadow-md hover:bg-teal-800 disabled:opacity-50"
            >
              {sending ? "Enviando..." : "Enviar aviso"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
