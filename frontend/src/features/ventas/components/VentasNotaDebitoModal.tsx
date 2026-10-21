import { useState } from "react";
import { X, Plus, Trash2, FilePlus, AlertCircle, CheckCircle2 } from "lucide-react";
import { SaleRecord } from "../types/ventas";
import { formatearMoneda } from "../utils/formateadores";

const DEBIT_NOTE_REASONS = [
  { code: "01", label: "Intereses por mora" },
  { code: "02", label: "Aumento en el valor de la operación" },
  { code: "03", label: "Penalidades / otros conceptos" },
  { code: "04", label: "Ajuste de flete y gastos de envío" },
];

interface VentasNotaDebitoModalProps {
  isOpen: boolean;
  sale: SaleRecord | null;
  onClose: () => void;
  onSuccess: (debitNote: unknown) => void;
  toast?: { success?: (msg: string) => void; error?: (msg: string) => void };
}

export function VentasNotaDebitoModal({ isOpen, sale, onClose, onSuccess, toast }: VentasNotaDebitoModalProps) {
  const [reasonCode, setReasonCode] = useState("01");
  const [description, setDescription] = useState("");
  const [lines, setLines] = useState<Array<{ id: string; concept: string; amount: number; taxRate: number }>>([
    { id: "1", concept: "Intereses por mora", amount: 0, taxRate: 0.18 }
  ]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen || !sale) return null;

  const currency = sale.currency || "USD";
  const originalNumber = sale.number || `${sale.series}-${sale.correlative}`;
  const suggestedSeries = sale.document_type === "INVOICE" ? "FD01" : "BD01";

  const totalAmount = lines.reduce((acc, l) => acc + (Number(l.amount) || 0), 0);
  const totalTax = lines.reduce((acc, l) => acc + (Number(l.amount) || 0) * (Number(l.taxRate) || 0), 0);
  const grandTotal = totalAmount + totalTax;

  function handleAddLine() {
    setLines((prev) => [
      ...prev,
      { id: String(Date.now()), concept: "", amount: 0, taxRate: 0.18 }
    ]);
  }

  function handleRemoveLine(id: string) {
    if (lines.length <= 1) return;
    setLines((prev) => prev.filter((l) => l.id !== id));
  }

  function handleUpdateLine(id: string, field: "concept" | "amount" | "taxRate", value: string | number) {
    setLines((prev) =>
      prev.map((l) => (l.id === id ? { ...l, [field]: value } : l))
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!sale) return;
    if (grandTotal <= 0) {
      setError("El importe de la nota de débito debe ser mayor a 0.");
      return;
    }
    const emptyConcept = lines.some((l) => !l.concept.trim());
    if (emptyConcept) {
      setError("Todos los conceptos deben contar con una descripción.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      const selectedReason = DEBIT_NOTE_REASONS.find((r) => r.code === reasonCode);
      const debitNotePayload = {
        sale_id: sale.id || sale.sale_id,
        reference_document: originalNumber,
        reference_type: sale.document_type,
        series: suggestedSeries,
        reason_code: reasonCode,
        reason_description: selectedReason?.label || "Nota de débito",
        additional_notes: description,
        currency,
        subtotal: totalAmount,
        tax_amount: totalTax,
        total: grandTotal,
        lines: lines.map((l) => ({
          concept: l.concept,
          amount: Number(l.amount),
          tax_amount: Number(l.amount) * Number(l.taxRate),
          tax_rate: Number(l.taxRate),
        })),
        created_at: new Date().toISOString(),
      };

      onSuccess(debitNotePayload);
      if (toast?.success) {
        toast.success(`Nota de débito emitida para ${originalNumber}. Saldo deudor incrementado.`);
      }
      onClose();
    } catch {
      setError("No se pudo emitir la nota de débito. Inténtalo de nuevo.");
      if (toast?.error) toast.error("Error al emitir nota de débito");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
        <header className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-6 py-4 dark:border-slate-800 dark:bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-600 text-white shadow-md">
              <FilePlus className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Crear Nota de Débito Electrónica
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Enlazada a {sale.document_type === "INVOICE" ? "Factura" : "Boleta"} <strong className="font-mono text-slate-700 dark:text-slate-300">{originalNumber}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6 space-y-4">
          <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-3.5 text-xs text-amber-900 dark:border-amber-800/60 dark:bg-amber-950/40 dark:text-amber-200">
            <p className="font-semibold">Efecto comercial y contable:</p>
            <p className="mt-0.5 text-[11px] text-amber-800 dark:text-amber-300">
              La emisión de esta nota de débito aumentará el valor de la operación y el saldo por cobrar del cliente en <strong className="font-mono">{formatearMoneda(grandTotal, currency)}</strong>.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Motivo del Catálogo SUNAT
              </label>
              <select
                value={reasonCode}
                onChange={(e) => setReasonCode(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-800 shadow-sm outline-none focus:border-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {DEBIT_NOTE_REASONS.map((r) => (
                  <option key={r.code} value={r.code}>
                    {r.code} - {r.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Serie asignada
              </label>
              <input
                type="text"
                readOnly
                value={`${suggestedSeries} (Automática)`}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-xs font-mono font-bold text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Sustento / Observaciones adicionales
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ej. Intereses moratorios calculados al 15/10/2026..."
              className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs shadow-sm outline-none focus:border-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Líneas de cargo
              </label>
              <button
                type="button"
                onClick={handleAddLine}
                className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800 dark:text-amber-400"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Agregar cargo</span>
              </button>
            </div>

            <div className="space-y-2">
              {lines.map((line, idx) => (
                <div key={line.id} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/50 p-2.5 dark:border-slate-800 dark:bg-slate-800/40">
                  <span className="text-[11px] font-mono font-bold text-slate-400 w-8 text-center">
                    N° {idx + 1}
                  </span>
                  <input
                    type="text"
                    value={line.concept}
                    onChange={(e) => handleUpdateLine(line.id, "concept", e.target.value)}
                    placeholder="Concepto del cargo..."
                    className="flex-1 rounded-lg border border-slate-300 bg-white p-1.5 text-xs shadow-sm outline-none focus:border-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                  <div className="w-28">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={line.amount || ""}
                      onChange={(e) => handleUpdateLine(line.id, "amount", parseFloat(e.target.value) || 0)}
                      placeholder="Monto"
                      className="w-full rounded-lg border border-slate-300 bg-white p-1.5 text-right font-mono text-xs shadow-sm outline-none focus:border-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    />
                  </div>
                  <select
                    value={line.taxRate}
                    onChange={(e) => handleUpdateLine(line.id, "taxRate", parseFloat(e.target.value))}
                    className="w-24 rounded-lg border border-slate-300 bg-white p-1.5 text-xs shadow-sm outline-none focus:border-amber-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <option value={0.18}>18% IGV</option>
                    <option value={0.10}>10% IGV</option>
                    <option value={0.00}>Exonerado</option>
                  </select>
                  {lines.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveLine(line.id)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-3.5 space-y-1.5 text-xs dark:border-slate-800 dark:bg-slate-950/60">
            <div className="flex justify-between text-slate-600 dark:text-slate-400">
              <span>Subtotal cargos:</span>
              <span className="font-mono">{formatearMoneda(totalAmount, currency)}</span>
            </div>
            <div className="flex justify-between text-slate-600 dark:text-slate-400">
              <span>IGV aplicable:</span>
              <span className="font-mono">{formatearMoneda(totalTax, currency)}</span>
            </div>
            <div className="flex justify-between border-t border-slate-200 pt-1.5 font-bold text-slate-900 dark:border-slate-800 dark:text-slate-100">
              <span>Total Nota de Débito:</span>
              <span className="font-mono text-amber-700 dark:text-amber-400">{formatearMoneda(grandTotal, currency)}</span>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-rose-50 p-3 text-xs text-rose-800 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={busy}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={busy || grandTotal <= 0}
              className="inline-flex items-center gap-1.5 rounded-xl bg-amber-600 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-amber-700 disabled:opacity-50"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{busy ? "Emitiendo..." : "Emitir Nota de Débito"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
